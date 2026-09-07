# Account Bootstrap Modes

Use this reference whenever an application exposes signup, bootstrap administrator credentials, root reconciliation, or first-run account setup.

## Source Evidence

Classify the exact selected release from these sources in order:

1. Official Kubernetes or Helm values and templates.
2. Official Compose files and release-specific installation docs.
3. Entrypoint, configuration schema, and authentication source code.
4. First-boot logs and the observed first-run page or API flow.

Record one mode before defining Template inputs:

| Mode | Required evidence | Emitted Template contract | Runtime proof |
|---|---|---|---|
| Functional first-user signup | A fresh deployment exposes a supported registration flow | Omit optional administrator/root inputs and bootstrap env/config | Register after readiness, then complete one authenticated action |
| Mandatory bootstrap, deployer-supplied | The server requires an administrator identity before it can serve the signup/login flow, and the selected release documents deployer-selected credentials | Required username or email and password inputs with no defaults | Validate before deploy, then log in with the exact supplied values |
| Mandatory bootstrap, runtime-generated | The server requires an administrator identity before it can serve the login flow, and the selected runtime supports deterministic credential generation plus durable retrieval | Omit administrator inputs; construct the exact valid format and retain the resolved credential in a Secret or documented live runtime source | Retrieve the resolved credential without printing it, then complete login and one authenticated action |
| Optional root reconciliation | Root bootstrap config is optional and first-user signup remains functional | Prefer the first-user signup contract | Complete signup and verify the root overlay is absent |

Functional first-user signup remains the selected contract when root reconciliation is optional. Preserve mandatory bootstrap behavior when the selected release requires it, including Frappe-style site initialization.

## Template Input Capability Boundary

Sealos Template inputs may express:

- `type`
- `description`
- `default`
- `required`
- `options`
- `if`

Regular expressions, minimum or maximum length, character classes, equality, and cross-field constraints require Phase 5.5 validation. Treat every startup-fatal constraint as a pre-deploy rule.

For deployer-supplied mandatory bootstrap credentials:

1. Declare each documented identity field and password as `required: true` with no `default`.
2. Put the exact release-specific constraints in the English `description`.
3. Validate the collected value locally before Template API deployment.
4. Pass the value unchanged through Template API args and the documented bootstrap path.
5. Use that same value for the live login smoke and keep it redacted in output.

For runtime-generated mandatory bootstrap credentials:

1. Confirm the exact selected release documents generated initialization and the credential format.
2. Construct and validate the documented format deterministically before the server starts.
3. Omit administrator inputs unless the selected release documents deployer selection.
4. Retain the resolved credential in a Kubernetes Secret or documented live runtime source.
5. Retrieve it without printing the value, then complete login and one authenticated action.

For generated startup-critical values, use deterministic format construction only when the value is application-internal and the selected runtime supports generated initialization. Keep an unconstrained opaque `${{ random(n) }}` value limited to contracts that accept every emitted character sequence.

## Failure Classification and Repair

Treat a pre-server exit containing password policy, invalid bootstrap configuration, schema validation, or root-user reconciliation errors as a configuration-contract failure. Repair the account mode and credential path before changing CPU or memory.

When a live deployment contains an invalid optional root overlay:

1. Patch the source Template.
2. Patch the highest writable declarative owner that emits the workload.
3. Roll out a fresh Pod and wait through one reconciliation window.
4. Confirm the removed bootstrap key names stay absent from live workload and Pod specs.
5. Inspect only redacted key names in last-applied annotations and ControllerRevisions.
6. Recommend rotation for every credential that reached the cluster.

Deleting historical annotations or revisions requires the user's explicit confirmation.

## Acceptance Checklist

- The exact selected release has one recorded account mode.
- Signup mode emits no optional administrator/root inputs or bootstrap injection.
- Deployer-supplied mandatory mode validates required credentials before deploy and preserves them byte-for-byte through login.
- Runtime-generated mandatory mode constructs the documented format, retains the resolved credential, and proves redacted live login.
- First-boot logs contain no account-policy or reconciliation exit.
- Registration or login completes from a fresh session.
- One authenticated page or API action succeeds.
- Credential values stay redacted in diagnostics and reports.
