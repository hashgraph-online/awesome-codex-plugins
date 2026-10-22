#!/usr/bin/env python3
"""Build a container image with an in-cluster Kaniko Job and push it to GHCR.

For sandboxes without a Docker daemon (Brain managed deploys). The build
context is tarred into the DevBox-local VersityGW S3 store; a Kaniko Job in
the current namespace pulls it from there, builds for linux/amd64, pushes the
tagged image to ghcr.io, and reports the immutable digest.

Standard library only. Requires: kubectl, tar, GITHUB_TOKEN (write:packages).

Inputs, in precedence order:
  1. CLI flags
  2. .sealos/build-runtime.json (written by the Brain control plane):
     s3Endpoint (Job-reachable), bucket, accessKeyId, secretKeyRef
     {name,key}, buildDeadlineAt, buildDeadlineSeconds, devboxName
  3. DevBox runtime env: KANIKO_CONTEXT_POSIX_DIR, KANIKO_CONTEXT_S3_BUCKET,
     KANIKO_CONTEXT_S3_PREFIX, KANIKO_JOB_S3_ENDPOINT, S3_ENDPOINT,
     AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY / SEALOS_DEVBOX_JWT_SECRET /
     DEVBOX_JWT_SECRET, AWS_REGION, VERSITYGW_ROOT, SEALOS_DEVBOX_NAME
  4. Documented defaults (labring-actions/devbox-runtime sandbox/v1)

Usage:
  kaniko-build.py --image ghcr.io/<owner>/<repo>:<tag> [--context DIR]
                  [--dockerfile PATH] [--namespace NS] [--build-arg K=V ...]
                  [--runtime-file PATH] [--render-only] [--timeout SECONDS]

Output: one JSON object on stdout. Progress and diagnostics go to stderr.
Success: {"success": true, "image": "<tag ref>", "digest": "sha256:...",
          "image_ref": "<repo>@sha256:...", "pull": "anonymous|private|indeterminate", ...}
"""

import argparse
import base64
import calendar
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_KANIKO_IMAGE = "gcr.io/kaniko-project/executor:v1.24.0"
DEFAULT_PLATFORM = "linux/amd64"
MAX_BUILD_SECONDS = 1800
WAIT_SLACK_SECONDS = 60
DEFAULT_BUCKET = "kaniko-contexts"
DEFAULT_PREFIX = "contexts"
DEFAULT_S3_PORT = "1319"
TAR_EXCLUDES = [".git", ".sealos", ".versitygw-s3", ".versitygw-iam", ".versitygw-versioning"]
DNS_LABEL_RE = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
DIGEST_RE = re.compile(r"sha256:[a-f0-9]{64}")
IMAGE_RE = re.compile(
    r"^ghcr\.io/[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._/-]*:"
    r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$"
)
SAMPLE_MANIFEST = """apiVersion: batch/v1
kind: Job
metadata:
  name: kaniko-example
  namespace: ns-example
spec:
  activeDeadlineSeconds: 1800
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: kaniko
        image: gcr.io/kaniko-project/executor:v1.24.0
        args:
        - '--dockerfile=Dockerfile'
        - '--context=s3://kaniko-contexts/contexts/devbox/sample/context.tar.gz'
        - '--destination=ghcr.io/example/app:preview'
        - '--custom-platform=linux/amd64'
        - '--digest-file=/dev/termination-log'
        env:
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: devbox-secret
              key: SEALOS_DEVBOX_JWT_SECRET
"""


def log(message):
    print(message, file=sys.stderr, flush=True)


def fail(message, **extra):
    print(json.dumps({"success": False, "error": message, **extra}))
    sys.exit(1)


