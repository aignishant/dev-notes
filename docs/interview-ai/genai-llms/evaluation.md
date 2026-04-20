# 📊 Evaluation & Benchmarks

> **Q86–Q100 · 15 questions** on the hardest problem in LLM development: *how do you actually know if your model is better?* Classical benchmarks, LLM-as-judge, pairwise preference, contamination, calibration, hallucination evals, reasoning evals, and the evals that actually correlate with product success.

---

## Q86. Why LLM evaluation is fundamentally hard { #q86 }

Unlike classification (where accuracy is unambiguous), LLM outputs are:
- **Open-ended**: many valid responses to "write me a poem about regret."
- **Multi-dimensional**: quality = {factuality, helpfulness, coherence, style, safety, conciseness, ...}.
- **Context-dependent**: the "right" answer depends on user intent you may not have.
- **Stochastic**: same input, different outputs at T>0.
- **Benchmark-hackable**: models are trained on internet, benchmarks leak into training data.

**The four layers of LLM evaluation:**

| Layer | What | Example metrics |
|---|---|---|
| **Capability** | Can model solve task class? | MMLU, HumanEval, GSM8K |
| **Alignment** | Does it follow instructions safely? | MT-Bench, Arena, refusal rates |
| **Product** | Does it help users? | Acceptance rate, retention, NPS |
| **Safety** | Does it avoid harms? | Red-team attack success rate |

**Rule of thumb:** *benchmarks are necessary but not sufficient.* Two models with identical MMLU can feel completely different in product. Always evaluate at the product layer before shipping.

---

## Q87. Classical benchmarks — MMLU, HumanEval, GSM8K, BIG-Bench { #q87 }

**MMLU (Massive Multitask Language Understanding):** 57 subjects, multiple choice. Tests breadth of knowledge — history, law, medicine, math. Accuracy typical range: 30% (random = 25%) → 90%+ (frontier).

**HumanEval:** 164 Python problems, functional correctness. Model writes code, runs against test cases. pass@1 (first try passes).

**MBPP:** 974 Python problems. Simpler than HumanEval.

**GSM8K:** grade-school math word problems. Tests chain-of-thought reasoning.

**MATH:** competition-level math. Much harder than GSM8K.

**BIG-Bench:** 200+ diverse tasks, many novel. Designed to resist contamination.

**HellaSwag, ARC, TruthfulQA, WinoGrande:** the "open-LLM-leaderboard" classics.

**BFCL (Berkeley Function-Calling Leaderboard):** tool/function calling evaluation.

**Major weaknesses:**

1. **Contamination**: model has seen the benchmark during training. Results are inflated.
2. **Multiple-choice bias**: models can guess well on 4-choice questions without understanding.
3. **Surface-form sensitivity**: tiny prompt wording changes swing scores ±5-10%.
4. **Not product-correlated**: Model A beats Model B on MMLU but loses in user preference tests.

**Modern replacements (contamination-resistant):**
- **LiveCodeBench**: problems scraped after a cutoff date.
- **LiveBench**: refreshed monthly with novel tasks.
- **SWE-bench**: real GitHub issues fixed in PRs.
- **MMLU-Pro**: harder, 10-option, reasoning-heavy MMLU variant.
- **GPQA**: graduate-level Q&A, Google-proof.

---

## Q88. LLM-as-judge — the double-edged sword { #q88 }

**Concept:** use a strong LLM (usually GPT-4/Claude Opus/o-series) to score outputs. The judge reads the prompt, reads the response, and returns a score or preference.

**Why it's popular:**
- Scales arbitrarily (no humans).
- Consistent (same judge = same criteria).
- Cheap relative to humans ($0.01/judgment vs $1+).
- Can explain judgments.

**Types:**

| Type | Format | Use |
|---|---|---|
| **Pointwise** | Score response 1-5 on rubric | Ranking a single model across prompts |
| **Pairwise** | A vs B, which is better? | Comparing two models (Arena-style) |
| **Reference-based** | Compare response vs gold answer | QA benchmarks with known answers |

