# Mentoring Juniors

## Why Mentoring Is a Lead Deliverable

Your code output is bounded by your hours. Your team's output is bounded by how good your team is. **The highest leverage activity a lead has is making other engineers better.**

Interviewers look for this. "What's your most recent significant impact?" — if your answer is always your own code, you're not demonstrating lead behavior.

## Onboarding a New Hire — 30/60/90

### Days 1-30

- **Environment set up** end of week 1 (`mp`, uv, IDE, dev SOAR access)
- **Read-along** with senior pairing — walk through a live PR review, a production debug
- **First PR** — small, real work, merged before day 14
- Weekly 1:1s focused on what's confusing, not what's done

### Days 31-60

- Solo work with review-layer safety net
- Pick up on-call shadow shifts (not primary)
- Owns one small integration's maintenance
- Starting to review PRs (light — catches easy stuff)

### Days 61-90

- Ships a new small integration end-to-end
- Primary on-call with senior backup
- Regular PR reviewer; comments visibly improving quality
- Can lead a scoped technical discussion in standup

If the new hire is here at 90 days, they're on track. If not, intervene — don't wait for month 6.

## The Mentoring Interaction Model

Four modes, picked per situation:

| Mode | When | What you do |
|---|---|---|
| **Teach** | They don't know the domain yet | Explain the "why" + the "what" + walk examples |
| **Guide** | They know enough to try | Ask leading questions; let them solve |
| **Coach** | They know how but hesitant | Remove blockers; transfer confidence |
| **Sponsor** | They're good, need visibility | Assign stretch work, champion them publicly |

Most leads over-teach and under-sponsor. Watch for it in yourself.

## Common Anti-Patterns

| Anti-pattern | Why it fails |
|---|---|
| Solve it for them in the PR | They learn you'll fix their mistakes |
| "Why didn't you X?" (rhetorical) | Shames; closes the conversation |
| Never paired on real code | Learning only via PR comments = slow |
| Only review, never mentor | Transactional; no trust |
| Everyone reports equally | Juniors need more attention than seniors |

## The 1:1 That Actually Works

30 min weekly, their agenda not yours:

- **What's on your mind?** (Their topic, always first)
- **What's blocking you?** (You remove blockers; don't solve)
- **What did you learn this week?** (Reinforces learning loop)
- **What can I do for you?** (Invites asks; builds trust)
- **Career arc check-in** — once a quarter

Never: "Can you update me on X project?" — that's a status meeting, not a 1:1.

## Signals You're Mentoring Well

- Their PRs get faster, smaller, higher quality over time
- They start catching issues in others' PRs
- They ask more-specific questions over time ("should I use async here?" → not "how does this whole thing work?")
- They take on stretch work voluntarily
- They start mentoring newer people

## Signals You're Mentoring Poorly

- They ghost 1:1s
- They rewrite your feedback word-for-word without understanding
- You keep fixing the same bug across their PRs
- They avoid asking you questions
- They leave

## Mentoring Across Skill Levels

### Junior → Mid

Focus: autonomy + quality. They need to stop asking permission for small choices. Techniques:

- "I'm going to stop answering that — what do *you* think?"
- Pair on code review: they review first, you review their review
- Assign ownership of a slice they can run end-to-end

### Mid → Senior

Focus: scope + impact + judgment. They need to stop asking "what to build" and start proposing. Techniques:

- Delegate a project with outcome, not spec
- Encourage cross-team work (platform team, partner integrations)
- Invite them to write the RFC, not just implement it

### Senior → Lead

Focus: team-level thinking. They stop measuring impact by their own code and start measuring by team output. Techniques:

- Delegate on-call rotation ownership
- They run a sprint planning
- They review someone's promo packet — forces them to think about career growth, not just technical work

## The Most Important Question

> *"What are you afraid to ask?"*

Juniors filter themselves constantly. This question breaks the filter. Run it in a 1:1 once a quarter; prepare to act on the answer.

## STAR Material You Can Draw From

For behavioral questions, mentoring stories make excellent answers. Have 2-3 ready:

- "Tell me about a time you helped someone develop" → mentoring arc
- "Tell me about giving difficult feedback" → PR review standoff
- "Tell me about someone you hired who didn't work out" → honest story about sub-par performance management
- "Tell me about a time you empowered someone" → delegation story

See **[STAR Stories Bank](star-stories.md)** for pre-drafted examples.

## Next

→ **[Handling Incidents](incidents.md)**