def run(cmd, input_text=None, timeout=120):
    """Run a command; return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd, input=input_text, capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", f"{cmd[0]}: command not found"
    except subprocess.TimeoutExpired:
        return 124, "", f"{' '.join(cmd[:4])}...: timed out after {timeout}s"


def kubectl(args, input_text=None, timeout=120):
    return run(["kubectl", *args], input_text=input_text, timeout=timeout)


def http_json(url, headers=None, method="GET", timeout=30):
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = body[:300]
        return e.code, dict(e.headers), parsed
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, {}, str(e)


# ── contract resolution ─────────────────────────────────


def load_runtime_contract(path):
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except ValueError:
        log("warning: build runtime contract is not valid JSON; ignoring")
        return {}


def resolve_namespace(args_namespace):
    for candidate, source in [
        (args_namespace, "flag"),
        (os.environ.get("SEALAI_NAMESPACE"), "SEALAI_NAMESPACE"),
        (os.environ.get("NAMESPACE"), "NAMESPACE"),
    ]:
        if candidate:
            return candidate.strip(), source
    code, out, _ = kubectl(
        ["config", "view", "--minify", "-o", "jsonpath={.contexts[0].context.namespace}"]
    )
    if code == 0 and out.strip():
        return out.strip(), "kube-context"
    sa_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
    if os.path.exists(sa_path):
        with open(sa_path) as f:
            value = f.read().strip()
        if value:
            return value, "serviceaccount"
    fail("cannot resolve namespace: pass --namespace or set NAMESPACE")


def resolve_service_account(namespace):
    pod = os.environ.get("HOSTNAME", "")
    if pod:
        code, out, _ = kubectl(
            ["get", "pod", pod, "-n", namespace, "-o", "jsonpath={.spec.serviceAccountName}"]
        )
        if code == 0 and out.strip():
            return out.strip()
    return None


def resolve_pod_ip(namespace):
    if os.environ.get("POD_IP"):
        return os.environ["POD_IP"]
    pod = os.environ.get("HOSTNAME", "")
    if pod:
        code, out, _ = kubectl(
            ["get", "pod", pod, "-n", namespace, "-o", "jsonpath={.status.podIP}"]
        )
        if code == 0 and out.strip():
            return out.strip()
    return None


def is_loopback(url):
    host = urllib.parse.urlparse(url).hostname
    return host in ("127.0.0.1", "localhost", "::1")


def resolve_job_s3_endpoint(runtime, namespace):
    """S3 endpoint the Kaniko Job Pod can reach (never loopback)."""
    for candidate in (runtime.get("s3Endpoint"), os.environ.get("KANIKO_JOB_S3_ENDPOINT")):
        if candidate and not is_loopback(candidate):
            return candidate.rstrip("/")
    local = (
        os.environ.get("S3_ENDPOINT")
        or os.environ.get("AWS_ENDPOINT_URL_S3")
        or os.environ.get("AWS_ENDPOINT_URL")
        or f"http://127.0.0.1:{DEFAULT_S3_PORT}"
    )
    if not is_loopback(local):
        return local.rstrip("/")
    pod_ip = resolve_pod_ip(namespace)
    if not pod_ip:
        fail(
            "cannot derive a Job-reachable S3 endpoint: runtime contract has no "
            "s3Endpoint, KANIKO_JOB_S3_ENDPOINT is unset, and the Pod IP is unknown"
        )
    parsed = urllib.parse.urlparse(local)
    return f"{parsed.scheme}://{pod_ip}:{parsed.port or DEFAULT_S3_PORT}"


def resolve_context_store(runtime):
    """Where to write the context tarball, and the bucket/prefix for the URI.

    The POSIX dir and the S3 URI must name the same bucket. When the runtime
    env provides KANIKO_CONTEXT_POSIX_DIR, its bucket/prefix env vars are set
    by the same process, so env wins as a consistent set; the Brain contract
    bucket is used only to build a POSIX path when env is absent.
    """
    env_dir = os.environ.get("KANIKO_CONTEXT_POSIX_DIR")
    if env_dir:
        bucket = os.environ.get("KANIKO_CONTEXT_S3_BUCKET", DEFAULT_BUCKET)
        prefix = os.environ.get("KANIKO_CONTEXT_S3_PREFIX", DEFAULT_PREFIX)
        return env_dir, bucket, prefix
    bucket = (
        os.environ.get("KANIKO_CONTEXT_S3_BUCKET")
        or runtime.get("bucket")
        or DEFAULT_BUCKET
    )
    prefix = os.environ.get("KANIKO_CONTEXT_S3_PREFIX", DEFAULT_PREFIX)
    root = os.environ.get("VERSITYGW_ROOT") or os.path.join(
        os.environ.get("CODEX_GATEWAY_CWD", "/home/devbox/workspace"), ".versitygw-s3"
    )
    return os.path.join(root, bucket, prefix), bucket, prefix


def resolve_deadline_seconds(runtime, flag_timeout):
    if flag_timeout:
        if flag_timeout > MAX_BUILD_SECONDS:
            fail(f"--timeout must be <= {MAX_BUILD_SECONDS}")
        return flag_timeout
    seconds = runtime.get("buildDeadlineSeconds")
    seconds = int(seconds) if isinstance(seconds, (int, float)) and seconds > 0 else MAX_BUILD_SECONDS
    deadline_at = runtime.get("buildDeadlineAt")
    if isinstance(deadline_at, str):
        try:
            deadline_epoch = calendar.timegm(
                time.strptime(deadline_at[:19], "%Y-%m-%dT%H:%M:%S")
            )
            remaining = int(deadline_epoch - time.time())
            if remaining <= 0:
                fail("build deadline from build-runtime.json has already elapsed")
            seconds = min(seconds, remaining)
        except ValueError:
            log("warning: unparsable buildDeadlineAt; using the configured limit")
    return min(seconds, MAX_BUILD_SECONDS)


# ── GHCR ─────────────────────────────────────────────────


def check_ghcr_token(target_image):
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        fail("GITHUB_TOKEN is required to push to ghcr.io")
    status, headers, user = http_json(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "use-sealos-kaniko",
            "Accept": "application/vnd.github+json",
        },
    )
    if status != 200 or not isinstance(user, dict) or not user.get("login"):
        fail("GITHUB_TOKEN validation failed")
    login = user["login"]
    scopes = [s.strip() for s in (headers.get("x-oauth-scopes") or "").split(",") if s.strip()]
    if scopes and "write:packages" not in scopes:
        fail("GITHUB_TOKEN lacks the write:packages scope")
    owner = target_image.split("/")[1]
    if owner != owner.lower():
        fail("GHCR owner must be lowercase")
    if owner != login.lower():
        fail("target image owner does not match the token login",
             hint="use ghcr.io/<token-login>/<repo>:<tag>")
    return login, token


def classify_pull(image_repo, digest):
    """Can the pushed image be pulled anonymously? GHCR issues anonymous
    tokens for public packages only."""
    path = image_repo.split("/", 1)[1]
    status, _, tok = http_json(
        f"https://ghcr.io/token?scope=repository:{urllib.parse.quote(path)}:pull&service=ghcr.io"
    )
    if status != 200 or not isinstance(tok, dict) or not tok.get("token"):
        return "private" if status in (401, 403) else "indeterminate"
    req = urllib.request.Request(
        f"https://ghcr.io/v2/{path}/manifests/{digest}",
        headers={
            "Authorization": f"Bearer {tok['token']}",
            "Accept": "application/vnd.oci.image.index.v1+json, "
            "application/vnd.docker.distribution.manifest.v2+json, "
            "application/vnd.oci.image.manifest.v1+json",
        },
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return "anonymous" if resp.status == 200 else "indeterminate"
    except urllib.error.HTTPError as e:
        return "private" if e.code in (401, 403, 404) else "indeterminate"
    except (urllib.error.URLError, TimeoutError):
        return "indeterminate"


# ── build steps ──────────────────────────────────────────


def validate_image(image):
    if not IMAGE_RE.fullmatch(image):
        fail("target image must be a ghcr.io/<owner>/<repo>:<tag> reference")
    repo, tag = image.rsplit(":", 1)
    return repo, tag


def sanitize_dns_label(value, max_length):
    value = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-") or "build"
    return value[:max_length].rstrip("-")


def prepare_context_tar(context_dir, dockerfile, posix_dir, prefix, devbox, build_id):
    context_dir = os.path.realpath(context_dir)
    if not os.path.isdir(context_dir):
        fail("context directory not found")
    dockerfile_abs = os.path.realpath(os.path.join(context_dir, dockerfile))
    if not dockerfile_abs.startswith(context_dir + os.sep):
        fail("dockerfile must live inside the context")
    if not os.path.isfile(dockerfile_abs):
        fail("dockerfile not found")
    dockerfile_rel = os.path.relpath(dockerfile_abs, context_dir).replace(os.sep, "/")

    object_dir = os.path.join(posix_dir, devbox, build_id)
    os.makedirs(object_dir, exist_ok=True)
    tar_path = os.path.join(object_dir, "context.tar.gz")
    exclude_args = []
    for name in TAR_EXCLUDES:
        exclude_args += ["--exclude", f"./{name}"]
    code, _, _ = run(
        ["tar", *exclude_args, "-C", context_dir, "-czf", tar_path, "."], timeout=600
    )
    if code != 0:
        fail("tar failed")
    size = os.path.getsize(tar_path)
    log("build context archived")
    object_key = f"{prefix}/{devbox}/{build_id}/context.tar.gz"
    return object_key, dockerfile_rel, size


def create_registry_secret(namespace, login, token, secret_name):
    auth = base64.b64encode(f"{login}:{token}".encode()).decode()
    docker_config = json.dumps({"auths": {"ghcr.io": {"auth": auth}}})
    manifest = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": secret_name, "namespace": namespace},
        "type": "Opaque",
        "stringData": {"config.json": docker_config},
    }
    code, _, _ = kubectl(["create", "-f", "-"], input_text=json.dumps(manifest))
    if code != 0:
        fail("failed to create registry secret")


def s3_credential_env(runtime, namespace):
    """Kaniko Job env entries for the S3 credentials.

    Prefer the existing DevBox secret named by the Brain runtime contract;
    fall back to creating a build-only secret from the local env.
    Returns (env_yaml_lines, secret_to_cleanup_or_None).
    """
    access_key = runtime.get("accessKeyId") or os.environ.get("AWS_ACCESS_KEY_ID", "admin")
    ref = runtime.get("secretKeyRef")
    if isinstance(ref, dict) and ref.get("name") and ref.get("key"):
        code, _, _ = kubectl(["get", "secret", ref["name"], "-n", namespace])
        if code == 0:
            lines = [
                yaml_env_literal("AWS_ACCESS_KEY_ID", access_key),
                yaml_env_secret("AWS_SECRET_ACCESS_KEY", ref["name"], ref["key"]),
            ]
            return lines, None
        log("warning: runtime S3 secret reference is unavailable; falling back to env")
    secret_value = (
        os.environ.get("AWS_SECRET_ACCESS_KEY")
        or os.environ.get("SEALOS_DEVBOX_JWT_SECRET")
        or os.environ.get("DEVBOX_JWT_SECRET")
    )
    if not secret_value:
        fail(
            "no S3 credentials: build-runtime.json secretKeyRef is unusable and "
            "AWS_SECRET_ACCESS_KEY / SEALOS_DEVBOX_JWT_SECRET / DEVBOX_JWT_SECRET are unset"
        )
    secret_name = f"use-sealos-kaniko-s3-{uuid.uuid4().hex[:8]}"
    manifest = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": secret_name, "namespace": namespace},
        "type": "Opaque",
        "stringData": {
            "AWS_ACCESS_KEY_ID": access_key,
            "AWS_SECRET_ACCESS_KEY": secret_value,
        },
    }
    code, _, _ = kubectl(["create", "-f", "-"], input_text=json.dumps(manifest))
    if code != 0:
        fail("failed to create S3 secret")
    lines = [
        yaml_env_secret("AWS_ACCESS_KEY_ID", secret_name, "AWS_ACCESS_KEY_ID"),
        yaml_env_secret("AWS_SECRET_ACCESS_KEY", secret_name, "AWS_SECRET_ACCESS_KEY"),
    ]
    return lines, secret_name


def yaml_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def yaml_env_literal(name, value):
    return f"        - name: {name}\n          value: {yaml_quote(value)}"


def yaml_env_secret(name, secret, key):
    return (
        f"        - name: {name}\n"
        f"          valueFrom:\n"
        f"            secretKeyRef:\n"
        f"              name: {secret}\n"
        f"              key: {key}"
    )


def validate_build_arg(pair):
    key, sep, _ = pair.partition("=")
    if not sep or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        fail("--build-arg must be KEY=value with an env-style key")
    if "\n" in pair or "\r" in pair:
        fail("--build-arg value must be single-line")
    return pair


def render_job(
    *, job_name, namespace, service_account, kaniko_image, platform, context_uri,
    dockerfile, target_image, s3_endpoint, aws_region, registry_secret,
    s3_env_lines, build_args, deadline_seconds,
):
    for name, value in [("namespace", namespace), ("job name", job_name)]:
        if not DNS_LABEL_RE.match(value) or len(value) > 63:
            fail(f"{name} must be a DNS label up to 63 chars")
    build_arg_lines = "".join(
        f"        - {yaml_quote(f'--build-arg={pair}')}\n" for pair in build_args
    )
    sa_line = f"      serviceAccountName: {service_account}\n" if service_account else ""
    return f"""apiVersion: batch/v1
