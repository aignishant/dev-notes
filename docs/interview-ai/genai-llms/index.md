# GenAI & LLMs Interview Mastery 🧬

<div class="hero" markdown>
# The complete playbook for landing LLM-focused roles
### 115+ deeply-explained questions · Production-grade code · 3 mock interviews

*From tokenizers and embeddings to RLHF, vLLM serving, and the 2026 LLM stack — everything a senior GenAI engineer should know to walk confidently into an interview at any top AI lab, frontier model company, or LLM-powered startup.*
</div>

---

<div class="stats-grid" markdown>

<div class="stat-card" markdown>
**115+**
Conceptual & scenario questions
</div>

<div class="stat-card" markdown>
**6 modules**
Foundations → Safety
</div>

<div class="stat-card" markdown>
**80+**
Python / PyTorch / Transformers snippets
</div>

<div class="stat-card" markdown>
**3 mock rounds**
Phone screen · deep dive · system design
</div>

</div>

---

## 🗺 Module map

- 🧬 **[LLM Foundations](foundations.md)** (Q1–Q20) — architecture, tokenization (BPE/WordPiece/SentencePiece), embeddings, scaling laws, emergent abilities, context windows, memory and compute costs
- ✍️ **[Prompting & In-Context Learning](prompting.md)** (Q21–Q40) — zero/few-shot, chain-of-thought, self-consistency, tree-of-thoughts, ReAct, function calling, structured output, prompt injection
- 🎯 **[Fine-tuning & Alignment](fine-tuning.md)** (Q41–Q60) — SFT, RLHF (PPO), DPO, Constitutional AI, LoRA/QLoRA, PEFT, instruction tuning, multi-task learning
- ⚡ **[Inference & Deployment](inference.md)** (Q61–Q85) — KV cache, paged attention, continuous batching, vLLM/TGI/TensorRT-LLM, quantization (GPTQ/AWQ/FP8), speculative decoding, serving at scale
- 📊 **[Evaluation & Benchmarks](evaluation.md)** (Q86–Q100) — MMLU, HumanEval, MT-Bench, Chatbot Arena, LLM-as-judge, contamination, reasoning benchmarks, red-teaming
- 🛡️ **[Safety, Hallucinations & Guardrails](safety.md)** (Q101–Q115) — hallucination types & mitigation, jailbreaks, prompt injection defenses, PII, agent safety, watermarking, regulation
- 🎤 **[Mock Interviews](mock-interview.md)** — 45/60/75-min interviews with full rubrics
- 📋 **[Rapid Revision](rapid-revision.md)** — night-before cheat sheet

---

## 🧠 Three-pass study method

1. **Skim pass** (3–4 hours) — read every Q&A header. Don't go deep. Draw a mental map.
2. **Deep pass** (2–3 weeks, 1 hr/day) — work every question. Explain the answer out loud before reading it.
3. **Code pass** (1 week) — open your editor. Reproduce every code snippet from scratch. Break it. Fix it.

Night before: read **Rapid Revision** only. Sleep 8 hours.

---

## 🎯 What makes a senior-level GenAI answer

A staff+ engineer doesn't just recite definitions. They:

1. **Start with the constraint:** *"Before picking an architecture, what's the latency budget and context length?"*
2. **Name the trade-off:** *"Full fine-tuning gives more quality; LoRA saves 100× memory. Pick based on your target metric."*
3. **Quantify:** *"For a 70B model in BF16, KV cache for 32k context is ~10GB per request — this dominates serving cost."*
4. **Know the 2026 frontier:** DPO over PPO for simple alignment, Mamba/SSM for ultra-long context, flash attention 3, speculative decoding, JSON mode/structured output.
5. **Admit uncertainty gracefully:** *"I'd want to ablate that before committing — my prior is X, but the literature is mixed."*

---

## 🚀 Who this site is for

- **GenAI engineers** at any level preparing for roles at Anthropic, OpenAI, Google DeepMind, Meta AI, or well-funded LLM startups.
- **ML engineers transitioning** from classical ML to LLM-first roles.
- **Staff/Principal candidates** who need to review both research depth (alignment theory, scaling laws) *and* production infra (vLLM, KV cache optimization, quantization pipelines).
- **PhD students** entering industry who want a pragmatic translation of research into engineering decisions.

---

<div class="tip-box" markdown>
**One last tip:** interviewers at top AI labs don't want you to *memorize* the answers in this doc — they want to see you *think*. Use these Q&A as scaffolding for your own intuition. When you can critique each answer (find one thing I got slightly wrong; disagree with a trade-off I made), you've internalized it.
</div>

→ Start: [🧬 LLM Foundations](foundations.md)
