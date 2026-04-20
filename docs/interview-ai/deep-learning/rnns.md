# 🔁 RNNs & Sequences

!!! abstract "Module Scope"
    Sequential networks — RNN, LSTM, GRU, BPTT, vanishing/exploding gradients, seq2seq with attention. Questions **Q41–Q55**. Although transformers have largely eclipsed RNNs for NLP, interviews still test RNN fundamentals because they teach the core lessons (gradient flow, gating) that transformers built on.

---

## Q41. The vanilla RNN — forward pass, backprop through time, and why it fails { #q41 }

<span class="q-badge">Foundational</span>

**Vanilla RNN cell** at time $t$:

$$\mathbf{h}_t = \tanh(W_{hh} \mathbf{h}_{t-1} + W_{xh} \mathbf{x}_t + \mathbf{b})$$
$$\hat{\mathbf{y}}_t = W_{hy} \mathbf{h}_t$$

Same weights $W_{hh}, W_{xh}, W_{hy}$ shared across all time steps — this is parameter sharing over time.

**Backpropagation through time (BPTT)**: unroll the network over $T$ time steps, then apply standard backprop to the unrolled graph.

**Gradient through time**:

$$\frac{\partial L}{\partial \mathbf{h}_k} = \sum_{t \geq k} \frac{\partial L_t}{\partial \mathbf{h}_k}$$

Following the chain rule through $t - k$ applications of the recurrent weight:

