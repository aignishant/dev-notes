# `mp` CLI — Interview Q&A

---

## Q1. What is `mp` and where does it live?

`mp` (marketplace) is the Content Hub CLI — build, validate, test, lint, format, push/pull to dev SOAR. Source at `packages/mp/`. Installed globally via `uv tool install mp --from git+...#subdirectory=packages/mp`.

---

## Q2. What's the Windows gotcha?

`mp` conflicts with a Windows built-in alias. Use `wmp` instead on Windows for all commands. Documented in the README.

---

## Q3. Walk me through your typical development loop with `mp`.

1. `mp dev-env login` (once)
2. `mp dev-env pull integration X` — pull from dev SOAR
3. Edit, add tests
4. `mp format` — auto-format
5. `mp check --fix --static-type-check` — lint + type check
6. `mp test X` — run tests
7. `mp validate integration X --only-pre-build` — quick validate
8. `mp dev-env push integration X` — push to dev SOAR for smoke test
9. `mp validate integration X` — full validate before PR
10. Git commit + open PR

---

## Q4. What does `mp validate` check that CI relies on?

Structural and metadata correctness: required files, YAML validity, identifier consistency, version bumps in release notes, snake_case filenames, password fields without default values, missing ontology for connector-bearing integrations, missing logo files. Plus a full test build to catch import errors and missing resources.

---

## Q5. What's the difference between `mp check` and `mp format`?

`mp format` — auto-formats Python (wraps `ruff format`). Mutates files.
`mp check` — lints (wraps `ruff check`) + optionally type-checks (`--static-type-check` invokes `ty`). Reports issues. With `--fix`, applies safe auto-fixes. With `--unsafe-fixes`, applies fixes that need review.

---

## Q6. What's `--deconstruct` for?

Reverses a build — takes a built zip (typically exported from the SOAR UI) and decomposes it into repo format. Used in two places: (a) the manual contribution flow where a user exports their work from SOAR and needs to contribute it; (b) internally by `mp dev-env pull` to transform what it fetches.

---

## Q7. What's the difference between `mp dev-env push` and the GitHub Action `custom-integration-push`?

`mp dev-env push` is **interactive**, for a single developer pushing their work to their dev SOAR. The GitHub Action is **automated** — it watches the repo's `content/response_integrations/custom/` directory and auto-syncs to a customer's SOAR on every relevant commit. Same underlying mechanism, different invocation.

---

## Q8. What's the difference between `--only-pre-build` and full validation?

Pre-build: cheap structural checks (file presence, YAML parse, identifier consistency) — seconds. Full: adds a test build + module imports + unit tests — minutes. Use pre-build for fast iteration; full before PR.

---

## Q9. How do you get an API Root and API Key for `mp dev-env login`?

API Root: in the SecOps browser, DevTools Console → `localStorage['soar_server-addr']`. API Key: Settings → SOAR Settings → Advanced → API Keys → Create with Admins permission group.

---

## Q10. What does `--include-blocks` do when pushing a playbook?

Pushes nested-workflow blocks along with the parent playbook. Without it, if the target SOAR doesn't have the referenced block deployed, the push succeeds but the playbook is broken. Safer default for playbooks with dependencies.

---

## Q11. Your team reports `mp validate` fails with "integration_identifier mismatch" after a rename. What happened?

The top-level `identifier:` in `definition.yaml` was changed but one or more action/connector/job YAMLs still reference the old value in their `integration_identifier:` field. Grep all YAML files in the integration for the old identifier and update. This is why we say "identifier is immutable after release" — mass-updating N YAML files is error-prone.

---

## Q12. A teammate pushed a new integration but it doesn't appear in SOAR UI. How do you debug?

1. Check `mp dev-env push` output for errors.
2. Refresh SOAR UI browser cache.
3. Check the built zip (`--keep-zip`) and inspect it — does `Manifest.json` look right?
4. Check API Key permissions — is it still in Admins?
5. Check the SOAR logs (if accessible) for upload errors.
6. Try `mp dev-env pull <integration>` — if the pull finds it, the push succeeded but UI cache is stale; if not, push silently failed.

---

## Q13. Why is `mp describe` useful?

It generates AI-produced descriptions for integration actions. For an integration with 30 actions, hand-writing descriptions is tedious. `mp describe` reads the code + YAML and proposes descriptions; devs review and edit. Saves hours and produces consistent tone.

---

## Next

→ **[Section 8: Dev Workflow](../08-dev-workflow/index.md)**
