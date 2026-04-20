# CI/CD — Interview Q&A

---

## Q1. Walk me through what happens from PR open to merge-ready.

PR opened → CI detects changed files → matrix of validation jobs runs in parallel: `Validate Integrations`, `Validate Playbooks`, `Validate Parsers` (standalone), `Lint & Format`, `Unit Tests`, `CLA Check`. If parsers changed, contributor also manually triggers `Validate Google & Parsers` against live SecOps. All required checks must be green before the Repository Ruleset allows merge. Reviewer approves. Squash-merged to `main`. Internal publishing pipeline picks up and publishes to Content Hub registry.

---

## Q2. What are the two parser validation stages and why?

**Stage 1 (Validate Parsers)** — automatic, tests folder structure + unit test diffs + log_type validity. Cheap, runs in CI.

**Stage 2 (Validate Google & Parsers)** — manually triggered by contributor via `secops` CLI against a live SecOps instance with real customer logs. Tests parse efficiency and UDM field-coverage regression. Manual because access restrictions prevent full automation — CI can't have customer-data credentials.

---

## Q3. What's the `custom-integration-push` GitHub Action for?

A reusable Action (`chronicle/content-hub/actions/custom-integration-push@main`) for customers to auto-sync their custom integrations from their own repo to their SOAR instance. Supports API Key (recommended) and Username/Password auth. Only runs when relevant files change in `content/response_integrations/custom/`.

---

## Q4. CLA check is failing after you've signed the CLA. What do you do?

Push an empty commit to re-trigger the check: `git commit --allow-empty -m "retrigger ci" && git push`. The CLA bot re-checks against the latest commit. If still failing, confirm the committer email on the commit matches the email you signed the CLA with.

---

## Q5. A reviewer asks you to split your PR. When is that appropriate?

When the PR mixes concerns. Examples that warrant splitting:

- Integration change + TIPCommon change → two PRs
- Two unrelated integrations → one PR each
- Bug fix + unrelated typo fixes → bug-fix PR first, cleanup PR after

Reason: narrow scope = faster review, easier revert, cleaner history. Splitting is normal and expected for anything non-trivial.

---

## Q6. Why is squash-merge the repo's strategy?

Clean `main` history (one commit per feature), easy revert (one commit to reverse), atomic changes (each merged change is a complete unit). Intermediate branch commits are noise — the final state is what matters.

---

## Q7. Why can't even admins bypass required status checks?

Because the repo uses GitHub's **Repository Rulesets** (not older branch protection rules), which allow zero bypass even for admins. Intentional — protects `main` from "just this once" override decay. Only way around is temporarily removing the rule in repo settings with approval.

---

## Q8. You push a fix for a failing check but it still shows red. Troubleshoot.

1. Check the check is re-running (may take 30-60 seconds to re-kick)
2. If the UI is stale, refresh
3. Inspect the latest run's logs — is it a different failure?
4. Confirm the push landed — `git log --oneline origin/<branch>` on your fork
5. Check for conflicting workflow state — maybe cache stale or a previous run hung

---

## Q9. A check is green locally but red in CI. What's probably different?

- **Env vars** — local has `.env`, CI doesn't
- **Python version skew** — local might be 3.12; CI is 3.11
- **Path differences** — absolute paths in tests
- **Network access** — local has internet, CI's test job may not
- **Caching** — local has cached `uv` deps, CI has fresh install — a missing `pyproject.toml` dep shows up only in CI
- **Timezone** — CI runs UTC, local may not

---

## Q10. What's the "Ready for Review" convention?

PRs opened as Draft signal "in progress, don't review yet." Once all checks pass and you want review, click "Ready for review". This pings maintainers. Opening a non-Draft PR with failing checks wastes reviewer time and noise.

---

## Q11. How does the internal publishing pipeline work from the contributor's perspective?

It's **opaque** — intentionally. After merge, the Content Hub release team runs a pipeline that builds zips, tags versions, and publishes to the in-product Content Hub registry. Contributors don't manage this. Their responsibility ends at merge; publishing is Google's.

---

## Q12. What happens if your integration uses a field added in a newer TIPCommon but you pinned the old one?

`mp validate` catches the `AttributeError` during the test-build phase. Workflow fails. Fix: bump TIPCommon version in `pyproject.toml` + `uv.lock` regenerated via `uv lock`. If your change needs features from multiple TIPCommon versions, you can't pin both — you must migrate.

---

## Next

→ **[Section 11: Advanced Topics](../11-advanced/index.md)**