**Validated correlation with human preference:** ~80% agreement with humans on general tasks, up to ~95% on narrow domains with good rubrics.

**Known biases to fight:**

1. **Position bias**: judge prefers option A over B regardless of content (GPT-4 ~60/40 biased to first position). **Fix**: evaluate both orders, average.
2. **Length bias**: longer responses judged better. **Fix**: explicit rubric discouraging verbosity.
3. **Style bias**: judge prefers responses that *sound* like the judge's own outputs. **Fix**: use *different* judge from the model being evaluated.
4. **Confidence bias**: judge overly trusts confident-sounding wrong answers. **Fix**: explicit "check factual claims" in rubric.
5. **Self-enhancement**: GPT-4 judging GPT-4's outputs rates them higher. **Fix**: cross-judging with other model families.

```python
# Pairwise judge template (industry standard)
prompt = f"""You are evaluating two AI responses to the same user query.
Be fair, unbiased, and specific.

User query: {query}

Response A: {response_a}
Response B: {response_b}

Rate on these criteria:
1. Accuracy (does it answer correctly?)
2. Helpfulness (does it solve the user's real need?)
3. Conciseness (is it appropriately concise?)
4. Safety (does it avoid harmful content?)

Verdict: Either "A", "B", or "Tie".
Explanation: 1-2 sentences.
"""
```

**2026 best practice:** combine LLM-judge (scale) with periodic human calibration (~5% of items) to catch drift.

---

## Q89. Chatbot Arena and pairwise preference { #q89 }

**LMSYS Chatbot Arena:** crowdsourced pairwise preference voting. Users submit prompts, see two anonymized responses, vote for preferred. Elo ratings computed from millions of votes.

**Why Arena matters:**
- **Resists contamination**: novel user prompts.
- **Product-aligned**: real users asking real things.
- **Reflects holistic quality**: tone, helpfulness, correctness all bundled.

