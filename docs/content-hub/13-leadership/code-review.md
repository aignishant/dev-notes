# Code Review Standards

Code review is **the** lever for code quality at scale. As a lead, you own the bar.

## What "Good Review" Looks Like

A good review:

- **Happens fast** — first response within 1 business day
- **Is specific** — line-level comments, not vague "LGTM with nits"
- **Is kind** — critical of code, not of person
- **Teaches** — explain the "why," not just the "what"
- **Distinguishes blocking from suggesting** — prefix nitpicks with "nit:"
- **Runs the code** — at least for non-trivial changes, check out the branch and test
- **Catches patterns** — if you see the same bug in two PRs, write it down in the standards

## The Content Hub's Implicit Review Bar

For integration PRs:

- Lint + type-check green (automated)
- Tests added/updated (human check — did they actually test the change?)
- `release_notes.yaml` version bumped appropriately
- No password in logs (`print_value=True` on password → block)
- Ontology mapping present if connector added
- No secrets committed
- Error handling is specific (not bare `except Exception`)
- Entity iteration handles partial failures (four-bucket pattern)
- Type hints present and correct

For TIPCommon / `mp` / `packages/` PRs — **stricter**:

- Zero regressions on existing integrations (run harness)
- Unit tests for new helpers
- Documentation updated
- API stability considered (don't break signatures across minor versions)
- Lead approval required

## The Comment Taxonomy

Standardize your comments with prefixes — saves confusion.

| Prefix | Meaning |
|---|---|
| **nit:** | Stylistic or minor — author can ignore if they disagree |
| **suggestion:** | Recommendation — consider, don't have to act |
| **question:** | Genuinely curious — author should answer |
| **blocking:** or no prefix | Must address before merge |
| **fyi:** | Informational, no action needed |
| **praise:** | Positive callout — reinforce good work |

Consistent vocabulary means reviewers agree on what's mergeable.

## Things to Catch in Review

Real patterns from real repos:

### Security

- API key or token as `type: string` instead of `password`
- `print_value=True` on password parameter
- Hardcoded credentials in test files
- `verify=False` SSL defaults
- Logging full HTTP request bodies
- Storing plaintext secrets in context

### Correctness

- `siemplify.end()` called in the wrong branch → platform sees INPROGRESS forever
- Connector without `ontology_mapping.yaml`
- Missing `start_time`/`end_time` in ontology
- Processed-IDs cache not capped
- No idempotency key in bidirectional sync jobs
- Entity iteration uses `break` on first failure instead of four-bucket pattern

### Robustness

- Bare `except:` or `except Exception:` without re-raise
- Retry without jitter
- No timeout on `requests` calls (defaults to no timeout)
- Assumed response shape without validation
- Infinite loops in pagination

### Quality

- Missing type hints
- Wrong docstring style (not Google)
- Test names that don't describe the test
- Duplicated code that should be in `core/`
- Hardcoded values that should be params
- `name` vs `identifier` confusion

### Process

- Version not bumped in `release_notes.yaml`
- PR scope too broad (multiple unrelated changes)
- Changes to `definition.yaml.identifier` (immutable!)
- Renamed action without deprecation path
- Missing tests for new functionality

## Review Workflow

1. **Claim the review** — assign yourself within the SLA
2. **Read the PR description first** — if it's empty, ask for context
3. **Scan the diff high-level** — get a sense of scope
4. **Run validate + tests locally** — for non-trivial changes
5. **Line-by-line on critical paths** — auth, error handling, state management
6. **Leave comments with prefixes**
7. **Submit review** — approve / request changes / comment
8. **On response: re-review only the changed areas** — don't re-litigate

## Handling Disagreements

> *"Author disagrees with your feedback. What do you do?"*

1. **Re-read their response** — you might be wrong
2. **Engage the argument** — "My concern was X; you addressed by doing Y — but I still think Z because..."
3. **If still stuck, invite a third reviewer** — not to gang up, to triangulate
4. **If genuinely stylistic**, author wins — your job isn't to make every PR match your taste
5. **If genuinely a quality issue**, escalate calmly — "I think this is blocking; if we disagree, let's take it to lead"

Never passive-aggressive approve. Either block firmly or let it land.

## Review Ratios — Red Flags

| Ratio | What it means |
|---|---|
| Your reviews / your PRs >> 5 | You're the bottleneck; train others |
| Your reviews / your PRs << 0.5 | You're not carrying your review weight |
| Most of your reviews are "LGTM" no comments | You're rubber-stamping — look harder |
| Most of your reviews request changes | Maybe PR authors need more context earlier |

## Lead-Level Meta-Review

Periodically (monthly), the lead looks at:

- Are SLAs being met?
- Are the same bugs recurring? → update the contribution guide
- Are reviews constructive or toxic? → coaching conversation
- Is review load well-distributed?

## Example Review Comments

### Good

> *"blocking: `extract_action_param(..., print_value=True)` on a password parameter will log the secret. Please set `print_value=False`."*

> *"suggestion: Consider pulling this retry logic into `core/client.py` — it's duplicated in three actions already. Happy to pair on refactor if helpful."*

> *"nit: `result_value = "True"` should be lowercase `"true"` to match the rest of the codebase."*

> *"question: What happens if the third-party returns 200 with an empty `items` array? I think the current code would raise KeyError on `items[0]`. Worth a test?"*

### Bad

> *"This is wrong."*

> *"I'd do it differently."*

> *"This code is bad."*

> *"lgtm"* — on a 500-line PR touching security-critical code.

## Next

→ **[Mentoring Juniors](mentoring.md)**