$$\frac{\partial \mathbf{h}_t}{\partial \mathbf{h}_k} = \prod_{i=k+1}^{t} \text{diag}(\tanh'(\cdot)) \cdot W_{hh}^T$$

**The vanishing / exploding gradient problem** (Bengio et al., 1994):

- Product of $t - k$ matrices. If the largest singular value of $W_{hh}$ is $\lambda$:
  - $\lambda < 1$: gradient shrinks like $\lambda^{t-k}$ → **vanishes** for large $t - k$.
  - $\lambda > 1$: gradient grows like $\lambda^{t-k}$ → **explodes**.
- Both cases make long-range dependencies impossible to learn — the learning signal from far-past time steps either disappears or overwhelms.

**Partial remedies**:

1. **Gradient clipping** ($\|\nabla\|_2$ capped at some value) → handles exploding gradient.
2. **Orthogonal / identity initialization of $W_{hh}$** → keeps singular values near 1 at start.
3. **Truncated BPTT** — limit gradient flow to $k$ steps back → bounds memory/compute but also cuts long-range learning.
4. **Better architecture** — LSTM and GRU *structurally* fix vanishing gradient. This is the real solution.

```python
import torch
import torch.nn as nn

class VanillaRNN(nn.Module):
    def __init__(self, in_dim, hidden_dim):
        super().__init__()
        self.W_xh = nn.Linear(in_dim, hidden_dim)
        self.W_hh = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.hidden_dim = hidden_dim

    def forward(self, x):  # x: (B, T, in_dim)
        B, T, _ = x.shape
        h = torch.zeros(B, self.hidden_dim, device=x.device)
        outputs = []
        for t in range(T):
            h = torch.tanh(self.W_xh(x[:, t]) + self.W_hh(h))
            outputs.append(h)
        return torch.stack(outputs, dim=1)  # (B, T, H)
```

<div class="tip-box" markdown>
**Interviewer follow-up:** "Why does LSTM solve this?" The additive cell-state update ($c_t = f_t \odot c_{t-1} + i_t \odot \tilde c_t$) creates a gradient highway: if $f_t \approx 1$, gradient flows through many time steps unattenuated. Compare to vanilla RNN's multiplicative updates.
</div>

---

## Q42. LSTM — derivation and why gates fix the gradient problem { #q42 }

<span class="q-badge">Foundational • Must Know</span>

**LSTM** (Hochreiter & Schmidhuber, 1997) adds a **cell state** $\mathbf{c}_t$ with gated updates.

**The four gates** (each a sigmoid-of-linear of $[\mathbf{x}_t, \mathbf{h}_{t-1}]$):

$$\mathbf{f}_t = \sigma(W_f [\mathbf{x}_t, \mathbf{h}_{t-1}])  \quad \text{forget: how much of old cell to keep}$$
$$\mathbf{i}_t = \sigma(W_i [\mathbf{x}_t, \mathbf{h}_{t-1}])  \quad \text{input: how much of candidate to admit}$$
$$\mathbf{o}_t = \sigma(W_o [\mathbf{x}_t, \mathbf{h}_{t-1}])  \quad \text{output: what to expose as hidden}$$
$$\tilde{\mathbf{c}}_t = \tanh(W_c [\mathbf{x}_t, \mathbf{h}_{t-1}])  \quad \text{candidate content}$$

**Cell state update** (the key trick):

$$\mathbf{c}_t = \mathbf{f}_t \odot \mathbf{c}_{t-1} + \mathbf{i}_t \odot \tilde{\mathbf{c}}_t$$

**Hidden state**:

$$\mathbf{h}_t = \mathbf{o}_t \odot \tanh(\mathbf{c}_t)$$

**Why this fixes vanishing gradient**:

The cell state update is **additive**, not multiplicative. If the forget gate $\mathbf{f}_t \approx 1$:

$$\frac{\partial \mathbf{c}_t}{\partial \mathbf{c}_{t-1}} = \mathbf{f}_t \approx 1$$

Gradient flows through many time steps without exponential decay — the "**constant error carousel**" at the heart of Hochreiter's original paper.

**Practical tips**:

- **Initialize forget-gate bias positive** (e.g., 1) → starts the network "remembering" → easier to learn long dependencies from scratch.
- Don't stack more than 2–3 LSTM layers — returns diminish, gradients still have some issues.
- **Layer normalization** inside LSTM cells (LayerNorm-LSTM) helps with training stability.

```python
import torch.nn as nn

rnn = nn.LSTM(
    input_size=128,
    hidden_size=256,
    num_layers=2,
    batch_first=True,
    dropout=0.3,     # dropout between layers (not within single layer)
)
x = torch.randn(32, 100, 128)  # (batch, seq, features)
h, (hn, cn) = rnn(x)
# h: (32, 100, 256)  — all hidden states
# hn: (2, 32, 256)   — final hidden per layer
# cn: (2, 32, 256)   — final cell per layer
```

<div class="tip-box" markdown>
**Interviewer exercise:** "Why four gates specifically?" Forget, input, output, and candidate are the minimum to independently control memory erase, memory write, output exposure, and content — all with separate learned controllers. Fewer gates (GRU has three: combined forget-input) is a valid compromise. More gates adds capacity but marginal returns.
</div>

---

## Q43. GRU vs LSTM — when to pick which { #q43 }

<span class="q-badge">Comparison</span>

**GRU** (Gated Recurrent Unit, Cho et al., 2014) simplifies LSTM to two gates:

$$\mathbf{z}_t = \sigma(W_z [\mathbf{x}_t, \mathbf{h}_{t-1}])  \quad \text{update gate (combined forget + input)}$$
$$\mathbf{r}_t = \sigma(W_r [\mathbf{x}_t, \mathbf{h}_{t-1}])  \quad \text{reset gate}$$
$$\tilde{\mathbf{h}}_t = \tanh(W_h [\mathbf{x}_t, \mathbf{r}_t \odot \mathbf{h}_{t-1}])$$
$$\mathbf{h}_t = (1 - \mathbf{z}_t) \odot \mathbf{h}_{t-1} + \mathbf{z}_t \odot \tilde{\mathbf{h}}_t$$

No separate cell state — just hidden state. Update gate $\mathbf{z}_t$ interpolates between old and new hidden.

| Axis | LSTM | GRU |
|---|---|---|
| # gates | 3 (forget, input, output) | 2 (update, reset) |
| # states | 2 ($h$ and $c$) | 1 ($h$) |
| Parameters | ~4× $d_h \cdot (d_x + d_h)$ | ~3× $d_h \cdot (d_x + d_h)$ |
| Training speed | Slower | ~30% faster |
| Expressivity | Strictly more | Less, but often equivalent in practice |
| Typical accuracy | Slight edge on long / complex sequences | Comparable |

**Empirical result (Chung et al., 2014; Greff et al., 2017)**: no consistent winner across tasks. GRU is faster and uses less memory; LSTM is more expressive and has more explicit memory control. Benchmark both on your task if it matters.

**Rules of thumb**:

- **Language modeling (moderate sequence length)**: often GRU wins on speed without accuracy loss.
- **Very long-range dependencies**: LSTM's explicit cell state helps (though Transformer beats both).
- **Embedded / resource-constrained**: GRU for fewer parameters.

```python
# Drop-in replacement
rnn_lstm = nn.LSTM(input_size=128, hidden_size=256, batch_first=True)
rnn_gru  = nn.GRU( input_size=128, hidden_size=256, batch_first=True)
```

<div class="tip-box" markdown>
**Honest answer:** In 2026, you rarely pick between LSTM and GRU for NLP — you pick a Transformer. The LSTM vs GRU question is mostly for time-series forecasting, online sequential models, and legacy NLP systems where a compact recurrent model is preferred over attention.
</div>

---

## Q44. Bidirectional RNNs — when they help, when they don't { #q44 }

<span class="q-badge">Applied</span>

A **bidirectional RNN (BiRNN)** runs two RNNs — one forward, one backward — and concatenates (or sums) the hidden states at each time step:

$$\overrightarrow{\mathbf{h}}_t = \text{RNN}_{\text{fwd}}(\mathbf{x}_t, \overrightarrow{\mathbf{h}}_{t-1})$$
$$\overleftarrow{\mathbf{h}}_t = \text{RNN}_{\text{bwd}}(\mathbf{x}_t, \overleftarrow{\mathbf{h}}_{t+1})$$
$$\mathbf{h}_t = [\overrightarrow{\mathbf{h}}_t; \overleftarrow{\mathbf{h}}_t]$$

**Each hidden state now uses context from both past and future.**

**When BiRNN helps**:

- **NER, POS tagging**: labeling each token benefits from both left and right context.
- **Audio recognition**: phonemes depend on surrounding phonemes.
- **Parsing, reading comprehension**: word meaning depends on full sentence.

**When BiRNN is wrong**:

- **Language modeling / text generation**: generating the next token can't see future tokens. Using BiRNN is cheating (data leakage — you condition on the very thing you're predicting).
- **Streaming / real-time inference**: can't run backward RNN without the full sequence.
- **Autoregressive settings** in general.