**Weaknesses:**
- Favors **engaging style** over factual accuracy (users often can't tell when an answer is wrong).
- Biased toward **English conversational** use cases.
- Sybil attacks / gaming possible.

**Variants:**
- **Arena-Hard** (LMSYS 2024): curated hard prompts + LLM-judge, correlates well with human Arena but runs in minutes not days.
- **MT-Bench**: 80 multi-turn prompts + GPT-4 judge. Simpler alternative.
- **AlpacaEval 2**: 805 prompts vs GPT-4 baseline + length-controlled judge.

**How to read Arena:**
- Trust the *ranking*, not the exact Elo delta.
- Cross-check with task-specific benchmarks (Arena ≠ code eval ≠ math eval).
- Small models can score surprisingly high if trained well for chat (but fail at reasoning).

---

## Q90. Domain-specific evals — when generic benchmarks aren't enough { #q90 }

Generic benchmarks won't tell you if your legal-research LLM is actually good at legal research. You need **domain evals** for any vertical product.

**Design pattern for domain evals:**

1. **Collect** 100-1000 representative real queries from production.
2. **Get gold answers** from domain experts (expensive — can't skimp).
3. **Define rubrics** specific to the domain:
   - Legal: citation accuracy, correct jurisdiction, appropriate hedging.
   - Medical: differential diagnosis completeness, red-flag warnings, evidence-grade.
   - Code: functional correctness, security, style, test coverage.
   - Finance: numerical accuracy, regulatory compliance.
4. **Automate with LLM-judge** + rubric.
5. **Manual check** 5-10% for calibration.

**Examples of great domain evals:**
- **MedQA / USMLE**: medical licensing exams.
- **LegalBench**: legal reasoning tasks.
- **FinanceBench**: financial QA over filings.
- **SWE-bench / SWE-bench Verified**: real GitHub issues.

<div class="scenario" markdown>
**Scenario — new customer in healthcare:** Before any deployment, build a 500-prompt eval set from real customer queries, with rubrics co-designed with a physician. Baseline GPT-4 + your fine-tune + Claude. If no model is consistently >85% on critical-safety prompts, *don't ship*. I've seen this kill deployments that looked great on MMLU.
</div>

---

## Q91. Hallucination evaluation { #q91 }

**Hallucination** = content that sounds plausible but is factually wrong, unsupported by context, or contradicts known facts.

**Types:**

1. **Intrinsic hallucination**: contradicts the provided context (e.g., RAG chunk says "2021" but response says "2023").
2. **Extrinsic hallucination**: adds info not in context but verifiable (e.g., correct but uncited).
3. **Factual hallucination (no context)**: wrong answer to open-world questions.
4. **Extrinsic unsupported**: plausible-sounding but unverifiable or false.

**Eval methods:**

| Method | How |
|---|---|
| **SummEval-style NLI**: | Use NLI model to check if each claim is entailed by context |
| **FactScore** (Min 2023): | Decompose into atomic facts, verify each against source |
| **RAGAs faithfulness**: | Production tool for RAG hallucination |
| **LLM-judge with rubric**: | "Is this response fully supported by the context?" |
| **Consistency sampling**: | Generate N responses; disagreement = hallucination signal |

**Metrics:**
- **Faithfulness**: fraction of claims supported by context.
- **Answer relevance**: fraction of response that answers the query.
- **Context precision/recall**: retrieval quality feeding hallucination.

```python
# Using RAGAs for hallucination evaluation
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from ragas import evaluate

result = evaluate(
    dataset=eval_dataset,   # question, answer, contexts, ground_truth
    metrics=[faithfulness, answer_relevancy, context_precision],
)
# Returns scores per example + aggregate
```

**Model-level mitigations:**
- **RAG with high-precision retrieval**.
- **Chain-of-verification (CoVe)**: model checks its own claims.
- **Retrieval-augmented rewriting**: retrieve, draft, verify, revise.
- **Training**: DPO against known hallucinations (e.g., TruthfulQA DPO data).

---

## Q92. Calibration — does the model know what it doesn't know? { #q92 }

**Calibration:** when a model says "90% confident", is it actually right 90% of the time?

**Well-calibrated model:** confidence matches accuracy → ECE (Expected Calibration Error) low.
**Overconfident model:** says 90% when actually 60% — dangerous for high-stakes domains.
**Underconfident model:** says 50% when actually 95% — users lose trust.

**Sources of confidence:**
1. **Logit probabilities** at inference: $p(\text{token}) \approx$ confidence. But next-token prob ≠ answer correctness.
2. **Self-reported confidence**: "How confident are you?" Usually inflated (models trained to be helpful).
3. **Consistency across samples**: generate 10 times at T>0, measure agreement. Low agreement = low confidence. Works well.
4. **Verbalized uncertainty**: train model to output calibrated "I'm 70% sure" annotations (e.g., OpenAI's Calibrated Math).

**Post-hoc calibration:**
- **Temperature scaling**: divide logits by learned $T$, minimize NLL on val set. Simple, effective.
- **Platt scaling, isotonic regression**: more expressive.

**Evaluating calibration:**
- Plot **reliability diagram**: x = predicted confidence bin, y = empirical accuracy. Ideal = diagonal.
- Compute **ECE**: average gap between confidence and accuracy across bins.
- **Brier score**: $\mathbb{E}[(p - y)^2]$.

**2026 insight:** frontier instruction-tuned models are systematically overconfident because RLHF rewards confident-sounding responses. Calibration is an active research direction.

---

## Q93. Reasoning evaluation — GSM8K, MATH, AIME, ARC-AGI { #q93 }

**Math reasoning:**
- **GSM8K**: grade school word problems. Saturating (>95%).
- **MATH**: competition math (AMC/AIME). Frontier models ~70-90%.
- **AIME 2024/2025**: American Invitational Math Exam. Hardest widely-tested math (2026 frontier: 80-95% with reasoning-time compute).
- **Putnam**: undergrad-level. Active frontier.

**Logical/commonsense reasoning:**
- **ARC-Challenge**: grade-school science. Mostly saturated.
- **ARC-AGI** (François Chollet): abstract pattern puzzles. Designed to resist memorization. 2024 breakthrough: o3 scored 87.5% with massive test-time compute.

**Multi-step reasoning:**
- **BIG-Bench Hard**: 23 hard tasks from BIG-Bench.
- **GPQA (Diamond)**: PhD-level Q&A.

**Key 2024-2026 development — test-time reasoning:**

OpenAI's **o1/o3** series and DeepSeek **R1** showed that allocating compute to *chain-of-thought at test time* dramatically improves reasoning. This shifted evaluation norms:
- Report **pass@1 with no CoT** (raw capability).
- Report **pass@1 with CoT** (practical capability).
- Report **pass@1 with N-sample majority vote** (compute-bounded best).
- Report **compute-accuracy curves** (how much better with more thinking tokens).

**What interviewers want you to know:**
- Reasoning isn't a fixed capability — it scales with test-time compute.
- The scaling slope differs across models → "reasoning RL" training recipes matter.
- Most real products don't need o3-level reasoning. Cheaper models + RAG + tools solves 95% of cases.

---

## Q94. Red-teaming and adversarial evaluation { #q94 }

**Red-teaming:** actively attack the model to find failure modes.

**Goals:**
- Jailbreak: bypass safety training to generate harmful content.
- Prompt injection: hijack the model via user-submitted text.
- Factual manipulation: induce false outputs under adversarial framing.
- Data extraction: get model to reveal training data.
- DoS: craft inputs that maximize inference cost.

**Red-team methods:**

| Method | How | When |
|---|---|---|
| **Manual red-teaming** | Humans try to break the model | Pre-launch, for nuance |
| **Automated red-teaming** | Adversarial LLM generates attacks | CI/CD regression |
| **Template attacks** | Known jailbreak patterns (DAN, role-play) | Baseline safety check |
| **Gradient-based** (white-box) | GCG, AutoDAN — optimize adversarial suffixes | Research, open-weight models |
| **Best-of-N jailbreaking** | Sample many paraphrases, take attack success | Robust safety eval |

**Metrics:**
- **Attack Success Rate (ASR)**: % of attacks that succeed.
- **Category-specific ASR**: across CBRN (chemical/bio/radio/nuclear), cyber, misinformation, self-harm.
- **Robustness to paraphrase / encoding**: does base64-encoding the attack bypass filter?

**Standard benchmarks:**
- **HarmBench**: 400+ behavior-based attacks across 7 harm categories.
- **AdvBench**: classic 520-prompt harmful behavior set.
- **JailbreakBench**: curated jailbreak attempts.
- **WildChat**: real-world adversarial-ish conversations.

**Defense measurement:**
- False positive rate: model refuses benign requests.
- Over-refusal is a silent failure: model becomes useless for normal tasks.
- **XSTest, Or-Bench** measure over-refusal specifically.

---

## Q95. Data contamination — the silent killer of benchmarks { #q95 }

**The problem:** GPT-4 scored 90%+ on HumanEval. Was that real reasoning, or did it memorize the repo?

**Evidence of contamination:**
- Performance tanks on problem variants (change variable names, rephrase).
- Performance-date curves: new benchmarks (post-cutoff) perform *much* worse.
- Models "know" exact HumanEval solutions verbatim.

**Contamination types:**
1. **Direct contamination**: exact benchmark items in training data.
2. **Near-duplicate contamination**: blog posts discussing solutions.
3. **Solution leakage**: StackOverflow / forum posts with answers.

**Mitigations for model developers:**
- **Decontamination**: n-gram match benchmark questions against training corpus → remove. OpenAI, Anthropic, Meta all do this.
- **Perplexity filters**: compute training-time perplexity of known benchmarks; remove low-perplexity chunks.
- **Date-based**: only train on data before a cutoff, eval only on post-cutoff benchmarks.

**Mitigations for eval designers:**
- **Private / hidden benchmarks** (not on HF Hub, not on GitHub).
- **Rolling benchmarks** (LiveBench updates monthly).
- **Verified variants** (SWE-bench Verified filters out contaminated items).
- **Functional correctness** (HumanEval+ rigorous test suite).

**2026 best practice:** never trust a single number. Use a suite of benchmarks, at least one of which is contamination-resistant, at least one of which is your own private holdout.

---

## Q96. Evaluation design — the golden rules { #q96 }

**Hard-won rules from people who've shipped LLMs:**

**1. Evaluate continuously, not just at release.**
- CI/CD runs eval on every PR touching prompts, models, or retrieval.
- Regression budget: no metric can drop >2% without explicit approval.

**2. Eval set > benchmarks.**
- Curate 500+ prompts from real production traffic.
- Mix easy (sanity check) + hard (frontier) + adversarial (safety).
- Refresh quarterly.

**3. Combine metric types.**
- Automated (speed): LLM-judge, regex match, execution.
- Human (truth): panels of 3-5 raters, calibrated rubric, periodic.
- Product (impact): A/B retention, acceptance rate.

**4. Evaluate per-slice, not just aggregate.**
- Language (English vs non-English).
- User tier (free vs pro).
- Task type (Q&A vs summarization vs generation).
- Input length.

**5. Budget for eval.**
- Running a full eval on a 70B model ≈ $100-500.
- If you run 100 evals/month ≈ $10-50k/month. Budget it.

**6. Track agreement, not just scores.**
- Inter-rater agreement (humans vs humans): 60-80% is realistic.
- Judge-human agreement: 70-85%.
- If your judge disagrees with humans 40%, *your eval is meaningless.*

**7. Version your evals.**
- Which eval set ran? Which judge model? Which rubric? Git-track everything.

<div class="tip-box" markdown>
**Interview gold:** "How do you evaluate an LLM?" The bad answer lists benchmarks. The good answer walks through the 4 layers (capability → alignment → product → safety) and explains which methods fit which layer. The great answer adds the operational reality: continuous eval, slice analysis, contamination resistance, and the human-in-the-loop calibration that keeps automated judges honest.
</div>

---

## Q97. When a new open-weight model drops — how to eval in 48 hours { #q97 }

Every few weeks, a new model ships and leadership asks "should we switch?" Your job: answer in 48 hours.

**Hour 0-2: smoke tests.**
- Load via vLLM or similar. Verify inference works.
- 50-prompt sanity check: basic factual, code, math, refusals.
- Latency/throughput on your target hardware.

**Hour 2-12: standard benchmarks.**
- Run MMLU, HumanEval, GSM8K, MT-Bench, Arena-Hard subset.
- Compare to your current model on same eval harness (lm-eval-harness).

**Hour 12-36: domain eval.**
- Run your 500-prompt production eval set.
- Compare pairwise with LLM-judge.
- Check safety regressions (HarmBench subset).

**Hour 36-48: operational eval.**
- Cost per M tokens at your batch sizes.
- P95 latency.
- Prompt format compatibility (does your existing system prompt still work?).

**48-hour output: one-pager.**
- Metric comparison table (yours vs new model).
- Cost comparison at projected volume.
- Recommendation: A) switch now, B) shadow test 2 weeks, C) pass.
- Known risks and regressions.