kind: Job
metadata:
  name: {job_name}
  namespace: {namespace}
  labels:
    app.kubernetes.io/name: use-sealos-kaniko
    app.kubernetes.io/managed-by: use-sealos
  annotations:
    use-sealos.dev/context-uri: {yaml_quote(context_uri)}
    use-sealos.dev/target-image: {yaml_quote(target_image)}
spec:
  activeDeadlineSeconds: {deadline_seconds}
  backoffLimit: 0
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app.kubernetes.io/name: use-sealos-kaniko
    spec:
      restartPolicy: Never
{sa_line}      containers:
      - name: kaniko
        image: {kaniko_image}
        resources:
          requests:
            cpu: "500m"
            memory: "2Gi"
            ephemeral-storage: "2Gi"
          limits:
            cpu: "2"
            memory: "8Gi"
            ephemeral-storage: "10Gi"
        args:
        - {yaml_quote(f'--dockerfile={dockerfile}')}
        - {yaml_quote(f'--context={context_uri}')}
        - {yaml_quote(f'--destination={target_image}')}
        - {yaml_quote(f'--custom-platform={platform}')}
        - '--digest-file=/dev/termination-log'
        - '--cleanup'
        - '--verbosity=info'
{build_arg_lines}        env:
        - name: S3_ENDPOINT
          value: {yaml_quote(s3_endpoint)}
        - name: S3_FORCE_PATH_STYLE
          value: "true"
        - name: AWS_EC2_METADATA_DISABLED
          value: "true"
        - name: AWS_REGION
          value: {yaml_quote(aws_region)}
{chr(10).join(s3_env_lines)}
        volumeMounts:
        - name: docker-config
          mountPath: /kaniko/.docker/config.json
          subPath: config.json
          readOnly: true
      volumes:
      - name: docker-config
        secret:
          secretName: {registry_secret}
          items:
          - key: config.json
            path: config.json
