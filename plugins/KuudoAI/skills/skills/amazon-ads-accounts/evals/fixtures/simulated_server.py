#!/usr/bin/env python3
"""Simulate the Kuudo Amazon Ads MCP account tools for dry-run evals.

Usage:
  simulated_server.py <world> <calls.jsonl> search "<query>"
  simulated_server.py <world> <calls.jsonl> get_schema <tool1,tool2>
  simulated_server.py <world> <calls.jsonl> call <tool> '<json arguments>'

Each `call` stands in for one `await call_tool(name, arguments)` inside `execute`.
Every request is appended to calls.jsonl so grading can read the arguments.

Behavior mirrors read-only probes of the live server on 2026-10-30:
- Names outside the catalog fail with `Unknown tool`.
- Undeclared top-level keys such as `body` and `skill` are dropped without an error.
- `allv1_QueryAdvertiserAccount` returns global accounts unless asked otherwise, and
  its ID filter rejects anything that is not a global advertiser account ID.
- `ac_listProfiles`, `ac_getProfileById`, and `list_identities` cover only the identity's region.
- `allv1_QueryAccountLink` and `beta_QueryAccountLink` return 401 in every scope.
- `list_identities` holds a partial profile list, and `ac_ListAdsAccounts` returns only
  accounts with marketplace entries (probed 2026-11-02).

A world with several identities is an assumption, because no probed login had more
than one. Data calls fail until one is selected, using the SP-API server's message,
and each identity sees its own accounts.

Writes succeed so that a premature write is recorded instead of blocked.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "worlds.json"), encoding="utf-8"))
GLOBAL_ID = re.compile(r"^amzn1\.ads-account\.g\.[A-Za-z0-9]+$")
UNAUTHORIZED = (
    "HTTP error 401: Unauthorized - {'message': 'Unauthorized exception while "
    "handling 3P Request: Unauthorized'}"
)
FILTER = {"type": "object", "required": ["include"], "properties": {"include": {"type": "array", "items": {"type": "string"}}}}
LINK_SCHEMA = {
    "type": "object",
    "required": ["relationshipTypeFilter"],
    "properties": {
        "relationshipTypeFilter": {"type": "object", "required": ["include"], "properties": {"include": {"type": "array", "maxItems": 1, "items": {"enum": ["CHILD", "PARENT"]}}}},
        "accountIdFilter": FILTER,
        "accountNameFilter": FILTER,
        "accountTypeFilter": {"type": "object", "required": ["include"], "properties": {"include": {"type": "array", "items": {"enum": ["ADVERTISER_ACCOUNT", "MANAGER_ACCOUNT"]}}}},
        "maxResults": {"type": "integer", "minimum": 10, "maximum": 100, "default": 100},
        "nextToken": {"type": "string"},
    },
}
NO_ARGS = {"type": "object", "properties": {}}


def selection_schema(key):
    return {"type": "object", "required": [key], "properties": {key: {"type": "string"}}}


READS = {
    "allv1_QueryAdvertiserAccount": (
        "List advertiser accounts",
        {
            "type": "object",
            "properties": {
                "advertiserAccountIdFilter": {"type": "object", "required": ["include"], "properties": {"include": {"type": "array", "minItems": 1, "maxItems": 100, "items": {"type": "string"}}}},
                "isGlobalAccountFilter": {"type": "object", "required": ["include"], "properties": {"include": {"type": "array", "minItems": 1, "maxItems": 1, "items": {"type": "boolean"}}}},
                "maxResults": {"type": "integer", "minimum": 10, "maximum": 100, "default": 100},
                "nextToken": {"type": "string"},
            },
        },
    ),
    "allv1_QueryAccountLink": ("Query Account Links for a given advertising account", LINK_SCHEMA),
    "beta_QueryAccountLink": ("Query Account Links for a given advertising account", LINK_SCHEMA),
    "ac_getManagerAccountsForUser": ("Returns all manager accounts that a user has access to, along with metadata for the Amazon Ads accounts that are linked to each manager account.", NO_ARGS),
    "ac_ListAdsAccounts": ("List all advertising accounts for the user associated with the access token.", NO_ARGS),
    "ac_listProfiles": ("Note that this operation does not return a response unless the current account has created at least one campaign using the advertising console.", NO_ARGS),
    "ac_getProfileById": ("This operation does not return a response unless the current account has created at least one campaign using the advertising console.", {"type": "object", "required": ["profileId"], "properties": {"profileId": {"type": "integer"}}}),
    "list_identities": ("List Kuudo identities that grant access to Amazon resources. Select an identity before choosing an Amazon profile or marketplace. These are provider identities, not an inventory of Amazon profiles or marketplaces; use the Amazon listing tools to discover those resources.", NO_ARGS),
    "get_active_profile": ("Report which advertising profile calls are currently scoped to.", NO_ARGS),
    "get_active_account": ("Report the selected Amazon Ads account header value.", NO_ARGS),
    "get_active_manager_account": ("Report the selected Amazon Ads manager-account header value.", NO_ARGS),
}
SELECTIONS = {
    "set_active_identity": ("Select a Kuudo identity that grants access to Amazon resources.", "identity_id"),
    "set_active_profile": ("Choose the Amazon advertising profile subsequent calls act on.", "profile_id"),
    "set_active_account": ("Choose the Amazon Ads account header for subsequent calls.", "account_id"),
    "set_active_manager_account": ("Choose the Amazon Ads manager-account header for later calls.", "manager_account_id"),
}
WRITES = {
    "allv1_CreateAdvertiserAccount": "Create advertiser accounts",
    "allv1_UpdateAdvertiserAccount": "Update advertiser accounts",
    "allv1_CreateManagerAccount": "Create manager accounts",
    "allv1_DeleteAccountLink": "Delete Account Links for a given advertising account",
    "beta_DeleteAccountLink": "Delete Account Links for a given advertising account",
    "ac_createManagerAccount": "Creates a new Amazon Advertising Manager account.",
    "ac_LinkAdvertisingAccountsToManagerAccountPublicAPI": "Link Amazon Advertising accounts or advertisers with a Manager Account.",
    "ac_UnlinkAdvertisingAccountsToManagerAccountPublicAPI": "Unlink Amazon Advertising accounts or advertisers with a Manager Account.",
}


def describe(name):
    if name in READS:
        return READS[name][0]
    if name in SELECTIONS:
        return SELECTIONS[name][0]
    return WRITES[name]


def search(query):
    terms = [term for term in re.split(r"\W+", query.lower()) if term]
    scored = []
    for name in [*READS, *SELECTIONS, *WRITES]:
        haystack = (name + " " + describe(name)).lower()
        scored.append((sum(term in haystack for term in terms), name))
    matches = [name for score, name in sorted(scored, key=lambda pair: -pair[0]) if score][:10]
    lines = [f"- {name}: {describe(name)}" for name in matches]
    return f"{len(matches)} of 765 tools:\n\n" + "\n".join(lines)


def schema(name):
    if name in READS:
        return {"name": name, "description": READS[name][0], "inputSchema": READS[name][1], "annotations": {"readOnlyHint": True}}
    if name in SELECTIONS:
        return {"name": name, "description": SELECTIONS[name][0], "inputSchema": selection_schema(SELECTIONS[name][1])}
    if name in WRITES:
        return {"name": name, "description": WRITES[name], "inputSchema": {"type": "object"}, "annotations": {"readOnlyHint": False}}
    return None


def get_schema(names):
    found = [schema(name) for name in names if schema(name)]
    missing = [name for name in names if not schema(name)]
    return {"tools": found + ([{"not_found": missing}] if missing else [])}


def query_accounts(world, args):
    ids = (args.get("advertiserAccountIdFilter") or {}).get("include")
    if ids:
        bad = [value for value in ids if not GLOBAL_ID.match(str(value))]
        if bad:
            return {"error": f"HTTP error 400: Bad Request - {{'code': 'BAD_REQUEST', 'message': 'Invalid account ids: {bad}. Expected format: amzn1.ads-account.g.<alphanumeric> (e.g., amzn1.ads-account.g.EXAMPLE)'}}"}
        rows = [DATA["accounts"][key] for page in world["global_pages"] for key in page]
        return {"advertiserAccounts": [row for row in rows if row["advertiserAccountId"] in ids]}
    wants_global = (args.get("isGlobalAccountFilter") or {}).get("include", [True])[0]
    pages = world["global_pages"] if wants_global else world["non_global_pages"]
    token = args.get("nextToken")
    index = 0
    if token:
        if not re.fullmatch(r"page-\d+", str(token)) or int(token[5:]) > len(pages):
            return {"error": "HTTP error 400: Bad Request - {'code': 'BAD_REQUEST', 'message': 'Invalid nextToken'}"}
        index = int(token[5:]) - 1
    response = {"advertiserAccounts": [DATA["accounts"][key] for key in pages[index]]}
    if index + 1 < len(pages):
        response["nextToken"] = f"page-{index + 2}"
    return response


def list_ads_accounts(world):
    rows = [DATA["accounts"][key] for page in world["global_pages"] for key in page]
    return {
        "adsAccounts": [
            {
                "adsAccountId": row["advertiserAccountId"],
                "accountName": row["displayName"],
                "alternateIds": row["alternateIds"],
                "countryCodes": [entry["countryCode"] for entry in row["alternateIds"] if "profileId" in entry],
                "status": "CREATED",
            }
            for row in rows
            if any("profileId" in entry for entry in row["alternateIds"])
        ]
    }


def identity_row(identity_id, label, region, profile_keys):
    profiles = [
        {
            "profileId": row["profileId"],
            "region": region,
            "countryCode": row["countryCode"],
            "marketplaceId": row["accountInfo"]["marketplaceStringId"],
            "accountId": row["accountInfo"]["id"],
            "accountName": row["accountInfo"]["name"],
            "accountType": row["accountInfo"]["type"],
            "dailyBudgetCurrency": row["currencyCode"],
        }
        for row in (DATA["profiles"][key] for key in profile_keys)
    ]
    return {"id": identity_id, "label": label, "attributes": {"provider": "amazon_ads", "mode": "managed_app", "region": region, "profiles": profiles}}


def identities(world):
    if "identities" not in world:
        return [identity_row("101", "Amazon Ads connection (NA)", "na", world["profiles"])]
    return [identity_row(item["id"], item["label"], item["region"], item["listed_profiles"]) for item in world["identities"]]


def scope(world, state):
    """Return the selected identity's data, or None when several exist and none is selected."""
    if "identities" not in world:
        return world
    for item in world["identities"]:
        if item["id"] == state.get("get_active_identity"):
            return item
    return None