**BERT-style (bidirectional Transformer) inherits this principle**: it's fine for classification and tagging, wrong for generation (hence GPT uses causal masking instead).

```python
rnn = nn.LSTM(
    input_size=128, hidden_size=256, num_layers=2,
    bidirectional=True, batch_first=True
)
# Output h: (B, T, 2 * hidden_size) — concatenation of fwd and bwd
```

<div class="tip-box" markdown>
**Interviewer gotcha:** Using a BiRNN for language modeling is a subtle but catastrophic bug — the model can trivially "memorize" by looking at its own output. Always check: is my task generative/causal, or discriminative with full-sequence access?
</div>

---

## Q45. Sequence-to-sequence models — encoder-decoder, attention, and limitations { #q45 }

<span class="q-badge">Foundational</span>

**Seq2seq** (Sutskever et al., 2014) — encoder-decoder RNN for variable-length input → variable-length output:

1. **Encoder** reads the input sequence, produces a final hidden state $\mathbf{h}_T$.
2. **Decoder** initializes from $\mathbf{h}_T$ and autoregressively generates output tokens.

**The bottleneck problem**: compressing an arbitrarily long input into a single $\mathbf{h}_T$ vector destroys information. Translation quality collapses for inputs > ~20 tokens.

**Attention (Bahdanau et al., 2015) — the fix**:

At each decoding step $t$, compute an alignment score between decoder's current state $\mathbf{s}_t$ and each encoder hidden state $\mathbf{h}_i$:

$$e_{t,i} = \text{score}(\mathbf{s}_t, \mathbf{h}_i)$$

Softmax over time:
$$\alpha_{t,i} = \frac{\exp(e_{t,i})}{\sum_j \exp(e_{t,j})}$$

**Context vector** — weighted sum of encoder states:
$$\mathbf{c}_t = \sum_i \alpha_{t,i} \mathbf{h}_i$$

Decoder uses $[\mathbf{s}_t; \mathbf{c}_t]$ to predict next token.

**Scoring functions**:

- **Additive (Bahdanau)**: $\text{score}(s, h) = \mathbf{v}^T \tanh(W_s s + W_h h)$
- **Multiplicative (Luong)**: $\text{score}(s, h) = s^T W h$
- **Scaled dot-product** (used in Transformers): $\text{score}(s, h) = (s \cdot h) / \sqrt{d}$

**Why attention was a revolution**:

1. **Removes bottleneck** — decoder directly looks at relevant encoder positions.
2. **Interpretable** — $\alpha_{t,i}$ shows what input token the model focused on.
3. **Enables variable-length input** — no fixed-size summary.

**Transformer (2017) pushed attention to its logical conclusion**: remove the RNN entirely, use only attention.

<div class="scenario" markdown>
**Scenario:** Building a summarization model.<br>
**Answer:** Don't reach for seq2seq RNN in 2026. Use an encoder-decoder **Transformer** — BART, T5, or similar. If fine-tuning is too heavy, prompt a pretrained LLM. Seq2seq RNN knowledge is conceptually important (shows you understand the attention motivation) but almost never the right production choice.
</div>

---

## Q46. Teacher forcing and exposure bias { #q46 }

<span class="q-badge">Training Practical</span>

**Teacher forcing**: during training of autoregressive seq2seq, feed the **ground-truth** previous token to the decoder (not its own prediction).

```
Target:   "the cat sat on the mat"
Decoder: <start> → "the" → "cat" → "sat" → ...
At step 3, decoder sees ground-truth "cat", not its own prediction.
```

**Why**:

1. **Stabilizes training** — without teacher forcing, early bad predictions compound, loss explodes.
2. **Enables parallelization** — all decoder positions can be computed in parallel (with masking).

**Exposure bias** (the downside): at inference, the decoder must feed its own predictions. The distribution of inputs it sees at inference differs from training → compounding errors.

**Mitigations**:

