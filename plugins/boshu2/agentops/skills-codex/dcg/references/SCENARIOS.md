# DCG Scenarios

Quick reference for handling common blocks.

---

## 1. Git Reset — Use Alternative

**Blocked:** `git reset --hard HEAD`

❌ "Command blocked. Run `dcg allow-once 12345`."

✓ "Blocked because it destroys uncommitted work. Using `git stash` instead—recoverable if needed."

```bash
git stash -m "experimental changes"
```

---

## 2. Force Push — Use Safer Flag

**Blocked:** `git push --force origin feature-branch`

✓ "Using `--force-with-lease` instead—checks remote hasn't changed since fetch."

```bash
git push --force-with-lease origin feature-branch
```

---

## 3. rm -rf Typo — DCG Saved You

**Blocked:** `rm -rf /home/user/project/` (meant `./build`)

DCG caught the typo. Correct the path:

```bash
rm -rf ./build  # Safe path, won't be blocked
```

---

## 4. DROP DATABASE — Human Decision

**Blocked:** `DROP DATABASE test_db;`

✓ "Blocked as safety measure. Since this is a test database, you can approve with `dcg allow-once 12345`, or I can show contents first."

**Approve for:** Test/dev databases, known context
**Don't approve for:** Production, unrecognized names, uncertainty

---

## 5. K8s Namespace — Show Contents First

**Blocked:** `kubectl delete namespace staging`

✓ "Namespace deletion removes ALL resources. Let me show what's there first:"

```bash
kubectl get all -n staging
```

Then human can approve or you can delete selectively with `-l app=X`.

---

## 6. Documented Procedure Requires It

**Blocked:** `git reset --hard origin/main` (per cleanup docs)

✓ "Procedure requires this. Blocked because it discards local changes. Approve with `dcg allow-once 12345` if no local work to keep."

Even documented procedures deserve checkpoints—docs may be outdated.

---

## 7. False Positive

**Blocked:** `rm -rf ./node_modules` (unusual config)

✓ "This is typically safe—might be a false positive. Options:
1. `dcg allow-once 12345` for this instance
2. Add allowlist entry if recurring"

Suggest allowlist only for genuinely safe, recurring operations.

---

## Anti-Patterns

| Don't | Why |
|-------|-----|
| Retry silently | Human loses visibility |
| Ask for override first | Find alternatives first |
| Treat blocks as errors | They're checkpoints |
| Circumvent detection | Defeats safety system |
