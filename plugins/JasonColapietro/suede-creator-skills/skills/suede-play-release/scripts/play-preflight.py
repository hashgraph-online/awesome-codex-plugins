#!/usr/bin/env python3
"""Prove Google Play publishing works, or say exactly what is missing.

Opens a real Play edit and deletes it again, so it proves the whole path
(credential, token exchange, and the Play Console grant) while changing nothing.

    python3 play-preflight.py <package.name> [--service SERVICE] [--account ACCOUNT]

Defaults suit a single-app setup; pass --service/--account when you keep more
than one publishing credential in the Keychain.

Exit codes are the point:
    0  publishing is wired
    2  credential is valid but Play has not granted it access (the normal state
       of a new service account; the fix is a Play Console UI action)
    1  anything else, with the reason

The service-account JSON is read from the macOS login Keychain, base64-encoded.
`security` hex-encodes any multi-line secret on read, so raw JSON comes back in
one of two shapes; base64 gives one shape and one decode path.
"""
import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import jwt
except ImportError:
    sys.exit("FAIL  PyJWT is not installed. `pip3 install pyjwt cryptography`")

SCOPE = "https://www.googleapis.com/auth/androidpublisher"
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"


def load_credential(service, account):
    result = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(
            f"FAIL  no Keychain item for service {service!r}, account {account!r}.\n"
            f"      Store it with: security add-generic-password -U -s {service} "
            f"-a {account} -w\n"
            f"      Paste the base64 of the service-account JSON, not the raw JSON."
        )
    try:
        return json.loads(base64.b64decode(result.stdout.strip()))
    except Exception:
        sys.exit(
            f"FAIL  {service} did not decode to JSON. It must hold the "
            f"base64 of the service-account file."
        )


def access_token(sa):
    now = int(time.time())
    assertion = jwt.encode(
        {"iss": sa["client_email"], "scope": SCOPE, "aud": sa["token_uri"],
         "iat": now, "exp": now + 3600},
        sa["private_key"], algorithm="RS256",
    )
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }).encode()
    request = urllib.request.Request(
        sa["token_uri"], data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.load(urllib.request.urlopen(request, timeout=30))["access_token"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", help="Play application id, e.g. com.example.app")
    parser.add_argument("--service", default="GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
    parser.add_argument("--account", default="play-publisher")
    args = parser.parse_args()

    sa = load_credential(args.service, args.account)
    print(f"OK    credential found: {sa['client_email']}")

    token = access_token(sa)
    print("OK    exchanged it for an access token (the key itself is valid)")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        edit = json.load(urllib.request.urlopen(urllib.request.Request(
            f"{API}/{args.package}/edits", data=b"{}", method="POST", headers=headers,
        ), timeout=30))
    except urllib.error.HTTPError as error:
        detail = error.read().decode()
        if error.code in (401, 403):
            print(f"PEND  the Play Console has not granted this account access "
                  f"yet (HTTP {error.code}).")
            print(f"      Invite {sa['client_email']} in Play Console ->")
            print( "      Users and permissions, with release permissions on this app.")
            print( "      That is a Console UI action; it cannot be done from the API.")
            print( "      Then re-run this script.")
            return 2
        if error.code == 404:
            sys.exit(f"FAIL  Play does not know the package {args.package!r} for "
                     f"this account. Check the application id.")
        sys.exit(f"FAIL  HTTP {error.code}: {detail[:400]}")

    print(f"OK    opened a Play edit for {args.package} "
          f"(id {edit['id'][:12]}...) - publishing is wired")
    urllib.request.urlopen(urllib.request.Request(
        f"{API}/{args.package}/edits/{edit['id']}", method="DELETE", headers=headers,
    ), timeout=30)
    print("OK    cleaned up the edit; nothing was changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