1. **Scheduled sampling** (Bengio et al., 2015): randomly mix ground-truth and predicted tokens during training, with increasing predicted-token probability over time. Mixed results empirically.
2. **Professor forcing**: adversarially match the distributions of teacher-forced and free-running hidden states. Complex, rarely used.
3. **Reinforcement learning fine-tuning**: optimize a sequence-level reward (BLEU, ROUGE) with REINFORCE or policy gradient. Used in NMT (e.g., SeqGAN, MIXER) and now for LLMs via RLHF.
4. **Minimum risk training**: sample sequences, weight by reward. Related to RL.

**In modern LLMs (2026)**: teacher forcing is used in pretraining, then **RLHF / DPO** fine-tuning addresses exposure bias implicitly by training on model's own samples with preference signals.

```python
# Teacher forcing (classic seq2seq training)
for t in range(seq_len):
    output = decoder(input=target[:, t-1], hidden=hidden)
    loss += criterion(output, target[:, t])

# Free-running inference
for t in range(max_len):
    output = decoder(input=output.argmax(-1), hidden=hidden)
```

<div class="tip-box" markdown>
**Interviewer angle:** Exposure bias is a nice way to motivate RLHF. If asked "why RLHF vs just more next-token training?" — because the latter reinforces exposure bias; RLHF optimizes what actually matters (human preferences on generated outputs).
</div>

---

## Q47. Beam search — derivation and tradeoffs { #q47 }

<span class="q-badge">Inference</span>

**Greedy decoding**: at each step, pick argmax. Fast but myopic — one bad early choice can lock you into a bad sequence.

**Beam search** keeps $K$ (beam width) candidates at each step:

1. Start with a single sequence: `<start>`.
2. At each step, expand each beam into $|V|$ candidates (one per vocab token).
3. Keep the top $K$ candidates by cumulative log-prob across all expansions.
4. Stop when EOS is generated or max length reached.

**Length normalization** (Wu et al., 2016): raw cumulative log-prob favors short sequences (each step adds a negative number). Normalize by length:

$$\text{score}(y) = \frac{\log P(y | x)}{|y|^\alpha}$$

with $\alpha \in [0.6, 1.0]$ typical.

**Coverage penalty** (for translation) — discourage attending to the same source tokens repeatedly.

**Tradeoffs**:

| Beam width | Effect |
|---|---|
| 1 | Greedy decoding, fast, myopic |
| 4–10 | Sweet spot for translation |
| 50+ | Diminishing returns, can worsen (repetition) |

**Beam search fails at creativity** — for open-ended generation (stories, poetry), beam search produces bland, repetitive text because high-probability ≠ interesting. This is why LLM inference uses:

- **Temperature sampling**: scale logits by $T$.
- **Top-k sampling**: restrict to top-k tokens, renormalize.
- **Top-p (nucleus) sampling**: restrict to smallest set of tokens with cumulative prob $\geq p$.

```python
def beam_search(model, input_ids, beam_width=4, max_len=50):
    beams = [(input_ids, 0.0)]  # (seq, log_prob)
    for _ in range(max_len):
        candidates = []
        for seq, score in beams:
            logits = model(seq)[-1]             # next-token logits
            log_probs = F.log_softmax(logits, dim=-1)
            top_lp, top_idx = log_probs.topk(beam_width)
            for lp, idx in zip(top_lp, top_idx):
                new_seq = torch.cat([seq, idx.view(1)])
                candidates.append((new_seq, score + lp.item()))
        beams = sorted(candidates, key=lambda x: x[1], reverse=True)[:beam_width]
    return beams[0][0]
```

<div class="scenario" markdown>
**Scenario:** Summarization model produces short, repetitive summaries.<br>
**Answer:** Multiple fixes: (1) **length penalty** ($\alpha = 0.7$) to reward longer outputs, (2) **coverage penalty** to avoid repeat attention, (3) **minimum length constraint** — forbid EOS until $n$ tokens generated, (4) **no-repeat n-gram penalty** — zero out logits for tokens that would create a repeated n-gram, (5) switch to **nucleus sampling** if diversity matters more than fidelity.
</div>

---

## Q48. Gradient clipping — why and how { #q48 }

<span class="q-badge">Training</span>

**The problem**: even well-designed RNNs (LSTM, GRU) occasionally experience gradient explosions on specific batches — a single rare sequence can produce a gradient 1000× the typical magnitude, pushing weights into bad regions.

**Two clipping strategies**:

**1. Clip by value**: cap each coordinate of the gradient:

```python
torch.nn.utils.clip_grad_value_(model.parameters(), clip_value=5.0)
```

Simple but can distort direction.

**2. Clip by norm** (preferred): rescale the whole gradient vector if its norm exceeds threshold:

$$\mathbf{g} \leftarrow \begin{cases} \mathbf{g} & \text{if } \|\mathbf{g}\| \leq c \\ c \cdot \mathbf{g} / \|\mathbf{g}\| & \text{otherwise}\end{cases}$$

Preserves gradient direction, reduces magnitude only.

