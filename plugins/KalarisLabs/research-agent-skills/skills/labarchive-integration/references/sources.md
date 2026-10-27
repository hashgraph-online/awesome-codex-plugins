# Sources and Verification Notes

Research date: **2026-07-23**.

Official LabArchives pages were located with `parallel-cli search` and read with
`parallel-cli extract`. GitHub repository metadata was cross-checked with
GitHub's API. No search output or credential material is stored in this skill.

## Official API sources

### ELN overview and regional API hosts

https://mynotebook.labarchives.com/share/LabArchives%20API/NS4yfDI3LzQvVHJlZU5vZGUvMTF8MTMuMg

- Page revision: **2025-11-03**
- Describes the ELN API as REST-like.
- Lists API hosts for US/rest of world, Australia/New Zealand, UK, Europe
  outside the UK, and Canada.
- Requires HTTPS.
- States that many responses are XML and child-element order is not fixed.

### Requirements and best practices

https://mynotebook.labarchives.com/share/LabArchives%20API/MTM2LjV8MjcvMTA1L1RyZWVOb2RlLzM2MzY3OTM2NjF8MzQ2LjU=

- Page revision: **2024-06-28**
- Credentials are issued for a specific organization/vendor and purpose.
- Large batches must be serialized or staggered by at least one second.
- HTTP 4xx responses must not be automatically retried.
- Eligible retries must wait at least one second, back off, and stop at a
  bounded count/duration.
- `expires` should represent current epoch milliseconds, with server-clock
  adjustment, not a future expiry.

### Call authentication

https://mynotebook.labarchives.com/share/LabArchives%20API/Ny44fDI3LzYvVHJlZU5vZGUvMTE1MzU5MTAyNXwxOS44

- Page revision: **2023-05-10**
- Defines Base64(HMAC-SHA-512) over the concatenation of Access Key ID, method
  input, and `expires`, using the Access Password as the HMAC key.
- Documents `akid`, `expires`, and URI-encoded `sig` query parameters.
- The published dummy test vector is reproduced by
  `scripts/entry_operations.py self-test`.

### API user login and UID

https://mynotebook.labarchives.com/share/LabArchives%20API/ODEuOXwyNy82My05My9UcmVlTm9kZS8yMjYyMTU0MTg3fDIwNy44OTk5OTk5OTk5OTk5OA==

- Page revision: **2023-03-03**
- Documents the signed `/api_user_login` redirect, returned `auth_code` and
  email, and redemption through `users::user_access_info`.
- Defines the user-generated temporary password token alternative.
- States that UIDs are bound to the Access Key ID and persist until revoked.

### ELN API class tree

https://mynotebook.labarchives.com/share/LabArchives%20API/MS4zfDI3LzEvVHJlZU5vZGUvODYxMDc1MjB8My4z

- Current tree includes entries, search tools, utilities, users, tree tools,
  notifications, notebooks, and site-license tools.
- Method pages, not names inferred from other clients, are the source of truth.

### ELN entry response elements

https://mynotebook.labarchives.com/share/LabArchives%20API/NjguOXwyNy81My9UcmVlTm9kZS8xODUxMDkwNDk2fDE3NC45

- Documents common `<entry>` XML fields and optional entry/comment data.
- Distinguishes attachment metadata from retrieval of attachment bytes.

### LA container file

https://mynotebook.labarchives.com/share/LabArchives%20API/Ni41fDI3LzUvVHJlZU5vZGUvNDQ3MDk3MTI0fDE2LjU=

- Original page revision shown as **2014-11-10**; the public page also contained
  an example-file revision dated **2026-03-02** at research time.
- Defines an LA container as a ZIP with `lamanifest.xml`, an application file,
  preview file, and UTF-8 index file.
- This format is not the same thing as a notebook-backup response.

### Inventory authentication

https://mynotebook.labarchives.com/share/LabArchives%20API/MTQ0LjN8MjcvMTExL1RyZWVOb2RlLzM5NjYzNjc4MjJ8MzY2LjI5OTk5OTk5OTk5OTk1

- Page revision: **2025-11-24**
- Inventory uses the shared LabArchives authentication flow.
- Requires a new signature for each exact relative route.
- Lists `X-LabArchives-UId`, `X-LabArchives-AKId`,
  `X-LabArchives-LabId`, `X-LabArchives-Signature`, and
  `X-LabArchives-Expires`.
