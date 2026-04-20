# Deep Learning — Interview Mastery

<div class="hero" markdown>
<h1>The Deep Learning Interview Bible</h1>
<p>115+ ruthlessly-answered questions covering every layer of modern deep learning — from the math of backprop to serving production transformers. Each answer carries the depth, intuition, and trade-off language that senior engineers expect in 2026.</p>
</div>

<div class="stats-grid" markdown>
<div class="stat-card" markdown>
**115+**<br>Interview questions
</div>
<div class="stat-card" markdown>
**6**<br>Core knowledge modules
</div>
<div class="stat-card" markdown>
**70+**<br>PyTorch code snippets
</div>
<div class="stat-card" markdown>
**3**<br>Full mock rounds
</div>
</div>

## What makes this different

Most deep learning prep materials stop at "here's a CNN". This one goes through the **why** at every step — why residual connections changed everything, why layer norm beat batch norm for transformers, why Adam is not always best, why knowledge distillation works, why positional encoding has to be added, not concatenated.

Every question covers:

- **Precise definition / derivation** (the math behind the scenes)
- **Geometric or gradient intuition** (what's actually happening inside)
- **Comparison table** (when faced with similar choices)
- **PyTorch code** (production-standard implementation)
- **Scenario** or **interviewer tip** (what makes candidates stand out)

## Module map

| # | Module | Focus |
|---|---|---|
| 🧱 | [Foundations](foundations.md) | Perceptron → backprop → activations → initialization → loss functions |
| 👁️ | [CNNs & Vision](cnns.md) | Convolutions, pooling, AlexNet → ResNet → EfficientNet → ViT |
| 🔁 | [RNNs & Sequences](rnns.md) | RNN, LSTM, GRU, vanishing gradients, seq2seq, attention precursor |
| 🎯 | [Transformers & Attention](transformers.md) | Self-attention, positional encoding, BERT, GPT, T5, ViT, Flash Attention |
| ⚙️ | [Optimization & Training](optimization.md) | SGD, Adam, schedules, mixed precision, gradient clipping, LR warmup |
| 🛡️ | [Regularization & Normalization](regularization.md) | Dropout, BN/LN/GN, weight decay, augmentation, early stopping, label smoothing |
| 🎤 | [Mock Interviews](mock-interview.md) | Phone screen + 60-min deep dive + 75-min system design |
| 📋 | [Rapid Revision](rapid-revision.md) | Cheat sheet, formulas, phrases that earn points |

## Study approach

**Three-pass method** over 3 weeks:

| Pass | Goal | Time |
|---|---|---|
| **Pass 1** — skim | See every question, absorb the structure | 6–8 hours |
| **Pass 2** — answer aloud | Force yourself to articulate before peeking | 10–12 hours |
| **Pass 3** — drill | Focus on weak areas + mock rounds with timer | 6–8 hours |

Treat each **scenario box** as a 2-minute answer and practice verbally. Interviews aren't about what you know — they're about what you can **explain under pressure**.

## The senior-level answer framework

For every deep learning question you face, frame the response in this order:

1. **The concept in one crisp sentence** — definition, not meandering setup.
2. **The math or gradient flow that makes it work** — one step of derivation or a diagram.
3. **Why it was invented** — what problem it solved, what came before.
4. **When it fails or is the wrong choice** — the trade-off.
5. **What you'd actually use today** — modern context (2026).

Candidates who hit all five bullets in ~2 minutes read as "senior". Those who get stuck on bullet 1 read as "junior".

## A final word on depth

Deep learning has a surface — you can recite "ReLU, convolution, Adam" with 20 hours of prep. And it has a core — you can derive backprop, explain why residual networks converge, and debug a NaN loss in 2 minutes. The core is what separates the $120k offer from the $300k offer.

This site is written for the core.

→ Start with: [🧱 Foundations](foundations.md)