```python
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
optimizer.step()
```

**Typical values**:

- **RNNs**: clip at 1.0–5.0.
- **Transformers**: clip at 0.5–1.0.
- **Large language models**: usually 1.0.

**Side benefit**: monitoring the **unclipped gradient norm** is a great training-health metric. A sudden spike signals:

- Bad batch (outlier example).
- Learning rate too high.
- Numerical issue (NaN upstream).

**Important**: for mixed precision (FP16), clip *after* unscaling:

```python
# With GradScaler for AMP
scaler.scale(loss).backward()
scaler.unscale_(optimizer)              # undo loss scaling before clipping
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
scaler.step(optimizer)
scaler.update()
```

<div class="tip-box" markdown>
**Interviewer tip:** "Does gradient clipping affect convergence?" Clipping biases the step (rescales gradient) but is almost always worth it for stability. In regimes where clipping fires rarely (< 5% of steps), effect on convergence is negligible. Clipping firing >20% of the time is a signal to lower LR.
</div>

---

## Q49. Handling variable-length sequences — packing, masking, padding { #q49 }

<span class="q-badge">Practical</span>

A batch of sequences with different lengths — how do you handle this?

**Approach 1: Padding** (universal). Pad shorter sequences to max length in batch with a pad token. Simplest, but wastes compute on pad positions.

```python
from torch.nn.utils.rnn import pad_sequence
batch = [torch.tensor([1,2,3]), torch.tensor([4,5])]
padded = pad_sequence(batch, batch_first=True, padding_value=0)
# padded = [[1,2,3], [4,5,0]]
```

**Approach 2: Masking** — compute over padded batch, but apply a mask so pad positions don't contribute to loss or attention.

```python
mask = (tokens != PAD_TOKEN).float()
loss = (per_token_loss * mask).sum() / mask.sum()
```

**Approach 3: Pack-pad-pad** (PyTorch RNNs). `pack_padded_sequence` processes only non-pad positions:

```python
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

lengths = torch.tensor([3, 2])  # true sequence lengths
packed = pack_padded_sequence(padded, lengths, batch_first=True, enforce_sorted=False)
output, (h, c) = lstm(packed)
output, _ = pad_packed_sequence(output, batch_first=True)
```

Saves compute proportional to padding fraction. With nearly-sorted lengths (length-bucketed sampler), packing saves significant time.

**Approach 4: Bucketing / dynamic batching**. Group similar-length sequences into batches → minimal padding within each batch. Standard in NLP training pipelines.

**For transformers**: use attention mask — set masked positions to $-\infty$ before softmax, so attention weights on pad are zero.

```python
# Transformer attention mask (1 = attend, 0 = mask)
attn_mask = (tokens != PAD_TOKEN)
# Inside attention:
scores = scores.masked_fill(~attn_mask.unsqueeze(1), float('-inf'))
```

**Common bugs**:

- Forgetting to mask loss → loss includes pad positions → distorted.
- Masking attention but not the hidden → hidden states at pad positions are garbage, then used by downstream.
- `enforce_sorted=True` with unsorted data → silent indexing bug.