- Route parameters are included in the signature input; query parameters are
  excluded.

### Inventory API v1 item creation

https://mynotebook.labarchives.com/share/LabArchives%20API/MTg4LjV8MjcvMTQ1L1RyZWVOb2RlLzEyOTcxODY5ODF8NDc4LjU=

- Page revision: **2026-04-02**
- The public navigation labels the Inventory surface **APIs (v1)**.
- Explicitly documents `POST /public/v1/inventory` and its JSON schema.
- The navigation also exposes read/update item routes and sections for item
  types, orders, storage locations, and vendors.

## Official product and help sources

### Regional browser login URLs

https://help.labarchives.com/hc/en-us/articles/11728160845332-Using-an-Institutional-Single-Sign-on-for-LabArchives-Access

- Updated **2025-11-04**
- Lists separate login URLs for US/rest of world, Canada,
  Australia/New Zealand, UK, and Europe.

### ELN API entitlement

https://help.labarchives.com/hc/en-us/articles/11723701830676-ELN-for-Research-Introduction-and-Subscription-Plans

- Updated **2025-09-24**
- Lists developer API access under the Enterprise plan.

### Inventory API entitlement

https://help.labarchives.com/hc/en-us/articles/11811035048212-Inventory-FAQs

- Updated **2026-05-19**
- Limits API availability to Enterprise and Enterprise Plus licensees.
- Requires Inventory account/API access and directs eligible users to support.

### Integration index

https://help.labarchives.com/hc/en-us/sections/11732611360660-Integrations

Current index at research time included GraphPad Prism, SnapGene, Geneious,
Proofig AI, Jupyter, REDCap, Protocols.io, Qeios, SciSpace, Vernier Logger Pro,
and DataCite.

Selected dated articles:

- Jupyter, updated **2025-09-08**:
  https://help.labarchives.com/hc/en-us/articles/11780569021972-Jupyter-Integration
- REDCap, updated **2025-09-05**:
  https://help.labarchives.com/hc/en-us/articles/11780613160980-REDCap-Integration
- Protocols.io, updated **2025-09-22**:
  https://help.labarchives.com/hc/en-us/articles/11780572389524-Protocols-io-Integration

## Community Python client status

Community projects are not official LabArchives sources and are not installed by
this skill.

### `mcmero/labarchives-py`

https://github.com/mcmero/labarchives-py

GitHub metadata checked **2026-07-23**:

- personal/community repository, not LabArchives-owned,
- 3 commits total,
- last commit: **2022-08-10** (`1b5b745baaf9`),
- no tags,
- no GitHub releases,
- no matching PyPI project found in the searches performed,
- no official LabArchives endorsement found.

Conclusion: remove the old unpinned Git clone installation and do not recommend
this wrapper by default.

### `nimh-dsst/labapi`

- PyPI: https://pypi.org/project/labapi/
- Source: https://github.com/nimh-dsst/labapi
- Documentation: https://nimh-dsst.github.io/labapi/

Verified status on **2026-07-23**:

- community project under the NIMH DSST GitHub organization, not
  LabArchives-owned,
- PyPI stable release **1.1.1**, published **2026-07-06**,
- Python requirement **>=3.10**,
- GitHub also had prerelease **1.2.0rc2**, published **2026-07-23**,
- repository activity was current on the research date,
- no official LabArchives endorsement was found.

The published documentation offers optional `.env` auto-loading, which this
skill intentionally does not recommend for agent workflows. PyPI 1.1.1 and the
current repository metadata also showed differing license labels during this
review; inspect the exact selected artifact and license before adoption.

If an institution explicitly approves this client, pin the stable release rather
than a branch or prerelease:

```bash
uv add "labapi==1.1.1"
```

Review transitive dependencies and use only named process-environment variables.
The standard-library bundled helpers remain the default here.

## Claims not established by public official sources

The research did **not** establish:

- a complete absolute regional base-URL table for Inventory API v1,
- a numeric requests-per-minute or burst quota,
- a generic LabArchives OAuth 2.0 authorization/token endpoint,
- an official LabArchives Python SDK,
- a blanket backward-compatibility guarantee for the legacy ELN API,
- universal attachment extensions, file-size limits, or archive formats,
- that every advertised product integration exposes a programmable API.

Obtain missing product-specific details from institution/vendor-provided API
documentation or LabArchives support. Do not fill gaps from model memory or a
community wrapper.
