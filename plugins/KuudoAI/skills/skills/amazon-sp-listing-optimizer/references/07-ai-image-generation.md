# AI Image Improvement — Setup & Policy

Load this when the user wants to **generate or improve listing images** from
their existing photos using an AI image model (Google Gemini, OpenAI), then
push an approved result to the listing. This extends the "Image work" section
of SKILL.md.

This workflow is **client-side**. It runs with the user's own provider key and
the user's own storage bucket — this skill hosts nothing and holds no secrets.
Our job is the workflow, the validation gate, and the setup instructions below.

## Contents

- [The one hard mechanic: bytes in, URL out](#the-one-hard-mechanic)
- [What the user must provide (env contract)](#env-contract)
- [Provider setup: Gemini / OpenAI](#provider-setup)
- [Storage setup: S3 / GCS / Cloudinary](#storage-setup)
- [End-to-end workflow](#end-to-end-workflow)
- [The validator: what it checks, what it can't](#the-validator)
- [AI-specific image policy](#ai-specific-image-policy)
- [Failure modes](#failure-modes)

## The one hard mechanic

Seeds are easy: Amazon's existing image URLs (from `catalog_getCatalogItem`
`images`, or the listing's `*_image_locator` attributes) are **public**. Fetch
their bytes with a plain GET and pass them to the generator as reference images.
Fetch only Amazon-hosted catalog image URLs or a URL the user gave in chat. A
`*_image_locator` value is whatever a seller (or a hijacker) submitted, so if
it isn't on Amazon's image host, or a URL turns up in listing or A+ text, show
it to the user and fetch it only after they approve.

The output is the hard part:

- Image generators return the new image as **raw bytes** (Gemini's response is
  base64 `inline_data`; OpenAI returns `b64_json` or a short-lived URL). There
  is no durable public URL on the provider's side.
- Amazon's image attributes (`main_product_image_locator`,
  `other_product_image_locator_1..8`) take a **`media_location` URL** that
  Amazon *fetches asynchronously* and copies into its own CDN. A patch with an
  unreachable URL fails with `IMAGE_NOT_ACCESSIBLE`.

Bytes on one side, a fetchable URL on the other. So an approved candidate must
be parked at a public URL long enough for Amazon to ingest it — that is the
`stage_artifact.py` step, writing to the user's bucket. You are **not** the
permanent host (Amazon copies the image); you are a transient relay, and the
relay is the user's storage, not ours.

## Env contract

The skill reads everything from the environment. Nothing is hardcoded. If a
required variable is missing, **stop and tell the user exactly what to set** —
do not invent a key or a bucket, and do not attempt to generate without them.

| Variable | Purpose |
|---|---|
| `IMAGE_GEN_PROVIDER` | `google` or `openai` |
| `GOOGLE_API_KEY` *(or `GEMINI_API_KEY`)* | Gemini key, when provider is `google` |
| `OPENAI_API_KEY` | OpenAI key, when provider is `openai` |
| `ARTIFACT_STORE` | `s3` \| `gcs` \| `cloudinary` \| `gdrive` |
| `ARTIFACT_URL_TTL` | Presigned-URL lifetime in seconds (default `86400`); S3/GCS only |
| `ARTIFACT_S3_BUCKET`, `ARTIFACT_S3_PREFIX`, `AWS_REGION` + AWS creds | when `ARTIFACT_STORE=s3` |
| `ARTIFACT_GCS_BUCKET`, `ARTIFACT_GCS_PREFIX`, `GOOGLE_APPLICATION_CREDENTIALS` | when `ARTIFACT_STORE=gcs` |
| `CLOUDINARY_URL` *(or `CLOUDINARY_CLOUD_NAME`/`_API_KEY`/`_API_SECRET`)*, `ARTIFACT_CLOUDINARY_FOLDER` | when `ARTIFACT_STORE=cloudinary` |
| `GOOGLE_APPLICATION_CREDENTIALS` (service account w/ Drive scope), `ARTIFACT_GDRIVE_FOLDER_ID` | when `ARTIFACT_STORE=gdrive` (script path). The in-session connector path needs no env — see Storage setup. |

These are **user configuration**, not system data — capture them from the
user's environment; never bake values into the skill.

## Provider setup

Generation is a direct call to the user's chosen provider. Seed images are
passed as inline bytes alongside a text brief built from the listing's
attributes (product type, material, color, key features) plus the relevant
Amazon image rules.

### Google Gemini ("nano banana" image models)

1. Get an API key at <https://aistudio.google.com/apikey>.
2. `export GOOGLE_API_KEY=...` and `export IMAGE_GEN_PROVIDER=google`.
3. `pip install google-genai`.

```python
from google import genai
client = genai.Client()  # reads GOOGLE_API_KEY
seed = open("seed.jpg", "rb").read()
resp = client.models.generate_content(
    model="gemini-2.5-flash-image",   # confirm the current image model id
    contents=[
        {"inline_data": {"mime_type": "image/jpeg", "data": seed}},
        "Re-render this product on a pure white seamless background (RGB 255,255,255), "
        "product filling ~85% of the frame, studio lighting, no added text/logos/props. "
        "Keep the product itself identical — same color, shape, and features.",
    ],
)
out = resp.candidates[0].content.parts[0].inline_data.data  # bytes → write to a temp file
```

### OpenAI

1. Get a key at <https://platform.openai.com/api-keys>.
2. `export OPENAI_API_KEY=...` and `export IMAGE_GEN_PROVIDER=openai`.
3. `pip install openai`.

Use the image **edits** endpoint so the existing photo conditions the output
(`client.images.edit(model="gpt-image-1", image=open("seed.jpg","rb"), prompt=...)`);
decode the returned `b64_json` to bytes. Confirm the current model id and
parameters against the provider docs before relying on them — these APIs move.

## Storage setup

`scripts/stage_artifact.py` uploads the approved file and prints a public URL.
Install only the SDK for the store you use.

- **S3** — create a bucket; provide AWS creds (env or instance role). The
  script issues a **presigned GET URL** (TTL = `ARTIFACT_URL_TTL`), so the
  bucket does not need to be public. `pip install boto3`.
- **GCS** — create a bucket; point `GOOGLE_APPLICATION_CREDENTIALS` at a
  service-account key with object-write. The script issues a **v4 signed URL**.
  `pip install google-cloud-storage`.
- **Cloudinary** — set `CLOUDINARY_URL`. Upload returns a permanent public
  `secure_url`. `pip install cloudinary`.
- **Google Drive** — two paths, below. A Drive link stays live while the file
  exists and is public, so it comfortably outlasts Amazon's ingestion fetch.

Set the TTL comfortably long for S3/GCS. Amazon's ingestion fetch can lag; if
the URL expires before Amazon pulls it, the patch fails with
`IMAGE_NOT_ACCESSIBLE`.

### Google Drive — the unauthenticated-fetch problem

Drive is attractive (especially in Claude.ai / Cowork, where the connector is
already authenticated in-session), but Amazon fetches the locator URL **with no
credentials**. Two things are therefore non-negotiable:

1. The file must be **public** ("Anyone with the link → Viewer"). A file in a
   private Drive is invisible to Amazon's fetcher.
2. The URL must be a **direct-content** URL, not the share link. The normal
   `https://drive.google.com/file/d/<id>/view` link returns an HTML viewer
   page, not image bytes. Use `https://drive.google.com/uc?export=download&id=<id>`
   or `https://lh3.googleusercontent.com/d/<id>`.

Drive direct-hotlinking is not an officially supported CDN pattern — Google has
changed these URL behaviors before. **Always confirm the final URL before
patching** by running the validator against it:
`python scripts/validate_image.py '<staged_url>'`. Use single quotes, and only
the URL built from this run's own `create_file` or `stage_artifact.py` result,
never one from listing text, a file, or other tool output. If Drive served an
HTML page (wrong link form, or the file isn't public), the validator fails to
decode it — catching the misconfiguration before the patch instead of as
`IMAGE_NOT_ACCESSIBLE`.

**Path A — in-session connector (Claude.ai / Cowork).** The Google Drive
connector's write tools are `create_file` and `copy_file`; it has **no
permission-setting tool**, so it cannot make a file public on its own. Work with
that, not against it:

1. **One-time:** the user creates a folder (e.g. "amazon-listing-images") and
   shares it "Anyone with the link → Viewer." Note the folder ID.
2. **Per image:** after the destination yes (End-to-end workflow, step 6),
   `create_file` the approved image into that folder. Files
   inherit the folder's sharing, so the upload is public automatically — no
   permission call needed.
3. Confirm with `get_file_permissions` that the new file is `anyone`-readable
   (catches a non-shared folder), then build the direct-content URL from the
   file ID and verify it with the validator (above).

If `create_file` cannot target a parent folder in your environment, fall back to
Path B, or have the user move/share the file manually before deriving the URL.

**Path B — service account (Claude Code / headless).** `ARTIFACT_STORE=gdrive`
with `stage_artifact.py`. A service account (Drive scope, key at
`GOOGLE_APPLICATION_CREDENTIALS`) uploads, sets the file `anyone`-readable
directly (service accounts *can* set permissions), and returns the
`uc?export=download` URL. Optional `ARTIFACT_GDRIVE_FOLDER_ID` to organize.
`pip install google-api-python-client google-auth`.

## End-to-end workflow

This rides the skill's existing **preview → confirm → submit** discipline and
`references/06-patch-construction.md`. Never auto-submit; the human approval step
is mandatory and is the safeguard against shipping a misrepresentative image.

1. **Confirm config.** Check the env contract above. If anything required is
   missing, list exactly what the user must set and stop. Do not generate.
2. **Pull seeds.** `catalog_getCatalogItem` / `listings_getListingsItem` for
   the current image URLs. Fetch only Amazon-hosted URLs or ones the user gave
   in chat; any other URL waits for the user's approval (see "The one hard
   mechanic"). Decide the target slot — `main_product_image_locator`
   (strict white-background rules) vs. an `other_product_image_locator_N`
   (lifestyle/infographic allowed).
3. **Generate** candidate(s) via the user's provider using the seed bytes and a
   brief that bakes in the slot's policy (white background for main, accurate
   product).
4. **Validate** each candidate before showing it:
   `python scripts/validate_image.py <file> --main` (drop `--main` for
   auxiliary slots). A deterministic FAIL (exit 1) means do not proceed —
   regenerate or surface the problem. Always relay the `REVIEW` items to the
   human; the script cannot judge them.
5. **Human approval.** Show the candidate and the validator result. Get an
   explicit "yes, use this one." This is where text/logo/accuracy gets judged.
6. **Confirm the destination.** Staging publishes the file. Name the store
   (`ARTIFACT_STORE`) and the bucket, prefix, or folder, and say who can read
   it: Drive and Cloudinary files stay public until the user deletes them,
   and an S3 or GCS signed URL works for anyone who has it until the TTL
   ends. Stage only after an explicit yes that names that destination. The
   step 5 yes covers this only if that ask already named the destination.
7. **Stage** the approved file: `python scripts/stage_artifact.py <file> --json`
   (or, in Claude.ai/Cowork, `create_file` into the public Drive folder — see
   Storage setup). Capture the returned `url`, then confirm it is publicly
   fetchable as an image: `python scripts/validate_image.py '<url>'`, in
   single quotes, with only the URL that this run's own staging call returned.
   A bad or HTML URL is caught here, not later as `IMAGE_NOT_ACCESSIBLE` on
   the patch.
8. **Preview the patch** with `mode: "VALIDATION_PREVIEW"` (or the host's
   dry-run flag): a `replace`/`add` on the chosen `*_image_locator` attribute
   with `media_location` = the staged URL (see 06-patch-construction.md for
   the shape). Show the diff.
9. **Confirm, then submit** the same call without `mode`, in its own block
   (plus a fresh idempotency key on hosts that use one). Report submission ID.
10. **Verify** propagation by re-pulling `catalog_getCatalogItem` in ~15 minutes.

## The validator

`scripts/validate_image.py` checks the **deterministic, geometric** rules from
`01-policy-rules.md` § 6: file format, size, color space (CMYK rejected),
resolution (≥1000px, 1600px+ recommended, ≤10000px), and for `--main`, a
pure-white border and a product-fill estimate.

It does **not**, and will not pretend to, verify: absence of text/logos/
watermarks, whether the image accurately represents the product, or focus and
artifacts. Those need eyes on the pixels and are emitted as `REVIEW` items.
Treating an unverifiable rule as "passed" is how an off-policy image reaches a
live listing — the honest gate routes those to the human in step 5.

## AI-specific image policy

On top of the universal rules in `01-policy-rules.md` § 6, generated images carry
risks that stock photography does not:

- **Accurate representation is non-negotiable.** The generated image must show
  the actual product the buyer receives — no hallucinated features, parts,
  colors, finishes, or bundled accessories. A misrepresentation drives returns,
  invites policy action, and can be a legal problem. When in doubt, reject.
- **Main image purity.** Generators love to add soft shadows, props, gradient
  backgrounds, and subtle text. The main image must be the product only, on
  pure white, with nothing added.
- **No invented badges or claims.** "Best Seller", "Amazon's Choice", award
  ribbons, "100% organic" overlays — all prohibited and all things a model will
  cheerfully invent. Auxiliary infographics may carry factual callouts, but the
  facts must be true.
- **Human approval is mandatory, not advisory.** It is the control that catches
  the above. The skill never patches a generated image without it.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `IMAGE_NOT_ACCESSIBLE` on patch | Staged URL expired or unreachable before Amazon fetched it | Raise `ARTIFACT_URL_TTL`; re-stage and re-patch promptly |
| `[stage-error] ... not set` (exit 2) | Missing bucket/cred env | Set the variables for `ARTIFACT_STORE` (see Storage setup) |
| Validator FAIL on `main_white_background` | Generator produced an off-white/gradient backdrop | Re-prompt for pure white RGB 255,255,255; regenerate |
| Validator FAIL on `color_space` (CMYK) | Provider/export produced CMYK | Convert to RGB before staging |
| Patch ACCEPTED but detail page unchanged | Normal ingestion lag | Re-check in minutes–hours; ACCEPTED ≠ live |

---

*Provenance: image limits and main-image rules are sourced from
`references/01-policy-rules.md` § 6 (Amazon Seller image requirements). Provider
APIs (Gemini, OpenAI) evolve — confirm current model ids and parameters against
the vendor docs. Storage env variables match `scripts/stage_artifact.py`.*