<div class="tip-box" markdown>
**Interviewer tip:** Know the three places to mask: (1) **loss** (don't count pad), (2) **attention** (don't attend to pad), (3) **pooling / aggregation** (don't include pad in mean/sum). Missing any one is a silent bug.
</div>

---

## Q50. CTC loss — alignment-free sequence training { #q50 }

<span class="q-badge">Specialized</span>

**Problem**: train a model to map input of length $T$ (e.g., 1000 audio frames) to output of length $U$ (e.g., 10 characters), where $T \gg U$ and alignment is unknown.

**Connectionist Temporal Classification (CTC)** (Graves et al., 2006):

1. Extend vocabulary with a **blank token** $\varnothing$.
2. Model outputs a distribution over the extended vocab for each of $T$ frames.
3. Define a many-to-one **collapse function** $\mathcal{B}$: merge consecutive repeats, then remove blanks.
   - e.g., `a a _ b b _ _ c` → `a b c` (where `_` is blank).
4. **CTC loss** = negative log-probability of the target sequence, marginalized over all length-$T$ alignments that collapse to it:

$$P(\mathbf{y} | \mathbf{x}) = \sum_{\pi \in \mathcal{B}^{-1}(\mathbf{y})} \prod_{t=1}^{T} p(\pi_t | \mathbf{x})$$

Computed efficiently via dynamic programming (forward-backward).

**Why blank is needed**: without it, you couldn't distinguish `"hello"` (2 separate `l`s) from `"helo"`. The blank between repeats preserves them.

**Use cases**:

- **Automatic Speech Recognition** (ASR): audio → text.
- **Handwriting recognition**.
- **Keyword spotting**.
- **Monotonic alignment tasks** generally.

**Inference**:

- **Greedy** (best path): pick argmax per frame, apply $\mathcal{B}$.
- **Beam search with language model**: CTC gives acoustic model; language model scores word sequences.

```python
# PyTorch CTC (log_probs are T x B x C with blank as index 0)
criterion = nn.CTCLoss(blank=0, zero_infinity=True)

log_probs = model(audio).log_softmax(dim=-1)     # (T, B, C)
input_lengths = torch.tensor([T]*B)               # length per batch item
target_lengths = torch.tensor([len(t) for t in targets])
flat_targets = torch.cat(targets)                 # concatenated targets

loss = criterion(log_probs, flat_targets, input_lengths, target_lengths)
```

**Alternatives**:

- **RNN-Transducer (RNN-T)**: addresses CTC's conditional independence assumption. Standard for streaming ASR.
- **Attention-based seq2seq**: conditions on previous outputs, more expressive but can hallucinate.
- **Hybrid CTC-attention**: multi-task learns both objectives.

<div class="tip-box" markdown>
**Interviewer tip:** CTC has a strong **conditional independence assumption** — output at frame $t$ is independent of other outputs given input. This is why CTC-only ASR hallucinates less but can't model language structure → you always combine with a language model at decoding time. RNN-T fixes this at the cost of more complex training.
</div>

---

## Q51. Character-level vs word-level vs subword tokenization { #q51 }

<span class="q-badge">NLP Foundation</span>

How you split text into input tokens determines what your model can learn.

**Word-level** (old school):

- Vocab = words. Fixed size (say 50k).
- **OOV (out-of-vocabulary) problem**: any word not in vocab becomes `<unk>`.
- Bad for morphologically rich languages (Finnish, Turkish — many forms of each root).
- Huge embedding matrix.

**Character-level**:

- Vocab tiny (100–300 chars).
- No OOV.
- Very long sequences → slow, hard to learn semantic units.
- Used in early LSTM models, some ASR / spelling tasks.

**Subword (modern default)**:

Balance between word and character — common substrings are merged into tokens, rare ones broken down.

| Method | Idea |
|---|---|
| **BPE (Byte-Pair Encoding)** | Start with chars, iteratively merge most frequent adjacent pair → subword vocab |
| **WordPiece** (BERT) | Similar to BPE, merges maximize likelihood of training corpus |
| **Unigram LM** (SentencePiece) | Start with large candidate set, prune to maximize corpus likelihood |
| **Byte-level BPE** (GPT-2+) | Operate on bytes, no Unicode issues, handles all languages |

**Example BPE**:
- Raw: `"unhappiness"`
- BPE tokens: `["un", "happi", "ness"]` → 3 tokens instead of 1 word or 11 chars.

**Properties**:

1. **No OOV**: anything can be tokenized (worst case: characters).
2. **Compact**: typical text ~0.75 tokens per word in English.
3. **Fertility**: some languages tokenize to more tokens per character than English → multilingual models have cost asymmetry.

**Practical notes**:

- Modern LLMs use byte-level BPE (GPT) or SentencePiece (LLaMA, Gemini).
- Vocab sizes typically 32k–256k.
- Tokenization can be **lossy** (trailing whitespace, special characters matter).

```python
# HuggingFace tokenizer
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8b")
tokens = tok.encode("Hello world!")                 # [IDs]
text = tok.decode(tokens)                            # roundtrip
```

<div class="scenario" markdown>
**Scenario:** Fine-tuning an LLM on domain-specific text (legal / biomedical) and losing accuracy.<br>
**Answer:** Possible cause: **tokenizer mismatch**. Your domain has vocab not well represented in pretraining tokenizer → common terms split into many pieces (e.g., `"hepatocellular"` → 5 tokens). Fix: (1) check token counts for domain terms, (2) **extend tokenizer** with domain-specific tokens + their embeddings (re-initialized), (3) use domain-adaptive pretraining before fine-tuning.
</div>

---

## Q52. Word embeddings — word2vec, GloVe, and their limits { #q52 }

<span class="q-badge">Historical</span>

**Motivation**: represent words as dense vectors such that semantic similarity → vector similarity.

**word2vec** (Mikolov et al., 2013) — two architectures:

- **CBOW**: predict center word from surrounding context.
- **Skip-gram**: predict context words from center word. Generally better for rare words.

**Loss (negative sampling)**:

$$L = \log \sigma(\mathbf{v}_c \cdot \mathbf{v}_w) + \sum_{k=1}^{K} \mathbb{E}_{w_k \sim P_n} \log \sigma(-\mathbf{v}_{w_k} \cdot \mathbf{v}_w)$$

Positive samples from context window, negatives sampled from unigram distribution (smoothed).

**GloVe** (Pennington et al., 2014): matrix factorization of the global co-occurrence matrix. Loss weighted by co-occurrence frequency. Similar performance to word2vec but different motivation.

**Famous emergent property**:

$$\vec{\text{king}} - \vec{\text{man}} + \vec{\text{woman}} \approx \vec{\text{queen}}$$

**Fundamental limitation — single vector per word**:

- `"bank"` (river) and `"bank"` (financial) share the same embedding.
- No way to handle polysemy.
- Context-free.

**Contextual embeddings (ELMo → BERT → GPT)**:

- ELMo (2018): biLSTM on language modeling, use hidden states as embeddings.
- BERT / GPT: transformer encoders produce context-dependent representations — `"bank"` in `"river bank"` vs `"Citibank"` → different vectors.
- This is what killed word2vec for NLP: contextual representations are strictly better.

**Where static embeddings still matter**:

- **Lightweight downstream tasks** (text classification on embedded vectors) — faster than running a transformer.
- **Retrieval and approximate nearest neighbor** for categorical-style tasks (e.g., product categories).
- **Cold-start cases** where transformer encoder is too heavy.

```python
# Using a pretrained embedding layer
import torch.nn as nn
embed = nn.Embedding.from_pretrained(glove_vectors, freeze=False)
# freeze=False allows fine-tuning during training
```

<div class="tip-box" markdown>
**Interviewer note:** Mention that word2vec / GloVe are mostly of historical interest in 2026. Modern practice uses **sentence/passage embeddings** (SBERT, E5, BGE, OpenAI's text-embedding-3) — these are transformer-based and contextual. Only reach for word2vec if you have extreme compute constraints.
</div>

---

## Q53. Language modeling — causal vs masked, perplexity { #q53 }

<span class="q-badge">NLP Foundation</span>

**Language modeling** = learning $P(\mathbf{x}) = P(x_1) P(x_2 | x_1) \cdots P(x_T | x_{<T})$ for a sequence $\mathbf{x}$.

**Two pretraining objectives**:

**1. Causal (autoregressive) LM** — predict next token given all previous:

$$L = -\sum_{t=1}^{T} \log P(x_t | x_{<t})$$

Models: GPT family, LLaMA, Gemini Pro, Claude. Good for **generation**.

**2. Masked LM (MLM)** — mask some tokens, predict them from bidirectional context:

$$L = -\sum_{t \in M} \log P(x_t | x_{\setminus M})$$

Models: BERT, RoBERTa. Good for **understanding** (classification, tagging, QA).

**Which when**:

| Task | Objective |
|---|---|
| Generation, chat, completion | Causal LM |
| Classification, sentiment, NER | MLM or Causal (both work) |
| Search / retrieval embeddings | Either, often MLM-based encoders |
| Machine translation | Encoder-decoder (mix of both) |

**Perplexity** — the universal LM metric:

$$\text{PPL} = \exp\left(-\frac{1}{T} \sum_t \log P(x_t | x_{<t})\right) = \exp(L)$$

Interpretation: "the model is as confused as if it had to choose uniformly among this many tokens per step." Lower is better.

**Typical perplexities** (on standard corpora):

| Model era | PPL (WikiText-103) |
|---|---|
| LSTM (2015) | 60 |
| Transformer-XL (2019) | 18 |
| GPT-2 | 17 |
| GPT-3 | 12 |
| GPT-4 / Claude 3 | ~5–7 |

**Limitations of PPL**:

- Only within-distribution; doesn't measure creativity, truthfulness, reasoning.
- Comparing across tokenizers is meaningless — PPL depends on tokenization granularity.
- Use **bits-per-character** for fair cross-model comparison if needed.

```python
# PPL computation
total_loss, total_tokens = 0, 0
with torch.no_grad():
    for batch in loader:
        logits = model(batch)
        loss = F.cross_entropy(
            logits[:, :-1].reshape(-1, V),
            batch[:, 1:].reshape(-1),
            reduction='sum'
        )
        total_loss += loss.item()
        total_tokens += (batch[:, 1:] != PAD).sum().item()

ppl = math.exp(total_loss / total_tokens)
```

<div class="tip-box" markdown>
**Interviewer insight:** BERT-era vs GPT-era — why did causal LM win in 2022+? Causal LMs scale more cleanly (no special mask token, next-token is natural), do text generation natively, and *with enough scale* can handle classification/understanding tasks almost as well as MLM (few-shot prompting). The bitter lesson played out here too — a simpler, more scalable objective won.
</div>

---

## Q54. Dropout in RNNs — the subtle right way to do it { #q54 }

<span class="q-badge">Practical</span>

Standard dropout applied to RNNs naively is **harmful** — it disrupts the recurrent dynamics.

**Wrong way**: apply fresh dropout at every time step to the recurrent connection $\mathbf{h}_{t-1}$:

- Different units zeroed at each step → model can't maintain coherent hidden state → destroys long-range learning.

**Right way** (Gal & Ghahramani, 2016 — "variational dropout"):

1. **Sample the dropout mask once per sequence**, apply the *same* mask at every time step.
2. Apply dropout to inputs and outputs independently.
3. Don't drop the cell state of LSTM (preserves memory).

**In PyTorch's built-in LSTM**, the `dropout` parameter applies dropout *between layers* only — not on the recurrent connection within a layer. For variational dropout on recurrent connections, you must implement it manually or use a specialized library.

```python
# PyTorch built-in: dropout between layers
lstm = nn.LSTM(128, 256, num_layers=3, dropout=0.3)
# Applies dropout between layer 1 output and layer 2 input, etc.

# Manual input/output dropout within timestep
class DropoutLSTM(nn.Module):
    def __init__(self, in_dim, hidden_dim, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(in_dim, hidden_dim, batch_first=True)
        self.dropout_in = nn.Dropout(dropout)
        self.dropout_out = nn.Dropout(dropout)

    def forward(self, x):
        x = self.dropout_in(x)       # input dropout (same mask per timestep)
        h, _ = self.lstm(x)
        return self.dropout_out(h)
```

**Zoneout** (Krueger et al., 2016) — alternative RNN regularization:

- Instead of zeroing units, randomly copy previous time step's hidden state for some units.
- Preserves information flow even when applied per-step.

**Layer normalization** often substitutes for dropout in recurrent settings — provides regularization indirectly by smoothing gradients.

<div class="tip-box" markdown>
**Interviewer signal:** "How do you apply dropout to an RNN?" Strong answer mentions variational dropout (same mask per sequence) or at least "dropout between layers, not within the recurrent connection". Saying "just `nn.Dropout` after the LSTM" is fine but shows shallower understanding.
</div>

---

## Q55. When RNNs still win — streaming, small, and efficient applications { #q55 }

<span class="q-badge">Modern Perspective</span>

Transformers dominate research, but **RNNs remain strong in specific niches** even in 2026:

**1. Online / streaming inference**:

- Transformers need the full context window; RNNs process one step at a time with O(1) state.
- **Real-time speech recognition** (streaming ASR): RNN-T is standard, not Transformer.
- **Online time-series anomaly detection**: small LSTM runs at microsecond latency on CPU.

**2. Very long sequences**:

- Transformer attention is $O(L^2)$ in sequence length. For $L = 100{,}000+$:
  - Full attention: intractable.
  - RNN: linear in $L$.
- **State-Space Models (SSMs)** like **Mamba** (2023) combine RNN linearity with transformer-like quality — growing alternative for long-sequence modeling.

**3. Resource-constrained settings**:

- Edge devices, IoT, embedded: LSTM with 1M params << Transformer with 100M.
- **Keyword spotting** ("Hey Siri"): tiny LSTM or even simpler.

**4. Tasks with strong sequential inductive bias**:

- Many time-series forecasting tasks don't need attention — recurrence is sufficient.
- Control / reinforcement learning policies with temporal context.

**5. Theoretical interest**:

- Recurrence is conceptually fundamental — understanding RNNs is prerequisite for understanding attention, SSMs, neural ODEs.

**Modern hybrid approaches**:

- **Linear RNNs** (RetNet, RWKV, Mamba): near-transformer quality with linear inference cost.
- **Attention + recurrence**: transformer encoder + RNN decoder, or transformer with recurrent memory (Transformer-XL, Compressive Transformer).

**Mamba (2023)** in particular has reignited interest in RNN-like architectures — state-space model with selective state, competitive with transformers at scale with linear complexity.

| Scenario | Pick |
|---|---|
| Language modeling at scale | Transformer / Mamba |
| Streaming ASR | RNN-T, Conformer |
| Time-series forecasting (single series, realtime) | LSTM / GRU |
| Edge keyword spotting | Tiny LSTM |
| Long document modeling | Mamba or sparse transformer |
| Standard NLP task | Transformer |

<div class="tip-box" markdown>
**Interviewer insight:** The "RNNs are dead" narrative is too strong. In 2026, the reality is: **Transformers won for language modeling at scale, but RNNs / SSMs are resurging for efficiency-critical applications**. Senior candidates distinguish where each architecture's inductive bias pays off.
</div>

---

## ✅ Module Recap

- **Vanilla RNN** fails on long sequences due to vanishing/exploding gradients from multiplicative dynamics.
- **LSTM** fixes this with gates + additive cell-state updates — the "constant error carousel". **GRU** simplifies to 2 gates; comparable performance for many tasks.
- **Attention + seq2seq** removed the bottleneck of compressing inputs into a single vector, paving the way for Transformers.
- **Teacher forcing** stabilizes training but causes **exposure bias**; addressed modernly by RLHF / DPO.
- **Tokenization** (subword, BPE) and contextual embeddings replaced word2vec/GloVe as the NLP foundation.
- **RNNs aren't dead** — streaming, small-model, and long-sequence applications still favor recurrence; Mamba/SSMs are a 2024+ resurgence.

→ Next: [🎯 Transformers & Attention](transformers.md)