"""


def read_digest(namespace, job_name):
    code, out, _ = kubectl(
        [
            "get", "pods", "-n", namespace, "-l", f"job-name={job_name}",
            "-o",
            'jsonpath={.items[*].status.containerStatuses[?(@.name=="kaniko")].state.terminated.message}',
        ]
    )
    if code != 0:
        log("warning: could not read termination message")
        return None
    match = DIGEST_RE.search(out or "")
    return match.group(0) if match else None


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--image", required=True, help="target ghcr.io/<owner>/<repo>:<tag>")
    parser.add_argument("--context", default=".", help="build context directory (default: .)")
    parser.add_argument("--dockerfile", default="Dockerfile", help="path relative to the context")
    parser.add_argument("--namespace", help="target namespace (default: resolved)")
    parser.add_argument("--build-arg", action="append", default=[], metavar="K=V",
                        help="kaniko --build-arg; values appear in the Job spec, never pass secrets")
    parser.add_argument("--runtime-file", help="path to .sealos/build-runtime.json")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM)
    parser.add_argument("--kaniko-image", default=DEFAULT_KANIKO_IMAGE)
    parser.add_argument("--timeout", type=int, help=f"build seconds cap (max {MAX_BUILD_SECONDS})")
    parser.add_argument("--render-only", action="store_true",
                        help="print a redacted sample Job manifest; no kubectl or tar upload")
    args = parser.parse_args()

    image_repo, _ = validate_image(args.image)
    for pair in args.build_arg:
        validate_build_arg(pair)

    workspace = os.environ.get("SEALAI_DEPLOY_WORKSPACE") or os.getcwd()
    runtime_path = args.runtime_file or os.path.join(workspace, ".sealos", "build-runtime.json")
    runtime = load_runtime_contract(runtime_path)
    deadline_seconds = resolve_deadline_seconds(runtime, args.timeout)
    aws_region = runtime.get("region") or os.environ.get("AWS_REGION", "sealos-internal")
    devbox = (
        runtime.get("devboxName")
        or os.environ.get("SEALOS_DEVBOX_NAME")
        or os.environ.get("DEVBOX_NAME")
        or os.environ.get("HOSTNAME")
        or "devbox"
    )
    build_id = f"{sanitize_dns_label(image_repo.rsplit('/', 1)[-1], 30)}-{uuid.uuid4().hex[:8]}"
    job_name = f"kaniko-{build_id}"[:63].rstrip("-")

    if args.render_only:
        sys.stdout.write(SAMPLE_MANIFEST)
        return

    if shutil.which("kubectl") is None:
        fail("kubectl is required")
    if shutil.which("tar") is None:
        fail("tar is required")

    namespace, _ = resolve_namespace(args.namespace)
    log("namespace selected")
    service_account = resolve_service_account(namespace)
    if service_account:
        log("service account resolved")

    login, token = check_ghcr_token(args.image)
    log("ghcr authentication validated")

    s3_endpoint = resolve_job_s3_endpoint(runtime, namespace)
    posix_dir, bucket, prefix = resolve_context_store(runtime)
    log("S3 context store resolved")

    object_key, dockerfile_rel, tar_size = prepare_context_tar(
        args.context, args.dockerfile, posix_dir, prefix, devbox, build_id
    )
    context_uri = f"s3://{bucket}/{object_key}"

    registry_secret = f"use-sealos-ghcr-auth-{uuid.uuid4().hex[:8]}"
    create_registry_secret(namespace, login, token, registry_secret)
    s3_env_lines, _ = s3_credential_env(runtime, namespace)

    manifest = render_job(
        job_name=job_name,
        namespace=namespace,
        service_account=service_account,
        kaniko_image=args.kaniko_image,
        platform=args.platform,
        context_uri=context_uri,
        dockerfile=dockerfile_rel,
        target_image=args.image,
        s3_endpoint=s3_endpoint,
        aws_region=aws_region,
        registry_secret=registry_secret,
        s3_env_lines=s3_env_lines,
        build_args=args.build_arg,
        deadline_seconds=deadline_seconds,
    )
    code, _, _ = kubectl(["apply", "-f", "-"], input_text=manifest)
    if code != 0:
        fail("kubectl apply failed")
    log("kaniko job created; waiting for completion")

    wait_timeout = deadline_seconds + WAIT_SLACK_SECONDS
    code, _, _ = kubectl(
        [
            "wait", "--for=condition=Complete", f"job/{job_name}",
            "-n", namespace, f"--timeout={wait_timeout}s",
        ],
        timeout=wait_timeout + 30,
    )
    if code != 0:
        fail(
            "kaniko job did not complete",
            job=job_name,
            namespace=namespace,
            hint="inspect the named Job and Pods in the selected namespace",
        )

    digest = read_digest(namespace, job_name)
    pull = classify_pull(image_repo, digest) if digest else "indeterminate"
    result = {
        "success": True,
        "image": args.image,
        "digest": digest,
        "image_ref": f"{image_repo}@{digest}" if digest else args.image,
        "pull": pull,
        "job": job_name,
        "namespace": namespace,
        "context_bytes": tar_size,
    }
    if not digest:
        result["warning"] = (
            "image pushed but digest could not be read from the pod termination "
            "message; deploy with the tag reference"
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