**Common traps:**
- Don't trust the model's own blog post. Benchmarks lie.
- Watch for *format*-sensitivity: some models need different templates and fall apart without them.
- Check context length *effective* (needle-in-haystack), not marketed.

---

## Q98. Production A/B testing for LLM rollouts { #q98 }

**Hypothesis-first design:**
- "Model B will reduce regeneration rate by 10% for coding prompts."
- Not: "Model B seems better, let's try it."

**Traffic allocation:**
- Start with 1% → 5% → 25% → 100%.
- Advance only if: no critical metric regresses >2%, primary metric beats control by >MDE.

**Sample size math:**
- For 10% lift detection at 80% power, $\alpha=0.05$, you need ~2000 per arm for binary metrics.
- For Likert / continuous: use power calculators with your observed variance.

**Guardrail metrics** (must not regress):
- Refusal rate.
- Toxicity rate.
- PII leak rate.
- P99 latency.

**Run duration:**
- Need to capture weekly seasonality (min 7 days).
- But also: novelty effect — first days' data may be biased by curiosity. Discount first 48 hours.

**Sequential testing:**
- Monitor daily but *don't stop early* without proper sequential analysis (alpha spending / mSPRT). Otherwise false positives inflate.

**Failure modes:**
- Sample ratio mismatch: 50/50 split showing 48/52 → trust broken, abort.
- Heterogeneous effects: new model wins on easy prompts, loses on hard. Aggregated stats hide this.