def call(world, state, name, args):
    if name in WRITES:
        return {"result": "accepted"}
    if name in SELECTIONS:
        key = SELECTIONS[name][1]
        if key not in args:
            return {"error": f"Missing required argument: {key}"}
        state[name.replace("set_", "get_")] = str(args[key])
        return {"result": f"{name.replace('set_active_', '').replace('_', ' ').capitalize()} set to {args[key]}."}
    if name not in READS:
        return {"error": f"Unknown tool: {name}"}
    if name == "list_identities":
        return identities(world)
    if name.startswith("get_active_"):
        label = name.replace("get_active_", "").replace("_", " ")
        return {"result": state.get(name, f"No active {label}.")}
    world = scope(world, state)
    if world is None:
        return {"error": "Provider identity selection is required."}
    if name == "allv1_QueryAdvertiserAccount":
        return query_accounts(world, args)
    if name == "ac_ListAdsAccounts":
        return list_ads_accounts(world)
    if name in ("allv1_QueryAccountLink", "beta_QueryAccountLink"):
        if not (args.get("relationshipTypeFilter") or {}).get("include"):
            return {"error": "Input validation failed: 'relationshipTypeFilter' is a required property"}
        return {"error": f"call_tool('{name}') failed: Error calling tool '{name}': {UNAUTHORIZED}"}
    if name == "ac_getManagerAccountsForUser":
        return {"managerAccounts": [DATA["managers"][key] for key in world["managers"]]}
    if name == "ac_listProfiles":
        return [DATA["profiles"][key] for key in world["profiles"]]
    if name == "ac_getProfileById":
        for key in world["profiles"]:
            if DATA["profiles"][key]["profileId"] == str(args.get("profileId")):
                return DATA["profiles"][key]
        return {"error": f"HTTP error 404: Not Found - {{'code': 'NOT_FOUND', 'details': 'Profile with id {args.get('profileId')} was not found for this advertiser'}}"}
    return {"error": f"Unknown tool: {name}"}


def main(argv):
    if len(argv) < 4:
        sys.exit(__doc__)
    world_name, log_path, command = argv[1], argv[2], argv[3]
    world = DATA["worlds"].get(world_name)
    if world is None:
        sys.exit(f"Unknown world: {world_name}")
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    state_path = log_path + ".state"
    state = json.load(open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {}

    if command == "search":
        entry, result = {"tool": "search", "args": {"query": argv[4]}}, search(argv[4])
    elif command == "get_schema":
        names = [name.strip() for name in argv[4].split(",")]
        entry, result = {"tool": "get_schema", "args": {"tools": names}}, get_schema(names)
    elif command == "call":
        arguments = json.loads(argv[5]) if len(argv) > 5 else {}
        entry = {"tool": argv[4], "args": arguments}
        result = call(world, state, argv[4], arguments)
    else:
        sys.exit(__doc__)

    entry["error"] = result.get("error") if isinstance(result, dict) else None
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")
    with open(state_path, "w", encoding="utf-8") as saved:
        json.dump(state, saved)
    print(result if isinstance(result, str) else json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv)