---

## Q99. Cost-aware evaluation — don't evaluate everything equally { #q99 }

**The trap:** "let's run our full 10,000-prompt eval every day!" At $50/run, that's $18k/month.

**Tiered evaluation:**

| Tier | Prompts | Frequency | Cost/run | Purpose |
|---|---|---|---|---|
| **Tier 1: Smoke** | 50 | Every commit | $1 | Catch regressions fast |
| **Tier 2: Broad** | 500 | Every PR to prompts/model | $20 | Confidence in merge |
| **Tier 3: Full** | 10k | Weekly | $500 | Comprehensive |
| **Tier 4: Deep** | 50k+ | Before major release | $5k | Ship/no-ship call |
| **Tier 5: Human** | 200 | Monthly | $2k (labeler cost) | Calibrate auto-evals |

**Sampling smart:**
- Stratify by user segment, task type, difficulty.
- Oversample edge cases (safety, adversarial, minority languages).
- Bandits / active learning: spend eval budget on prompts where you're uncertain.

**Cache aggressively:**
- Same prompt + same model + same params = same result. Cache it.
- Rerun only when any of (model, prompt, params) changes.

---

## Q100. Evaluating reasoning and agentic behavior { #q100 }

**Reasoning evals:**
- Beyond final answer: check if intermediate steps are valid.
- **Process reward models (PRMs)**: score each step of a CoT. Trained on human-labeled step correctness (OpenAI's PRM800K).
- **Self-consistency**: sample N reasoning paths, majority vote. Better than single-sample for math/logic.

**Agentic evals (tool-using, multi-turn):**

| Benchmark | What it tests |
|---|---|
| **AgentBench** | Multi-turn tool use across environments |
| **τ-bench** | Long-horizon customer service conversations |
| **WebArena / VisualWebArena** | Web browsing agents |
| **SWE-bench / SWE-bench Verified** | Autonomous code fix agents |
| **MLE-bench** | Kaggle-style ML engineering tasks |
| **GAIA** | General assistant benchmark |

**Multi-turn complications:**
- Success ≠ per-turn quality. Final state matters.
- Path efficiency: 3 tool calls vs 30 to solve same task.
- Error recovery: did agent recognize and recover from a failure?
- Hallucinated tool calls: agent makes up APIs that don't exist.

**Metrics:**
- **Task success rate** (did it solve it?).
- **Efficiency**: # steps, # tool calls, total tokens.
- **Faithfulness**: did the agent stay grounded in tool outputs?
- **Cost per successful task**.

**2026 reality check:** benchmarks saturate fast. τ-bench went from 30% to 70%+ in under a year. But real customer service agents still fail routinely — benchmarks measure narrow competence, not robustness. **Always eval on your actual product's tasks.**

---

## ✅ Module Recap

- **LLM evaluation is 4-layer**: capability → alignment → product → safety. Never conflate them.
- **Classical benchmarks are leaky** — use LiveBench, SWE-bench Verified, GPQA, or private evals.
- **LLM-as-judge** is the scalable workhorse but has position/length/style biases. Fight them with paired eval and cross-model judges.
- **Chatbot Arena / MT-Bench / Arena-Hard** are the best open alignment evals.
- **Hallucination evaluation** needs RAGAs-style faithfulness + consistency sampling.
- **Reasoning evals** are test-time-compute-dependent — report curves, not single numbers.
- **Red-teaming + safety evals** are non-negotiable before production.
- **Contamination is the silent killer** — rotate evals, use private holdouts.
- **Design evals as a system**: tiered, cached, versioned, slice-analyzed, continuously run.

→ Next: [🛡️ Safety, Hallucinations & Guardrails](safety.md)
