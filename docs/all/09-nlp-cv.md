# Module 9 — NLP and Computer Vision

> **Bible Module 9 of 14.** Self-contained. Written for **Hugging Face transformers 4.46+ (verified on 5.6), tokenizers 0.20+, datasets 3.x, sentence-transformers 3.x, accelerate 1.x, peft 0.13+, torch 2.5+ (verified on 2.11), torchvision 0.20+, timm 1.x**. All code runnable as-is on CPU; GPU paths are marked. Assumes Modules 1, 2, 4, 7, 8.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: pick the right NLP/CV approach for a problem (encoder vs decoder, fine-tune vs prompt vs embed); tokenize text correctly; fine-tune a Hugging Face encoder for classification, NER, and QA; build embedding pipelines for retrieval; fine-tune a vision foundation model; use object detection, segmentation, and audio models with a few lines of code; and ship any of the above behind a FastAPI service.

**Target reader.** Modules 1–4, 7, 8 done. Module 8 (PyTorch) is essential — every model here is a PyTorch model under the hood.

**How to use it.** Same as before. Run every code block; do all 36 problems before reading the solutions.

**Prerequisites.** Module 8.
**Next steps.** Module 10 (LLMs — generation, fine-tuning at scale, RAG, vLLM serving).

---

## 1. The 2026 NLP/CV landscape

### 1.1 The end of the "small model from scratch" era

Five years ago, an NLP project meant LSTM + word embeddings, trained from scratch on your data. Today, **you almost never train from scratch.** You start with a pretrained model. The question is which kind:

| Goal | Pick |
|---|---|
| Tag/classify/extract from existing text | **Encoder** (BERT, RoBERTa, DeBERTa, ModernBERT) — fine-tune |
| Generate fluent text, summaries, code | **Decoder** (GPT, Llama, Qwen) — Module 10 |
| Convert text-X → text-Y (translation, summary) | **Encoder-decoder** (T5, BART) or modern decoder |
| Search / retrieval / similarity | **Embedding model** (`sentence-transformers`, BGE, E5) |
| Image classification | **Vision Transformer** or **EfficientNet** — fine-tune |
| Detect bounding boxes | **DETR**, **YOLO**, **Grounding DINO** |
| Segment objects (per-pixel) | **SAM 2**, **Mask2Former** |
| Image + text together | **CLIP**, **BLIP-2**, **LLaVA-style** VLMs |
| Speech to text | **Whisper** |
| Speech embeddings / classification | **wav2vec2**, **HuBERT** |

### 1.2 The five jobs of NLP/CV in 2026

For most production problems you reach for one of these five patterns:

1. **Fine-tune an encoder for a classifier.** Sentiment, intent, content moderation, NER. The cheapest, fastest, most reliable production NLP.
2. **Embed → search.** Convert documents and queries to vectors; retrieve nearest neighbors. The basis of search and RAG (Module 10).
3. **Use a pretrained model zero-shot.** CLIP for image search, Whisper for transcription, Grounding DINO for detection — no training needed.
4. **Fine-tune a vision foundation model.** Replace the head, freeze most of the backbone, train on a few thousand images.
5. **Call a large LLM via API.** When the task needs reasoning, generation, or zero/few-shot flexibility (Module 10).

This module covers 1, 2, 3, and 4. Module 10 covers 5 in depth.

### 1.3 The Hugging Face ecosystem

Hugging Face publishes:
- **`transformers`** — model library (encoders, decoders, vision, audio, multimodal).
- **`tokenizers`** — fast Rust tokenizers.
- **`datasets`** — dataset library + arrow-backed loaders.
- **`accelerate`** — multi-GPU/precision wrapper around your training loop.
- **`peft`** — parameter-efficient fine-tuning (LoRA, QLoRA — Module 10).
- **`evaluate`** — metric library.
- **`safetensors`** — tensor format without pickle exec risk.
- **The Hub** — free hosting for models and datasets.

You'll use 5–6 of these in any production NLP project. Internalize the cohesive design.

---

## 2. Tokenization — the foundation everyone glosses over

A tokenizer turns text into a sequence of integer IDs the model can read. **Every NLP bug is a tokenization bug until proven otherwise.**

### 2.1 The three families

| Family | Models | Idea |
|---|---|---|
| **WordPiece** | BERT, DistilBERT | Greedy subword merging by likelihood |
| **BPE** | GPT-2/4, RoBERTa, Llama | Byte-pair encoding from frequency |
| **SentencePiece (BPE/Unigram)** | T5, mBART, Whisper, Llama 2/3 | Language-agnostic; treats input as raw bytes |

You don't pick one; you load the tokenizer that matches your model. **Mixing tokenizers and models is a classic fatal bug.**

### 2.2 The basic Hugging Face tokenizer

```python
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("bert-base-uncased")
out = tok("Hello, world!", return_tensors="pt")
print(out)
# {'input_ids': tensor([[101, 7592, 1010, 2088, 999, 102]]),
#  'token_type_ids': tensor([[0, 0, 0, 0, 0, 0]]),
#  'attention_mask': tensor([[1, 1, 1, 1, 1, 1]])}

print(tok.decode(out["input_ids"][0]))     # "[CLS] hello, world! [SEP]"
```

Three keys you'll see constantly:
- **`input_ids`** — the integer token IDs.
- **`attention_mask`** — 1 for real tokens, 0 for padding.
- **`token_type_ids`** — 0 for first segment, 1 for second (only used in some models like BERT for sentence-pair tasks).

### 2.3 Special tokens that matter

| Token | Role |
|---|---|
| `[CLS]` (BERT) / `<s>` (RoBERTa) | Start-of-sequence / classification token |
| `[SEP]` / `</s>` | End-of-sequence / sentence separator |
| `[PAD]` / `<pad>` | Padding |
| `[MASK]` / `<mask>` | Masked-language-modeling token |
| `[UNK]` / `<unk>` | Out-of-vocabulary |
| `<bos>`, `<eos>` | Begin / end of sequence (Llama-style) |

`tok.cls_token_id`, `tok.sep_token_id`, etc. give you the integer IDs.

### 2.4 Padding, truncation, and batching

For batches, all sequences must be the same length. Tokenizer handles this:

```python
batch = tok(
    ["short", "much longer sentence to tokenize"],
    padding=True,           # pad to longest in batch
    truncation=True,        # truncate to model max len
    max_length=128,         # explicit cap
    return_tensors="pt",
)
print(batch["input_ids"].shape)        # (2, 8) — the longer sequence's length
```

**Padding strategies:**
- `padding=True` — to longest in batch (efficient).
- `padding="max_length"` — to a fixed `max_length` (uniform, less efficient).
- `padding=False` — no padding (only useful for single sequence).

### 2.5 Sentence pairs

For tasks like NLI / sentence-pair classification:

```python
out = tok("The cat sat on the mat.", "It was tired.",
          padding=True, truncation=True, return_tensors="pt")
# token_type_ids identifies which segment each token belongs to
```

### 2.6 The fast tokenizer — and why it matters

`AutoTokenizer.from_pretrained(...)` returns a "fast" tokenizer (Rust-backed) by default. Two superpowers:

1. **Word-to-token alignment.** `out.word_ids(0)` tells you which original word each token came from — essential for token classification (NER) and QA.
2. **Speed.** Roughly 10× faster than the slow Python tokenizers.

```python
out = tok("Hugging Face is great.", return_tensors="pt", return_offsets_mapping=True)
print(out.word_ids(0))            # [None, 0, 0, 1, 2, 3, None]  (None = special tokens)
print(out["offset_mapping"])      # character spans for each token
```

### 2.7 The "max sequence length" trap

Each model has a **maximum context length**:
- BERT-base: 512 tokens.
- RoBERTa-base: 512.
- ModernBERT: 8192.
- Llama 3: 128k.

If your input is longer, you must truncate or chunk. For documents > model max:
- **Classification:** truncate (often the first 512 tokens are enough; sometimes use sliding window + voting).
- **QA over long docs:** use a long-context model like ModernBERT / Longformer, or chunk + retrieve.
- **Generation:** Module 10's RAG pattern.

### 2.8 What tokenization actually looks like

```python
text = "preprocessing"
print(tok.tokenize(text))     # ['pre', '##process', '##ing']  ← BERT WordPiece

text = "I'd've"
print(tok.tokenize(text))     # contractions split into multiple tokens
```

Each token is roughly ¾ of a word for English. For other languages (Chinese, Arabic, code), tokenization can be much denser. Always count tokens, not words, for context limits.

---

## 3. The transformer architecture (just enough)

You don't need to memorize every paper. You do need this much:

### 3.1 The core ideas

A transformer is a stack of identical layers, each containing:
1. **Multi-head self-attention** — every token looks at every other token. Lets the model build context-dependent representations.
2. **Feed-forward network** — a per-token MLP.
3. **Residual connections + LayerNorm** — keeps gradients flowing.

Inputs are token embeddings + positional embeddings (so the model knows token order).

### 3.2 The three architecture flavors

```
Encoder-only (BERT)
  input ──► [layer × 12] ──► hidden states ──► task head
  Attention is bidirectional (every token sees every other)
  Trained with masked-language-modeling (MLM)
  Use for: classification, NER, embeddings

Decoder-only (GPT, Llama)
  input ──► [layer × N] ──► next-token logits
  Attention is CAUSAL (each token sees only the past)
  Trained with next-token prediction
  Use for: generation, chat, code

Encoder-decoder (T5, BART)
  encoder reads source, decoder writes target attending to encoder
  Use for: translation, summarization (less common in 2026; modern decoders cover most cases)
```

### 3.3 Self-attention in one paragraph

Each token gets a Query, a Key, and a Value vector via three learned linear projections. Attention is `softmax(Q K^T / sqrt(d)) V`: every token computes how much it should attend to every other token's value, weighted by Q-K similarity. **Multi-head** means doing this in parallel several times with different projections; the heads learn different relations (syntax, coreference, position, etc.).

### 3.4 Why transformers won

- **Parallelism** — every position computes simultaneously (vs RNN sequential).
- **Long-range context** — direct connections between any two tokens (vs RNN's diminishing memory).
- **Scaling laws** — adding more parameters and data reliably improves quality, far beyond what RNNs achieved.

---

## 4. Hugging Face transformers — the API you'll live in

### 4.1 The `Auto*` classes

```python
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification, AutoConfig

# the model and tokenizer always come together — same checkpoint name
checkpoint = "bert-base-uncased"
tok = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModel.from_pretrained(checkpoint)            # base model — outputs hidden states
config = AutoConfig.from_pretrained(checkpoint)
print(config.hidden_size, config.num_hidden_layers)      # 768, 12

# task-specific heads
clf_model = AutoModelForSequenceClassification.from_pretrained(
    checkpoint, num_labels=3
)   # adds a randomly initialized classifier head on top
```

The `AutoModelFor*` family includes:
- `AutoModelForSequenceClassification` — single label per sequence.
- `AutoModelForTokenClassification` — label per token (NER, POS).
- `AutoModelForQuestionAnswering` — extractive QA.
- `AutoModelForMaskedLM` — masked-token prediction.
- `AutoModelForCausalLM` — next-token prediction (GPT-style).
- `AutoModelForSeq2SeqLM` — encoder-decoder generation.
- `AutoModelForImageClassification`, `AutoModelForObjectDetection`, etc.

### 4.2 The `pipeline` shortcut — for prototyping

For quick experiments and zero-shot use:

```python
from transformers import pipeline

clf = pipeline("sentiment-analysis")
print(clf("I love this!"))
# [{'label': 'POSITIVE', 'score': 0.9998}]

ner = pipeline("ner", grouped_entities=True)
print(ner("Apple is looking at buying U.K. startup for $1 billion"))
# [{'entity_group': 'ORG', 'word': 'Apple', ...}, ...]

# zero-shot — no training needed
zsl = pipeline("zero-shot-classification")
print(zsl("This is a great smartphone", candidate_labels=["technology", "sports", "politics"]))
```

`pipeline` is great for prototypes; not for production batch scoring (use the tokenizer + model directly for throughput).

### 4.3 Datasets library — load + map

`datasets` (Hugging Face) gives you a memory-mapped, columnar dataset format with built-in batching and lazy mapping.

```python
from datasets import load_dataset

ds = load_dataset("imdb")          # downloads + caches
print(ds)                           # DatasetDict with train, test
print(ds["train"][0])               # {'text': '...', 'label': 0}

# map a function over the dataset (lazy; cached)
def tokenize_fn(batch):
    return tok(batch["text"], truncation=True, max_length=256)

ds_tok = ds.map(tokenize_fn, batched=True, remove_columns=["text"])
ds_tok = ds_tok.with_format("torch")     # makes __getitem__ return tensors
```

Loading custom data:
```python
from datasets import Dataset
df = pd.DataFrame({"text": ["a", "b"], "label": [0, 1]})
ds = Dataset.from_pandas(df)
# or from JSON / CSV / parquet:
ds = load_dataset("json", data_files={"train": "data/train.jsonl"})
```

### 4.4 Saving and loading models

```python
# save
model.save_pretrained("my-bert/")
tok.save_pretrained("my-bert/")

# load
model = AutoModelForSequenceClassification.from_pretrained("my-bert/")
tok   = AutoTokenizer.from_pretrained("my-bert/")
```

Always save tokenizer + model together — they form a unit. Hugging Face writes model weights as `safetensors` by default (no pickle exec risk).

---

## 5. Fine-tuning encoder models — the production workhorse

The single most reliable NLP pattern: take a pretrained encoder, add a classifier/token-classifier/QA head, fine-tune for 2-4 epochs at LR ~2e-5. Cheap, fast, robust.

### 5.1 Sequence classification — full example

```python
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_cosine_schedule_with_warmup
from datasets import load_dataset
import torchmetrics

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
checkpoint = "distilbert-base-uncased"
tok = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(checkpoint, num_labels=2).to(device)

ds = load_dataset("imdb")
def tokenize_fn(batch):
    return tok(batch["text"], truncation=True, max_length=256)
ds_tok = ds.map(tokenize_fn, batched=True, remove_columns=["text"])
ds_tok = ds_tok.with_format("torch", columns=["input_ids","attention_mask","label"])

from transformers import DataCollatorWithPadding
collator = DataCollatorWithPadding(tokenizer=tok)
train_loader = DataLoader(ds_tok["train"], batch_size=32, shuffle=True, collate_fn=collator)
val_loader   = DataLoader(ds_tok["test"],  batch_size=64, shuffle=False, collate_fn=collator)

epochs = 3
total_steps = len(train_loader) * epochs

optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
scheduler = get_cosine_schedule_with_warmup(optimizer,
                                             num_warmup_steps=int(0.1 * total_steps),
                                             num_training_steps=total_steps)

acc = torchmetrics.classification.MulticlassAccuracy(num_classes=2).to(device)

for epoch in range(epochs):
    model.train()
    for batch in train_loader:
        batch = {k: v.to(device, non_blocking=True) for k, v in batch.items()}
        optimizer.zero_grad(set_to_none=True)
        out = model(**batch)                # auto-uses 'labels' key for loss
        out.loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step(); scheduler.step()

    model.eval(); acc.reset()
    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(device, non_blocking=True) for k, v in batch.items()}
            logits = model(**{k: v for k, v in batch.items() if k != "label"}).logits
            acc.update(logits, batch["label"])
    print(f"epoch {epoch} val acc {acc.compute().item():.4f}")
```

**The pattern.** `out = model(**batch)` returns an object with `loss`, `logits`. The collator dynamically pads each batch to its longest sequence — much faster than padding to model max.

### 5.2 The `Trainer` API — when you want less boilerplate

```python
from transformers import TrainingArguments, Trainer
import numpy as np
import evaluate as hf_evaluate

metric = hf_evaluate.load("accuracy")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    return metric.compute(predictions=np.argmax(logits, axis=1), references=labels)

args = TrainingArguments(
    output_dir="out",
    learning_rate=2e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=64,
    num_train_epochs=3,
    weight_decay=0.01,
    warmup_ratio=0.1,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    bf16=True,                    # mixed precision on Ampere+
    logging_steps=50,
    report_to="none",            # disable wandb default
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=ds_tok["train"],
    eval_dataset=ds_tok["test"],
    tokenizer=tok,
    data_collator=collator,
    compute_metrics=compute_metrics,
)
trainer.train()
trainer.save_model("my-classifier/")
```

### 5.3 Token classification (NER)

```python
from transformers import AutoModelForTokenClassification

# tokenize and align labels
def tokenize_and_align(examples):
    enc = tok(examples["tokens"], is_split_into_words=True,
              truncation=True, max_length=128)
    labels = []
    for i, label_seq in enumerate(examples["ner_tags"]):
        word_ids = enc.word_ids(i)
        prev_word, label_row = None, []
        for w in word_ids:
            if w is None:
                label_row.append(-100)        # ignore in loss
            elif w != prev_word:
                label_row.append(label_seq[w])
            else:
                label_row.append(-100)        # only first subword is labeled
            prev_word = w
        labels.append(label_row)
    enc["labels"] = labels
    return enc
```

**Two rules of NER fine-tuning:**
1. Label only the **first subword** of each word; mark continuation tokens as `-100` (ignored by loss).
2. Pad with `-100` for special tokens.

### 5.4 Question Answering (SQuAD-style)

Extractive QA predicts start/end token positions of an answer span:

```python
from transformers import AutoModelForQuestionAnswering

def prepare_qa(examples):
    questions = [q.strip() for q in examples["question"]]
    enc = tok(questions, examples["context"], truncation="only_second",
              max_length=384, stride=128, return_overflowing_tokens=True,
              return_offsets_mapping=True, padding="max_length")
    # complex but standard: map answer character positions to token positions
    # see https://huggingface.co/learn/nlp-course/chapter7/7
    return enc
```

QA fine-tuning is finicky; reach for the HF tutorial as the reference. Modern alternative: feed the doc as context to a generative LLM (Module 10).

### 5.5 Hyperparameter rules of thumb

| Setting | Typical value |
|---|---|
| Learning rate | 2e-5 to 5e-5 |
| Epochs | 2 to 4 |
| Batch size | 16 to 32 (encoder fine-tuning) |
| Warmup | 10% of total steps |
| Weight decay | 0.01 |
| Max sequence length | 256 (text classif.) or 384 (QA) |
| Mixed precision | bf16 on Ampere+, fp16 on V100 |

Don't over-tune. If you can't get good results with these defaults, the bottleneck is data, not hyperparameters.

---

## 6. Embeddings — the swiss army knife

Embeddings turn text into fixed-length vectors. Similar texts have nearby vectors. Foundation for: search, RAG, deduplication, clustering, recommendation, classification (kNN).

### 6.1 Sentence-Transformers — the easy path

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Production-grade general-purpose model in 2026:
model = SentenceTransformer("BAAI/bge-base-en-v1.5")    # ~420 MB, 768-dim

texts = [
    "Pizza is my favorite food.",
    "I love eating pizza.",
    "Quantum mechanics deals with subatomic particles.",
]
embeddings = model.encode(texts, normalize_embeddings=True)
print(embeddings.shape)           # (3, 768)

# similarity is just dot product on normalized vectors
sim = embeddings @ embeddings.T
print(sim.round(3))
# diagonal = 1; pizza pair ≈ 0.85; pizza vs quantum ≈ 0.20
```

`normalize_embeddings=True` makes vectors unit-length so dot product = cosine similarity.

### 6.2 Picking an embedding model in 2026

The MTEB leaderboard ranks models. Useful tiers:

| Tier | Examples | When |
|---|---|---|
| Tiny / fast | `all-MiniLM-L6-v2` (22M, 384-d) | Edge, low latency, modest quality |
| Standard | `BAAI/bge-base-en-v1.5` (110M, 768-d) | Default for most pipelines |
| Strong | `BAAI/bge-large-en-v1.5` (335M, 1024-d) | Best open quality |
| Multilingual | `BAAI/bge-m3` | Multi-language search |
| Domain-specific | code, biomedical, legal variants | When generic underperforms |

**Don't pick by leaderboard alone.** Run an eval on your data — even 1k pairs with relevance labels, measured as nDCG@10 — and pick what works.

### 6.3 Vector search basics

For fast nearest-neighbor search on millions of vectors, you need an index — not a Python loop.

```python
import numpy as np

# small case: brute force is fine
def brute_force_topk(query_emb, doc_embs, k=10):
    sims = doc_embs @ query_emb         # (N,)
    return np.argpartition(-sims, k)[:k]
```

For production:
- **In-memory:** `faiss-cpu` / `faiss-gpu`, `hnswlib`, `usearch`.
- **Managed:** Pinecone, Weaviate, Qdrant Cloud, pgvector (Postgres), BigQuery vector search (Module 5).

```python
# faiss example
import faiss
index = faiss.IndexFlatIP(768)        # inner-product on normalized = cosine
index.add(doc_embs.astype("float32"))
D, I = index.search(query_emb.reshape(1, -1).astype("float32"), k=10)
```

For >1M vectors, use HNSW or IVF-PQ for sub-linear queries.

### 6.4 Symmetric vs asymmetric retrieval

- **Symmetric** (text–text similarity): query and doc are the same kind ("find similar tweets"). Pick a sentence model.
- **Asymmetric** (query–doc): short question retrieves long passage. Use a model trained for retrieval (BGE, E5) and a query prefix:

```python
queries = ["Represent this sentence for searching relevant passages: " + q for q in raw_queries]
docs    = raw_docs
q_emb   = model.encode(queries, normalize_embeddings=True)
d_emb   = model.encode(docs,    normalize_embeddings=True)
```

Different models use different prefixes — read the model card.

### 6.5 Reranking — precision at the top

Embedding retrieval is fast but coarse. Rerank the top-50 with a **cross-encoder** for higher precision:

```python
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-base")

scores = reranker.predict([(query, doc) for doc in candidate_docs])
ranked = sorted(zip(candidate_docs, scores), key=lambda x: -x[1])
```

A cross-encoder takes (query, doc) **together** through the transformer — much more accurate than embedding similarity but ~100× slower per pair. Standard pipeline: embed → top-50 → cross-encode → top-5.

### 6.6 Embedding pipelines in production

- **Cache** embeddings of static documents — never recompute.
- **Version** the embedding model — when you change models, ALL embeddings need recomputation.
- **Batch** the encode calls (`encode(texts, batch_size=64)`).
- **Monitor** embedding drift — if your queries' distribution shifts, retrieval quality may quietly degrade.

---

## 7. Generation models — fundamentals (Module 10 goes deeper)

Decoder-only models (GPT, Llama, Qwen, Mistral) generate text by predicting the next token, repeatedly. Most production "AI features" call a hosted API; sometimes you fine-tune a smaller open model.

### 7.1 Loading and generating with HF

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
checkpoint = "Qwen/Qwen2.5-1.5B-Instruct"
tok = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForCausalLM.from_pretrained(
    checkpoint, torch_dtype=torch.bfloat16
).to(device)

prompt = "Explain transformers in one sentence."
messages = [{"role": "user", "content": prompt}]
inputs = tok.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True).to(device)

with torch.inference_mode():
    out = model.generate(
        inputs,
        max_new_tokens=200,
        do_sample=True, temperature=0.7, top_p=0.9,
        pad_token_id=tok.eos_token_id,
    )
print(tok.decode(out[0][inputs.shape[1]:], skip_special_tokens=True))
```

### 7.2 Generation parameters

| Parameter | Meaning | Typical |
|---|---|---|
| `max_new_tokens` | Hard cap on output length | 200–2000 |
| `do_sample=True` | Sample from distribution | for chat |
| `temperature` | Distribution sharpness; 0 = greedy | 0.7 typical, 0 for deterministic |
| `top_p` | Nucleus — keep top-p mass | 0.9–0.95 |
| `top_k` | Keep top-k tokens | 50 (less common w/ top_p) |
| `repetition_penalty` | Discourage repeats | 1.05–1.2 |
| `num_beams` | Beam search | 1 (greedy/sample) or 4 (deterministic) |

**Greedy** (`do_sample=False, num_beams=1`) is deterministic but boring. **Sampling with temperature 0.7** is the chat default. **Beam search** for translation/summarization where there's "one right answer."

### 7.3 Where small generative models still win

Module 10 focuses on big LLMs. Small ones (1–7B) still win for:
- **Strict formats / classification dressed as generation** — fine-tune a 1B model to output JSON; cheaper and faster than API calls at scale.
- **Privacy-sensitive workloads** where data can't leave your infra.
- **Specialized tasks** with enough training data to fine-tune (e.g., code completion in a niche language).

For everything else, calling a frontier API is usually cheaper than self-hosting at <100 RPS.


---

## 8. Vision — CNNs, ViTs, foundation models

Like NLP, vision in 2026 starts with a pretrained model. The question is which.

### 8.1 The ladder of vision models

| Model | When |
|---|---|
| **EfficientNetV2 / RegNetY** (CNN) | Tight memory budget, edge inference |
| **ResNet50** (CNN) | Boringly reliable baseline |
| **ConvNeXt v2** | Best CNN in 2026 |
| **ViT** (Vision Transformer) | Standard for fine-tuning when data is plentiful |
| **DeiT III**, **Swin v2** | ViT improvements |
| **DINOv2** | **Self-supervised**; killer for low-label regimes; great as a frozen feature extractor |
| **CLIP / SigLIP** | Image+text contrastive; zero-shot classification, retrieval |
| **SAM 2** | Segmentation foundation model (zero-shot) |

### 8.2 Loading a pretrained vision model with `timm`

`timm` (PyTorch Image Models) is the de facto registry for vision pretrained models. Hundreds of architectures with consistent API.

```python
# timm install: pip install timm
import timm
import torch

model = timm.create_model("convnextv2_base", pretrained=True, num_classes=10)   # adapt head
model.eval()

# get the model's expected preprocessing
data_cfg = timm.data.resolve_data_config({}, model=model)
transform = timm.data.create_transform(**data_cfg)

x = torch.randn(1, 3, 224, 224)
with torch.inference_mode():
    out = model(x)
print(out.shape)              # (1, 10)
```

### 8.3 Hugging Face vision models — same API as NLP

```python
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image

processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
model = AutoModelForImageClassification.from_pretrained("google/vit-base-patch16-224")

img = Image.open("photo.jpg")
inputs = processor(images=img, return_tensors="pt")
with torch.inference_mode():
    out = model(**inputs)
predicted = out.logits.argmax(-1).item()
print(model.config.id2label[predicted])
```

**Three families on the Hub:** `AutoModelForImageClassification`, `AutoModelForObjectDetection`, `AutoModelForSemanticSegmentation`.

### 8.4 Fine-tuning a ViT for classification

Same pattern as NLP:
```python
from transformers import AutoModelForImageClassification, TrainingArguments, Trainer

model = AutoModelForImageClassification.from_pretrained(
    "google/vit-base-patch16-224",
    num_labels=10, ignore_mismatched_sizes=True,    # replaces head
)
# Trainer + TrainingArguments same as NLP, but use a vision-aware data collator
```

`ignore_mismatched_sizes=True` is essential when changing `num_labels` — the new head is randomly initialized.

### 8.5 DINOv2 as a frozen feature extractor (the cheap classifier)

For very limited labeled data, a **linear probe on a self-supervised model** often beats full fine-tuning of a smaller model:

```python
from transformers import AutoImageProcessor, AutoModel
import torch.nn as nn

processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
encoder   = AutoModel.from_pretrained("facebook/dinov2-base")

# freeze
for p in encoder.parameters(): p.requires_grad = False

class LinearProbe(nn.Module):
    def __init__(self, encoder, num_classes):
        super().__init__()
        self.enc = encoder
        self.head = nn.Linear(encoder.config.hidden_size, num_classes)
    def forward(self, pixel_values):
        with torch.no_grad():
            feats = self.enc(pixel_values=pixel_values).last_hidden_state[:, 0]   # CLS token
        return self.head(feats)
```

Train only the linear head. With 100-1000 labels, this often hits 90% of fine-tune quality at 1% of compute.

### 8.6 CLIP — zero-shot classification without training

CLIP (and SigLIP) jointly embed images and text. You can classify any image against arbitrary text labels with no training:

```python
from transformers import AutoProcessor, AutoModel
import torch

proc = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = AutoModel.from_pretrained("openai/clip-vit-base-patch32")

img = Image.open("photo.jpg")
candidate_labels = ["a cat", "a dog", "a car", "a person"]
inputs = proc(text=candidate_labels, images=img, return_tensors="pt", padding=True)

with torch.inference_mode():
    out = model(**inputs)
logits = out.logits_per_image            # (1, num_labels)
probs = logits.softmax(dim=-1).flatten()
for label, p in zip(candidate_labels, probs.tolist()):
    print(f"{label}: {p:.3f}")
```

**Use CLIP for:**
- Zero-shot classification when categories aren't fixed.
- Image-text retrieval ("find images matching this caption").
- A cheap content-tagging baseline before training a custom model.

### 8.7 Augmentation — the highest-leverage CV regularizer

For training, augmentation is often more important than architecture changes.

```python
from torchvision import transforms as T

train_tfm = T.Compose([
    T.RandomResizedCrop(224, scale=(0.8, 1.0)),
    T.RandomHorizontalFlip(),
    T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    T.ToTensor(),
    T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    T.RandomErasing(p=0.25),
])
```

Modern strong augmentations: **CutMix**, **Mixup**, **TrivialAugment**, **RandAugment**. Used in nearly every winning vision recipe.

---

## 9. Object detection and segmentation (basics)

Detection and segmentation have specialized models and pipelines. For practitioners, two paths:

### 9.1 Bounding-box detection — three options

```python
# Option 1: ultralytics YOLO (fast, real-time, good defaults)
# pip install ultralytics
from ultralytics import YOLO

model = YOLO("yolo11n.pt")               # nano variant
results = model("image.jpg")
for r in results:
    for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
        print(box.tolist(), int(cls.item()), float(conf.item()))
```

```python
# Option 2: Hugging Face DETR / RT-DETR (transformer-based, integrated with HF stack)
from transformers import AutoImageProcessor, AutoModelForObjectDetection

proc = AutoImageProcessor.from_pretrained("PekingU/rtdetr_v2_r50vd")
model = AutoModelForObjectDetection.from_pretrained("PekingU/rtdetr_v2_r50vd")

img = Image.open("photo.jpg")
inputs = proc(images=img, return_tensors="pt")
with torch.inference_mode():
    out = model(**inputs)
# post-process to [x1, y1, x2, y2, score, label]
results = proc.post_process_object_detection(out, target_sizes=torch.tensor([img.size[::-1]]),
                                                threshold=0.5)[0]
```

```python
# Option 3: Grounding DINO — open-vocabulary detection by text prompt
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

proc  = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-base")
model = AutoModelForZeroShotObjectDetection.from_pretrained("IDEA-Research/grounding-dino-base")

text = "a person. a dog."        # period-separated phrases
inputs = proc(images=img, text=text, return_tensors="pt")
with torch.inference_mode():
    out = model(**inputs)
```

**Decision:**
- **YOLO** for real-time, fast, video, edge.
- **RT-DETR / DETR** for the HF ecosystem with reasonable speed.
- **Grounding DINO** for open-vocabulary — detect anything you can name.

### 9.2 Segmentation — Segment Anything (SAM)

SAM 2 segments anything you point to or box around:

```python
from transformers import AutoProcessor, AutoModel

proc = AutoProcessor.from_pretrained("facebook/sam2-hiera-base-plus")
model = AutoModel.from_pretrained("facebook/sam2-hiera-base-plus")

inputs = proc(images=img, input_points=[[[500, 375]]], return_tensors="pt")
with torch.inference_mode():
    out = model(**inputs)
# out.pred_masks holds the binary masks
```

For automatic segmentation of every object: SAM's automatic mask generator — no prompts needed.

### 9.3 Fine-tuning detection / segmentation

Possible but harder. The standard pipeline:
1. Convert your data to COCO format (`{"images":[...], "annotations":[...]}`).
2. Use the model author's recipe (Ultralytics for YOLO; HF tutorials for DETR; Detectron2 for general detection).
3. Use a strong augmentation pipeline (`albumentations`).

For most teams: **start with zero-shot** (SAM, Grounding DINO, CLIP). Only fine-tune when zero-shot quality is insufficient.

---

## 10. Audio and speech (briefly)

### 10.1 Speech-to-text with Whisper

```python
from transformers import pipeline

pipe = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo",
                 chunk_length_s=30, return_timestamps=True)
result = pipe("audio.wav")
print(result["text"])
# with timestamps:
# [{'timestamp': (0.0, 3.5), 'text': '...'}, ...]
```

Whisper-large-v3-turbo is the open ASR baseline in 2026. For multilingual, it covers ~100 languages with one model.

### 10.2 Audio classification / embeddings

```python
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

feat = AutoFeatureExtractor.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593")
model = AutoModelForAudioClassification.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593")
# inputs: 16kHz waveform; predicts AudioSet labels
```

For audio search, `wav2vec2`-style embeddings work well. For music: dedicated models (CLAP, MERT).

### 10.3 The audio-data trap

- Sample rate: most models expect **16 kHz**. Resample your data with `librosa.resample` or `torchaudio`.
- Channels: most models expect **mono**. Convert with `audio.mean(dim=0)`.
- Length: chunk long audio (Whisper's `chunk_length_s=30`) — model context is limited.

---

## 11. Multimodal — vision-language models (VLMs)

VLMs take an image and text together; output text. The 2026 mainstream:

```python
from transformers import AutoProcessor, AutoModelForVision2Seq

proc  = AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLM2-2.2B-Instruct")
model = AutoModelForVision2Seq.from_pretrained("HuggingFaceTB/SmolVLM2-2.2B-Instruct",
                                                  torch_dtype=torch.bfloat16)

messages = [{"role": "user", "content": [
    {"type": "image", "image": img},
    {"type": "text",  "text":  "Describe this image."},
]}]
inputs = proc.apply_chat_template(messages, add_generation_prompt=True,
                                    tokenize=True, return_dict=True, return_tensors="pt")
with torch.inference_mode():
    out_ids = model.generate(**inputs, max_new_tokens=300)
print(proc.decode(out_ids[0], skip_special_tokens=True))
```

**Use VLMs for:** image captioning, visual question answering, OCR-light tasks, document understanding (when paired with strong OCR), accessibility (alt-text), content moderation with nuance.

**Don't use VLMs for:** strict bounding-box detection (use a detector), pixel-perfect segmentation (use SAM), or high-throughput tagging (CLIP is much cheaper).

---

## 12. Evaluation — picking honest metrics

### 12.1 NLP — beyond accuracy

| Task | Metrics |
|---|---|
| Classification | accuracy, macro-F1, AUROC |
| NER | seqeval F1 (entity-level) |
| QA | exact-match, F1 (token-level) |
| Translation | BLEU, COMET (neural), chrF |
| Summarization | ROUGE, BERTScore, human eval |
| Generation quality | LLM-as-judge (Module 13), human eval |

```python
import evaluate as hf_evaluate
seqeval = hf_evaluate.load("seqeval")
print(seqeval.compute(predictions=preds_strs, references=refs_strs))
# → entity-level precision/recall/F1
```

For NER, use **entity-level F1** (seqeval), not token-level — partial matches don't count.

### 12.2 Retrieval

- **Recall@K** — does the relevant doc appear in top K?
- **MRR** (Mean Reciprocal Rank) — how high is the first relevant doc?
- **nDCG@K** — graded relevance, position-aware.

These need labeled query-document relevance (even 50–500 query/doc pairs is enough to start).

### 12.3 Vision

- **Classification:** top-1, top-5 accuracy.
- **Detection:** mAP at IoU thresholds (mAP@0.5, mAP@0.5:0.95).
- **Segmentation:** IoU per class, mean IoU.

### 12.4 The cardinal rule

Whatever metric you optimize is what you'll get. Pick metrics that align with the **business outcome**, not just what's standard. A model with 0.85 F1 that mispredicts in costly ways is worse than 0.80 F1 that fails gracefully.

---

## 13. Deployment

### 13.1 Encoder fine-tunes — small, fast, easy to ship

A fine-tuned BERT-base (110M params) runs at ~50ms/request on CPU, ~5ms on GPU. Standard FastAPI service (Module 4) wrapping HF model is fine.

```python
# serve.py
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = FastAPI()

@app.on_event("startup")
def load():
    app.state.tok = AutoTokenizer.from_pretrained("/models/sentiment/")
    app.state.model = AutoModelForSequenceClassification.from_pretrained("/models/sentiment/")
    app.state.model.eval()
    app.state.id2label = app.state.model.config.id2label

class Req(BaseModel):
    text: str

@app.post("/classify")
@torch.inference_mode()
def classify(req: Req):
    inputs = app.state.tok(req.text, truncation=True, max_length=256, return_tensors="pt")
    logits = app.state.model(**inputs).logits[0]
    probs = logits.softmax(-1).tolist()
    return {"label": app.state.id2label[int(logits.argmax())],
            "probabilities": probs}
```

Wrap in Module 6's Dockerfile, deploy to Cloud Run / Fargate.

### 13.2 ONNX export for faster CPU inference

```python
# pip install optimum[onnxruntime]
from optimum.onnxruntime import ORTModelForSequenceClassification

# convert + save
ort_model = ORTModelForSequenceClassification.from_pretrained(
    "/models/sentiment/", export=True
)
ort_model.save_pretrained("/models/sentiment-onnx/")

# serve with onnxruntime — typically 2-3× faster on CPU than PyTorch
ort_model = ORTModelForSequenceClassification.from_pretrained("/models/sentiment-onnx/")
```

### 13.3 Batching for throughput

A model serving 1 request at a time wastes the GPU. Batch incoming requests:

```python
import asyncio
from collections import deque

class Batcher:
    def __init__(self, max_batch=8, max_wait_ms=10):
        self.queue = deque()
        self.max_batch, self.max_wait = max_batch, max_wait_ms / 1000

    async def predict(self, text: str):
        future = asyncio.get_event_loop().create_future()
        self.queue.append((text, future))
        return await future

    async def run(self):
        while True:
            await asyncio.sleep(self.max_wait)
            if not self.queue: continue
            batch = [self.queue.popleft() for _ in range(min(self.max_batch, len(self.queue)))]
            texts = [b[0] for b in batch]
            results = self._predict_batch(texts)
            for (_, future), result in zip(batch, results):
                future.set_result(result)
```

Tools that do this automatically: **Triton Inference Server**, **Ray Serve**, **Text Embeddings Inference (TEI)** (HF's optimized server for embeddings), **vLLM** (Module 10 for generation).

### 13.4 Embedding-server pattern

For embedding pipelines:
- One service hosts the embedding model with batching.
- Producers send texts; receive vectors; persist to a vector DB.
- Independently scalable.

HF's **TEI** (Text Embeddings Inference) is a drop-in: handles batching, ONNX, monitoring.

---

## 14. Anti-patterns

| Anti-pattern | Right way |
|---|---|
| Loading a tokenizer from one checkpoint and a model from another | Always pair them; same checkpoint name |
| Manual padding in Python | `tokenizer(..., padding=True, truncation=True)` |
| Truncating at a fixed character count | Tokenize first; cap by token count |
| Forgetting `attention_mask` | Always pass — padding tokens otherwise contribute to attention |
| Embedding without `normalize_embeddings=True` | Then using cosine sim later — normalize once |
| Using model.encode without batching | Always pass `batch_size=64` for throughput |
| Mixing query and doc with the same prompt prefix | Asymmetric retrieval needs different prefixes per side |
| Re-embedding documents on every change | Cache by doc hash; invalidate only on doc change |
| Fine-tuning at full LR (1e-3) on transformers | Use 2e-5 to 5e-5 for fine-tuning |
| No warmup on transformer training | Always 10% warmup + cosine |
| Forgetting `ignore_mismatched_sizes=True` when changing num_labels | Add it; the head is randomly initialized |
| Vanilla fp32 fine-tuning on Ampere/H100 | bf16 for free 2× speedup |
| Reading raw audio without resampling | Always check the model's expected sample rate |
| Storing embeddings as float64 | float32 (or float16/bf16) — half the storage |
| Cosine similarity on un-normalized vectors | Normalize once at write; use dot product to query |
| Embedding model and downstream classifier mismatched | Pin embedding model version; recompute on upgrade |
| Brute-force kNN on 10M+ vectors | HNSW / IVF / managed vector DB |
| Saving with pickle | Use safetensors (HF default since 4.30+) |
| Trust-remote-code on a random model | Read the source first; the option name is a warning |
| One-off tokenization at serve time on every call | Pre-tokenize where possible; cache common prompts |
| `max_length=512` on classification of long docs | Either use a long-context model or chunk + vote |

---

## 15. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 4 tokenization (P1–P4), 4 HF basics (P5–P8), 6 encoder fine-tuning (P9–P14), 5 embeddings/retrieval (P15–P19), 6 vision (P20–P25), 3 detection/segmentation (P26–P28), 2 audio (P29–P30), 3 multimodal (P31–P33), 3 eval/deploy (P34–P36).

---

### Problem 1 — Tokenize a sentence and inspect the IDs

**Solution.**
```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("bert-base-uncased")

text = "Tokenization is the bedrock."
out = tok(text, return_tensors="pt")
print(out["input_ids"])
print(tok.convert_ids_to_tokens(out["input_ids"][0]))
# ['[CLS]', 'token', '##ization', 'is', 'the', 'bed', '##rock', '.', '[SEP]']
```

**Real-world.** Always inspect tokens for new languages/domains. "Pre" + "##process" + "##ing" is fine; if your domain term is split into 5 tokens, accuracy will suffer — consider domain pretraining or vocabulary extension.

**Follow-ups.** Compare BERT WordPiece vs Llama BPE on the same text. Token counting for context budgets.

---

### Problem 2 — Pad and truncate a batch correctly

**Statement.** Tokenize a list of sentences with mixed lengths; produce a tensor batch ready for the model.

**Solution.**
```python
texts = ["short", "this is a much longer sentence to encode", "medium length text"]
batch = tok(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
print(batch["input_ids"].shape)        # (3, max_in_batch)
print(batch["attention_mask"].sum(dim=1))   # actual lengths excl. pad
```

**Why `padding=True` (not `max_length`).** Padding to the longest in batch saves compute. Padding to `max_length=512` always wastes ~80%.

**Follow-ups.** `DataCollatorWithPadding` for dynamic per-batch padding in Trainer/DataLoader. Length-bucketing for further speedup.

---

### Problem 3 — Token-word alignment for NER

**Statement.** Given a sentence pre-tokenized into words and per-word labels, produce per-subword labels with `-100` for non-first-subwords and special tokens.

**Solution.**
```python
words  = ["Hugging", "Face", "is", "in", "Paris"]
tags   = [3,         3,      0,    0,    7]                    # B-ORG, I-ORG, O, O, B-LOC

enc = tok(words, is_split_into_words=True, return_tensors="pt")
word_ids = enc.word_ids(0)
labels, prev = [], None
for w in word_ids:
    if w is None:
        labels.append(-100)
    elif w != prev:
        labels.append(tags[w])
    else:
        labels.append(-100)            # subsequent subwords
    prev = w
print(labels)
```

**Why -100.** PyTorch's `CrossEntropyLoss(ignore_index=-100)` skips them — loss is computed only on the first subword of each word.

**Real-world.** Standard pattern in every HF NER fine-tune. The HF NLP course's NER chapter is the canonical reference.

**Follow-ups.** Label every subword with the same tag (alternative scheme, less common). Handle the BIO scheme (B-tag → I-tag).

---

### Problem 4 — Use the fast tokenizer's offset mapping

**Statement.** Find the **character span** in the original text corresponding to each token.

**Solution.**
```python
text = "Apple Inc. was founded in 1976."
enc = tok(text, return_offsets_mapping=True, return_tensors="pt")
toks = tok.convert_ids_to_tokens(enc["input_ids"][0])
for t, (s, e) in zip(toks, enc["offset_mapping"][0].tolist()):
    print(f"{t!r:>15} ↔ {text[s:e]!r}")
```

`(0, 0)` offset = special token (`[CLS]`/`[SEP]`).

**Real-world.** Critical for QA (mapping predicted answer-token positions back to text), highlight-the-evidence UIs, and post-hoc explainability.

**Follow-ups.** Map tokens back to PDF coordinates (combined with `pdfplumber`).

---

### Problem 5 — Load a model and run a forward pass

**Solution.**
```python
from transformers import AutoTokenizer, AutoModel
import torch

ck = "bert-base-uncased"
tok = AutoTokenizer.from_pretrained(ck)
model = AutoModel.from_pretrained(ck).eval()

inputs = tok("Hello world", return_tensors="pt")
with torch.no_grad():
    out = model(**inputs)
print(out.last_hidden_state.shape)         # (1, seq_len, 768)
print(out.pooler_output.shape)              # (1, 768)
```

**Last hidden state vs pooler output.** Pooler is `[CLS]` representation passed through a tanh layer (BERT specific). For embeddings, `last_hidden_state[:, 0]` (raw CLS) or mean pooling is more common.

**Follow-ups.** Using `output_hidden_states=True` to get all layers. `output_attentions=True` for visualization.

---

### Problem 6 — Use AutoModelForSequenceClassification

**Solution.**
```python
from transformers import AutoModelForSequenceClassification
import torch

model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased", num_labels=3
).eval()

inputs = tok("Service was great", return_tensors="pt")
with torch.no_grad():
    logits = model(**inputs).logits
probs = torch.softmax(logits, dim=-1)
print(probs)            # (1, 3)
```

**Why.** `AutoModelForSequenceClassification` adds a randomly initialized linear head over the encoder. You then fine-tune.

**Follow-ups.** `id2label` / `label2id` config for human-readable labels.

---

### Problem 7 — Use the pipeline API

**Solution.**
```python
from transformers import pipeline

clf = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print(clf("I love Hugging Face."))
# [{'label': 'POSITIVE', 'score': 0.999...}]

zsl = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
print(zsl("Apple just released a new MacBook.",
            candidate_labels=["technology", "sports", "politics"]))
```

**Real-world.** Pipelines for prototypes and one-off jobs. Don't use for production high-throughput — they batch poorly.

**Follow-ups.** `pipeline(..., device=0)` to put on GPU. `pipeline(..., batch_size=32)` for throughput.

---

### Problem 8 — Load and tokenize a dataset

**Solution.**
```python
from datasets import load_dataset

ds = load_dataset("imdb")
print(ds)                           # DatasetDict
print(ds["train"][0]["label"], ds["train"][0]["text"][:100])

def tokenize_fn(batch):
    return tok(batch["text"], truncation=True, max_length=256)

ds_tok = ds.map(tokenize_fn, batched=True, remove_columns=["text"])
ds_tok = ds_tok.with_format("torch")
print(ds_tok["train"][0].keys())    # input_ids, attention_mask, label
```

**Why batched=True.** Calls `tokenize_fn` on a list of samples — much faster than per-sample.

**Real-world.** `load_dataset` caches in `~/.cache/huggingface/datasets/`. For your own data: `Dataset.from_pandas(df)`, `Dataset.from_dict({...})`, or `load_dataset("json", data_files=...)`.

**Follow-ups.** Streaming mode for huge datasets (`load_dataset(..., streaming=True)`). Filtering and shuffling.

---

### Problem 9 — Fine-tune DistilBERT for binary classification

**Solution.**
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, \
                         TrainingArguments, Trainer, DataCollatorWithPadding
from datasets import load_dataset
import numpy as np
import evaluate as hf_evaluate

ck = "distilbert-base-uncased"
tok = AutoTokenizer.from_pretrained(ck)
model = AutoModelForSequenceClassification.from_pretrained(ck, num_labels=2)

ds = load_dataset("imdb")
def tokenize_fn(b): return tok(b["text"], truncation=True, max_length=256)
ds_tok = ds.map(tokenize_fn, batched=True, remove_columns=["text"])
collator = DataCollatorWithPadding(tokenizer=tok)

acc_metric = hf_evaluate.load("accuracy")
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    return acc_metric.compute(predictions=logits.argmax(-1), references=labels)

args = TrainingArguments(
    output_dir="ckpts/imdb-clf",
    learning_rate=2e-5, weight_decay=0.01,
    per_device_train_batch_size=32, per_device_eval_batch_size=64,
    num_train_epochs=2, warmup_ratio=0.1,
    eval_strategy="epoch", save_strategy="epoch",
    load_best_model_at_end=True, metric_for_best_model="accuracy",
    bf16=True, logging_steps=100, report_to="none",
)

trainer = Trainer(model=model, args=args,
                   train_dataset=ds_tok["train"], eval_dataset=ds_tok["test"],
                   tokenizer=tok, data_collator=collator,
                   compute_metrics=compute_metrics)
trainer.train()
trainer.save_model("imdb-clf/")
```

**Real-world.** This template handles 80% of NLP classification problems. Expected: ~92-93% accuracy on IMDB in <10 min on a single GPU.

**Follow-ups.** Add early stopping callback. Hyperparameter sweep with Optuna integration. Handle imbalance with weighted loss.

---

### Problem 10 — Manual training loop (for control)

**Solution.** (See §5.1 for full code.) The 10-line loop:
```python
for epoch in range(epochs):
    model.train()
    for batch in train_loader:
        batch = {k: v.to(device) for k, v in batch.items()}
        optimizer.zero_grad(set_to_none=True)
        out = model(**batch)
        out.loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step(); scheduler.step()
```

**When to prefer over Trainer:** custom losses, multi-task heads, complex evaluation, or production-style modular code. **When to prefer Trainer:** rapid iteration, multi-GPU/precision out of the box, want logging/checkpointing for free.

---

### Problem 11 — Token classification (NER) end-to-end

**Solution.**
```python
from transformers import AutoModelForTokenClassification, DataCollatorForTokenClassification
from datasets import load_dataset

ds = load_dataset("conll2003")            # tokens, ner_tags
labels = ds["train"].features["ner_tags"].feature.names
id2label = {i: l for i, l in enumerate(labels)}
label2id = {l: i for i, l in id2label.items()}

ck = "distilbert-base-uncased"
tok = AutoTokenizer.from_pretrained(ck)
model = AutoModelForTokenClassification.from_pretrained(
    ck, num_labels=len(labels), id2label=id2label, label2id=label2id
)

def tokenize_align(examples):
    enc = tok(examples["tokens"], is_split_into_words=True, truncation=True, max_length=128)
    new_labels = []
    for i, lbl in enumerate(examples["ner_tags"]):
        wids = enc.word_ids(i); prev = None; row = []
        for w in wids:
            row.append(-100 if w is None or w == prev else lbl[w])
            prev = w
        new_labels.append(row)
    enc["labels"] = new_labels
    return enc

ds_tok = ds.map(tokenize_align, batched=True, remove_columns=ds["train"].column_names)
collator = DataCollatorForTokenClassification(tok)

# Trainer + compute_metrics with seqeval — see §12.1
```

**Real-world.** Production NER for entities/events on call transcripts, support tickets, contracts. Competitive accuracy out of the box; specialize via fine-tuning on your taxonomy.

**Follow-ups.** Convert predictions back to text spans for highlighting. Multi-task learning (NER + classification heads).

---

### Problem 12 — Multilingual classification with XLM-RoBERTa

**Solution.**
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

ck = "FacebookAI/xlm-roberta-base"        # 100+ languages
tok = AutoTokenizer.from_pretrained(ck)
model = AutoModelForSequenceClassification.from_pretrained(ck, num_labels=3)
# fine-tune the same way as monolingual; tokenizer handles 100+ languages
```

**Why XLM-R / mBERT.** A single model serves many languages. Often beats per-language models when training data per language is small.

**Real-world.** Standard for global products. Trade-off: slightly weaker per-language than a dedicated model trained on that language alone — but operationally simpler.

**Follow-ups.** XLM-R-large for higher quality; mDeBERTa for stronger multilingual baseline.

---

### Problem 13 — Handle class imbalance in fine-tuning

**Solution (weighted loss).**
```python
import torch
from torch import nn
from transformers import Trainer

class WeightedTrainer(Trainer):
    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        loss = nn.CrossEntropyLoss(weight=self.class_weights.to(outputs.logits.device))(
            outputs.logits, labels
        )
        return (loss, outputs) if return_outputs else loss

# class_weights = total / (n_classes * counts)
counts = torch.bincount(torch.tensor(ds_tok["train"]["label"]))
weights = counts.sum() / (len(counts) * counts.float())
trainer = WeightedTrainer(..., class_weights=weights)
```

**Real-world.** Cleanest path for imbalanced text classification (e.g., 95/5 spam/ham).

**Follow-ups.** Focal loss for extreme imbalance. Sampler-based oversampling.

---

### Problem 14 — Gradient checkpointing for fine-tuning a big model on a small GPU

**Solution.**
```python
model.gradient_checkpointing_enable()           # standard HF call
model.config.use_cache = False                  # required during training; re-enable for generation
```

In TrainingArguments: `gradient_checkpointing=True`. Roughly halves memory at the cost of ~30% slower training.

**Real-world.** Essential for fine-tuning 7B-class generation models on a single 24GB GPU.

**Follow-ups.** Combine with bf16 + gradient accumulation. PEFT/LoRA — Module 10.

---

### Problem 15 — Compute embeddings for a dataset

**Solution.**
```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-base-en-v1.5")
sentences = ["I love pizza", "I enjoy cycling", "Pizza is delicious"]

emb = model.encode(sentences, normalize_embeddings=True, batch_size=32, show_progress_bar=True)
print(emb.shape, np.linalg.norm(emb, axis=1))         # (3, 768), all 1.0

sim = emb @ emb.T                                      # cosine since normalized
print(sim.round(3))
```

**Real-world.** Pre-compute once, store in a vector DB or parquet on S3. Recompute only on model upgrade.

**Follow-ups.** Float16 embeddings to halve storage. Batch on GPU for 100× speedup vs CPU.

---

### Problem 16 — Build a brute-force semantic search

**Solution.**
```python
import numpy as np

class SemanticSearch:
    def __init__(self, model_name="BAAI/bge-base-en-v1.5"):
        self.model = SentenceTransformer(model_name)
        self.docs = []
        self.embs = None
    def add(self, docs):
        self.docs.extend(docs)
        self.embs = self.model.encode(self.docs, normalize_embeddings=True, batch_size=64)
    def search(self, query, k=5):
        q = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.embs @ q
        idx = np.argpartition(-scores, k)[:k]
        idx = idx[np.argsort(-scores[idx])]
        return [(self.docs[i], float(scores[i])) for i in idx]

ss = SemanticSearch()
ss.add(["pizza is great", "I love coding", "the sky is blue"])
print(ss.search("food preferences", k=2))
```

**Real-world.** Fine for ≤100k docs. Beyond that, use a real vector index.

**Follow-ups.** HNSW index. Filtering by metadata (date, category) before similarity.

---

### Problem 17 — Use a faiss HNSW index

**Solution.**
```python
# pip install faiss-cpu
import faiss
import numpy as np

dim = 768
index = faiss.IndexHNSWFlat(dim, 32)        # M=32 (graph degree)
index.hnsw.efConstruction = 200             # build quality
index.hnsw.efSearch       = 64              # query quality

embs = ss.embs.astype("float32")
index.add(embs)

q = np.random.randn(1, dim).astype("float32")
q /= np.linalg.norm(q)                       # normalize for cosine
D, I = index.search(q, k=10)
```

**Why HNSW.** Sub-linear search on millions of vectors. ~5–20× faster than IVF for similar recall.

**Real-world.** Standard for embedded vector search up to 100M vectors. Beyond: managed vector DBs.

**Follow-ups.** PQ compression for less memory. Filter-aware indexes (Qdrant, Weaviate).

---

### Problem 18 — Ranking with a cross-encoder

**Solution.**
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-base")

candidates = [
    "Pizza dough recipe with yeast and flour.",
    "How to fix a flat bicycle tire.",
    "Best Italian dishes including pizza.",
]
query = "italian pizza"
pairs = [(query, c) for c in candidates]
scores = reranker.predict(pairs)
ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
for doc, s in ranked: print(f"{s:.3f}: {doc}")
```

**Real-world.** The standard retrieval pipeline: bi-encoder retrieval → cross-encoder rerank → top-K. Significantly better quality than embedding alone.

**Follow-ups.** Distillation: train a smaller student to mimic the reranker for faster inference.

---

### Problem 19 — Asymmetric retrieval prefixes

**Statement.** BGE models work better when query and doc are prefixed differently. Demo.

**Solution.**
```python
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

raw_queries = ["how to make pizza", "best chess opening"]
raw_docs    = ["pizza dough recipe", "Sicilian defense in chess"]

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
queries = [QUERY_PREFIX + q for q in raw_queries]

q_emb = model.encode(queries,  normalize_embeddings=True)
d_emb = model.encode(raw_docs, normalize_embeddings=True)
print(q_emb @ d_emb.T)
```

**Why.** BGE was trained with a query prefix; using it gives ~5–15% recall@K improvement.

**Real-world.** Always check the model card for prefixes. Different models have different prefixes ("query: ..." for E5, "passage: ..." etc.).

**Follow-ups.** Fine-tune the embedding model on your own (query, positive_doc) pairs for domain-specific gains.

---

### Problem 20 — Image classification with a pretrained model

**Solution.**
```python
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

ck = "google/vit-base-patch16-224"
proc = AutoImageProcessor.from_pretrained(ck)
model = AutoModelForImageClassification.from_pretrained(ck).eval()

img = Image.open("photo.jpg").convert("RGB")
inputs = proc(images=img, return_tensors="pt")
with torch.no_grad():
    logits = model(**inputs).logits
top = logits.argmax(-1).item()
print(model.config.id2label[top])
```

**Real-world.** Zero-shot ImageNet classification works for most natural images. For your domain, fine-tune.

**Follow-ups.** Top-5 predictions with `torch.topk`. Confidence calibration for production thresholding.

---

### Problem 21 — Fine-tune ViT on a small dataset

**Solution.**
```python
from transformers import AutoModelForImageClassification, TrainingArguments, Trainer
from torchvision.datasets import CIFAR10
from torchvision import transforms as T

train_tfm = T.Compose([
    T.Resize(256), T.RandomResizedCrop(224), T.RandomHorizontalFlip(),
    T.ToTensor(), T.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
])
val_tfm = T.Compose([
    T.Resize(256), T.CenterCrop(224),
    T.ToTensor(), T.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
])

class CIFARForViT(torch.utils.data.Dataset):
    def __init__(self, ds, tfm): self.ds, self.tfm = ds, tfm
    def __len__(self): return len(self.ds)
    def __getitem__(self, i):
        img, label = self.ds[i]
        return {"pixel_values": self.tfm(img), "labels": label}

train_ds = CIFARForViT(CIFAR10("./data", train=True,  download=True), train_tfm)
val_ds   = CIFARForViT(CIFAR10("./data", train=False, download=True), val_tfm)

model = AutoModelForImageClassification.from_pretrained(
    "google/vit-base-patch16-224",
    num_labels=10, ignore_mismatched_sizes=True,
)

args = TrainingArguments(output_dir="vit-cifar", learning_rate=5e-5,
    per_device_train_batch_size=32, num_train_epochs=3, bf16=True,
    eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True)

trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds)
trainer.train()
```

**Real-world.** ~96% on CIFAR-10 in 3 epochs on a single A10. Stronger augmentation (CutMix/Mixup) pushes to ~98%.

**Follow-ups.** Two-stage train (head only → unfreeze). DINOv2 backbone.

---

### Problem 22 — DINOv2 frozen features + linear probe

**Solution.**
```python
from transformers import AutoImageProcessor, AutoModel
import torch.nn as nn
import torch

proc = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
encoder = AutoModel.from_pretrained("facebook/dinov2-base").eval()
for p in encoder.parameters(): p.requires_grad = False

class LinearProbe(nn.Module):
    def __init__(self, encoder, num_classes):
        super().__init__()
        self.enc, self.head = encoder, nn.Linear(encoder.config.hidden_size, num_classes)
    @torch.inference_mode()
    def features(self, x):
        return self.enc(pixel_values=x).last_hidden_state[:, 0]
    def forward(self, x):
        return self.head(self.features(x))

probe = LinearProbe(encoder, num_classes=10)
# train only probe.head — fast and parameter-efficient
```

**Real-world.** With 100-1000 labels per class, a linear probe on DINOv2 often hits within 5% of full fine-tuning at 1% of compute.

**Follow-ups.** kNN classification on DINOv2 features (no training at all). Multi-class probe with class-balanced sampling.

---

### Problem 23 — Zero-shot image classification with CLIP

**Solution.**
```python
from transformers import AutoProcessor, AutoModel
from PIL import Image
import torch

proc  = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = AutoModel.from_pretrained("openai/clip-vit-base-patch32").eval()

img = Image.open("photo.jpg")
labels = ["a photo of a dog", "a photo of a cat", "a photo of a car"]
inputs = proc(text=labels, images=img, return_tensors="pt", padding=True)

with torch.no_grad():
    out = model(**inputs)
probs = out.logits_per_image.softmax(-1).flatten()
for l, p in zip(labels, probs.tolist()):
    print(f"{l}: {p:.3f}")
```

**Real-world.** When categories are dynamic (think "tag any photo with one of these 1000 user-defined labels"), CLIP avoids retraining for each new label set.

**Follow-ups.** Improving prompts ("a high-quality photo of a {label}, well-lit"). SigLIP for stronger zero-shot.

---

### Problem 24 — Image-text retrieval with CLIP

**Statement.** Given a corpus of images and a text query, return the top-K most relevant images.

**Solution.**
```python
import torch

# pre-compute image embeddings
img_embs = []
for img in image_corpus:
    inp = proc(images=img, return_tensors="pt")
    with torch.no_grad():
        e = model.get_image_features(**inp)
    img_embs.append(e / e.norm(dim=-1, keepdim=True))
img_embs = torch.cat(img_embs)               # (N, dim)

# query
def search(text, k=5):
    inp = proc(text=text, return_tensors="pt", padding=True)
    with torch.no_grad():
        q = model.get_text_features(**inp)
    q = q / q.norm(dim=-1, keepdim=True)
    sims = (img_embs @ q.T).flatten()
    return sims.topk(k).indices.tolist()
```

**Real-world.** Image search ("find dog photos"), product search by description, content moderation flagging.

**Follow-ups.** Fine-tune CLIP on (image, caption) pairs for your domain. Hybrid lexical + CLIP for product search.

---

### Problem 25 — Strong vision augmentation pipeline

**Solution.**
```python
from torchvision import transforms as T
from torchvision.transforms import RandAugment

train_tfm = T.Compose([
    T.Resize(256),
    T.RandomResizedCrop(224, scale=(0.8, 1.0)),
    T.RandomHorizontalFlip(),
    RandAugment(num_ops=2, magnitude=9),
    T.ToTensor(),
    T.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    T.RandomErasing(p=0.25),
])
```

`RandAugment` automatically applies N strong augmentations from a curated bank. Modern ViTs assume this level of augmentation; without it, you'll overfit.

**Real-world.** CutMix and Mixup go further but require collator-level changes (mix two samples and their labels). For most fine-tunes, RandAugment + RandomErasing gets you 90% of the benefit.

**Follow-ups.** Implement Mixup / CutMix collators. AutoAugment for finding policies on small datasets.

---

### Problem 26 — Object detection with YOLO

**Solution.**
```python
# pip install ultralytics
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
results = model("photo.jpg", conf=0.5)
for r in results:
    print(r.names)               # class names
    for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
        print(f"class={int(cls)}: {r.names[int(cls)]}, conf={float(conf):.2f}, box={box.tolist()}")
    r.save("out.jpg")            # save annotated image
```

**Real-world.** YOLO is the practitioner's choice for real-time detection. Fine-tunes well on custom data with `model.train(data="data.yaml", epochs=50)`.

**Follow-ups.** Convert custom dataset to YOLO format. Train + export to ONNX for production. Tracking with `model.track`.

---

### Problem 27 — Open-vocabulary detection with Grounding DINO

**Solution.**
```python
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
import torch

ck = "IDEA-Research/grounding-dino-tiny"
proc = AutoProcessor.from_pretrained(ck)
model = AutoModelForZeroShotObjectDetection.from_pretrained(ck).eval()

img = Image.open("photo.jpg").convert("RGB")
text = "a person. a dog. a chair."        # text prompts separated by periods
inputs = proc(images=img, text=text, return_tensors="pt")

with torch.no_grad():
    outputs = model(**inputs)

results = proc.post_process_grounded_object_detection(
    outputs, inputs["input_ids"],
    threshold=0.4, text_threshold=0.3,
    target_sizes=[img.size[::-1]],
)[0]
print(results["labels"], results["scores"], results["boxes"])
```

**Real-world.** Detect arbitrary objects without training when zero-shot quality is enough. Ideal for prototyping or when label sets evolve.

**Follow-ups.** Pair with SAM for "find object → segment object" pipelines.

---

### Problem 28 — Segment with SAM 2

**Solution.**
```python
from transformers import AutoProcessor, AutoModel
import torch
from PIL import Image

ck = "facebook/sam2-hiera-base-plus"
proc = AutoProcessor.from_pretrained(ck)
model = AutoModel.from_pretrained(ck).eval()

img = Image.open("photo.jpg").convert("RGB")
input_points = [[[500, 400]]]               # click coordinates (x, y)
inputs = proc(images=img, input_points=input_points, return_tensors="pt")

with torch.no_grad():
    out = model(**inputs)
masks = proc.post_process_masks(out.pred_masks.cpu(),
                                 inputs["original_sizes"], inputs["reshaped_input_sizes"])
# masks[0]: tensor of shape (n_predictions, H, W)
```

**Real-world.** "Segment by click/box" for image editing apps. Combined with Grounding DINO: "find the dog and segment it" — full open-vocabulary instance segmentation.

**Follow-ups.** Automatic mask generator (no prompts). Video segmentation with SAM 2's tracking.

---

### Problem 29 — Transcribe audio with Whisper

**Solution.**
```python
from transformers import pipeline

pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-large-v3-turbo",
    chunk_length_s=30,
    torch_dtype=torch.float16,
    device=0 if torch.cuda.is_available() else -1,
)

result = pipe("audio.wav", return_timestamps=True,
               generate_kwargs={"language": "english", "task": "transcribe"})
print(result["text"])
for chunk in result["chunks"]:
    print(chunk["timestamp"], chunk["text"])
```

**Real-world.** ASR is essentially a solved problem with Whisper. Fine-tune only for niche domains (medical, accents) where it underperforms.

**Follow-ups.** Translate-to-English with `task="translate"`. Speaker diarization (combine Whisper with `pyannote.audio`).

---

### Problem 30 — Build audio embeddings for similarity search

**Solution.**
```python
from transformers import AutoFeatureExtractor, AutoModel
import torchaudio
import torch

ck = "facebook/wav2vec2-base"
feat = AutoFeatureExtractor.from_pretrained(ck)
model = AutoModel.from_pretrained(ck).eval()

def embed_audio(path):
    wav, sr = torchaudio.load(path)
    if sr != 16000:
        wav = torchaudio.functional.resample(wav, sr, 16000)
    if wav.shape[0] > 1: wav = wav.mean(dim=0, keepdim=True)         # mono
    inp = feat(wav.squeeze().numpy(), sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        out = model(**inp)
    return out.last_hidden_state.mean(dim=1).squeeze()    # mean-pool to single vector
```

**Real-world.** Audio fingerprinting, music similarity, speaker verification (with appropriate models).

**Follow-ups.** CLAP for text-audio retrieval. Specialized models per domain (music: MERT; speech: Wav2Vec2; environmental: PANNs).

---

### Problem 31 — Image captioning with a VLM

**Solution.**
```python
from transformers import AutoProcessor, AutoModelForVision2Seq
from PIL import Image
import torch

ck = "HuggingFaceTB/SmolVLM2-2.2B-Instruct"
proc = AutoProcessor.from_pretrained(ck)
model = AutoModelForVision2Seq.from_pretrained(ck, torch_dtype=torch.bfloat16).eval()

img = Image.open("photo.jpg").convert("RGB")
messages = [{"role":"user","content":[
    {"type":"image","image":img},
    {"type":"text", "text":"Describe this image in one sentence."},
]}]
inputs = proc.apply_chat_template(messages, add_generation_prompt=True,
                                    tokenize=True, return_dict=True, return_tensors="pt")

with torch.inference_mode():
    out_ids = model.generate(**inputs, max_new_tokens=100)
print(proc.decode(out_ids[0], skip_special_tokens=True))
```

**Real-world.** Alt-text generation for accessibility, content moderation with reasoning, document understanding. For high-throughput, run a hosted VLM API instead of self-hosting.

**Follow-ups.** Visual question answering ("How many people are in this image?"). OCR-light tasks where strict accuracy isn't required.

---

### Problem 32 — Visual question answering with a VLM

**Solution.** Same code as P31 with different prompt:
```python
messages = [{"role":"user","content":[
    {"type":"image","image":img},
    {"type":"text", "text":"How many people are visible in this image? Answer with a single integer."},
]}]
```

**Caveat.** VLMs hallucinate. For "is there a defect on this part?" — combine VLM with a domain-specific classifier; don't trust VLM alone for safety-critical decisions.

**Follow-ups.** Constrained decoding for structured output. Ensembling multiple VLMs and a classifier.

---

### Problem 33 — Document understanding (OCR + VLM)

**Statement.** Extract structured fields from an invoice image.

**Pipeline:**
1. **OCR** — `pytesseract`, `EasyOCR`, or PaddleOCR for raw text + bounding boxes.
2. **Layout-aware extraction** — `LayoutLMv3` for token+layout joint reasoning, or feed image + OCR text to a VLM.
3. **Structured output** — prompt VLM to emit JSON fields ("invoice_number", "total", "date").

For complex documents, **specialized layout models (Donut, LayoutLMv3, Pix2Struct)** beat general-purpose VLMs on price-extraction-style tasks.

**Real-world.** Production invoice/form processing usually combines OCR + a fine-tuned LayoutLM model with hand-validation for low-confidence fields.

**Follow-ups.** Fine-tune Donut on your forms. Layout aware embedding for downstream classification.

---

### Problem 34 — NER evaluation with seqeval

**Solution.**
```python
import evaluate as hf_evaluate
import numpy as np

seqeval = hf_evaluate.load("seqeval")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    true_labels  = [[id2label[l] for l in lab if l != -100] for lab in labels]
    true_preds   = [[id2label[p] for p, l in zip(pr, lab) if l != -100]
                     for pr, lab in zip(preds, labels)]
    res = seqeval.compute(predictions=true_preds, references=true_labels)
    return {"precision": res["overall_precision"], "recall": res["overall_recall"],
            "f1": res["overall_f1"], "accuracy": res["overall_accuracy"]}
```

**Why entity-level F1.** Token-level metrics over-weight common O-tags and miss whole-entity structure. seqeval measures exact-span matches (B-PER followed by I-PER must both be predicted as the same span).

**Follow-ups.** Per-entity-type breakdown. Confusion matrix for NER (which entity types get confused).

---

### Problem 35 — Retrieval evaluation (Recall@K, MRR)

**Solution.**
```python
import numpy as np

def recall_at_k(retrieved, relevant, k):
    """retrieved: list of doc IDs (top-k order). relevant: set of true relevant IDs."""
    return len(set(retrieved[:k]) & relevant) / max(1, len(relevant))

def mrr(retrieved, relevant):
    for i, doc in enumerate(retrieved, 1):
        if doc in relevant: return 1.0 / i
    return 0.0

# evaluate over a labeled set
recall_5s, mrrs = [], []
for q, rel in eval_queries:
    top = retrieve(q, k=10)         # your retriever's output
    recall_5s.append(recall_at_k(top, set(rel), 5))
    mrrs.append(mrr(top, set(rel)))
print("Recall@5:", np.mean(recall_5s), "MRR:", np.mean(mrrs))
```

**Real-world.** Even 100-500 labeled (query, relevant_doc) pairs give you a strong eval. Re-evaluate after every model upgrade.

**Follow-ups.** nDCG@K with graded relevance. Offline + online (A/B) eval combination.

---

### Problem 36 — Deploy a fine-tuned classifier as a FastAPI service with batching

**Solution (single-file).**
```python
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = FastAPI()

class Req(BaseModel): text: str

class Batcher:
    def __init__(self, model_path, max_batch=8, max_wait_ms=20):
        self.tok = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).eval()
        self.queue = asyncio.Queue()
        self.max_batch, self.max_wait = max_batch, max_wait_ms / 1000

    async def predict(self, text):
        f = asyncio.get_event_loop().create_future()
        await self.queue.put((text, f))
        return await f

    async def run(self):
        while True:
            await asyncio.sleep(self.max_wait)
            batch = []
            while not self.queue.empty() and len(batch) < self.max_batch:
                batch.append(await self.queue.get())
            if not batch: continue
            texts = [t for t, _ in batch]
            inputs = self.tok(texts, padding=True, truncation=True, max_length=256, return_tensors="pt")
            with torch.no_grad():
                logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1).tolist()
            for (_, f), p in zip(batch, probs):
                f.set_result(p)

batcher = Batcher("/models/sentiment/")

@app.on_event("startup")
async def start_batcher():
    asyncio.create_task(batcher.run())

@app.post("/classify")
async def classify(req: Req):
    probs = await batcher.predict(req.text)
    return {"probs": probs}
```

**Real-world.** Batching gets you 5-20× throughput improvement on GPU. The above is a minimal version; **Triton Inference Server** and **HF Text Embeddings Inference** do this professionally.

**Follow-ups.** Drop in ONNX runtime for further CPU speedup. Add per-tenant rate limits (Module 4 P10).

---

## 16. Three mini-projects

### Mini-project A — A multilingual content moderation classifier
Take a public moderation dataset (e.g., Jigsaw multilingual toxicity). Fine-tune `xlm-roberta-base` with a Trainer. Calibrate probabilities. Pick thresholds per language. Build a FastAPI service with batching. Latency target: p95 < 100ms on CPU per request. Document languages where the model struggles and propose per-language fixes.

**Skills exercised:** §2-§5, §12-§13. Standard NLP production pattern.

### Mini-project B — A semantic search over a code/docs corpus
Build a search service over your team's docs (or open-source docs). Pipeline: text chunker → BGE embeddings → faiss HNSW index → cross-encoder rerank → FastAPI endpoint. Add metadata filters (source, date). Eval with 50-100 query/relevant-doc pairs. Compare BM25 baseline vs embeddings vs hybrid (BM25 + embeddings).

**Skills exercised:** §6, §12-§13. Foundation for RAG (Module 10).

### Mini-project C — A vision pipeline: zero-shot detection + segmentation + caption
Combine Grounding DINO (find objects by text) → SAM 2 (segment them) → SmolVLM (describe each segment). Build a "describe each object in this image" service. Compare against a fine-tuned single-class detector + classifier; document where each approach wins.

**Skills exercised:** §8, §9, §11. Multi-model orchestration.

---

## 17. Real-world usage map

| Concept | Where it returns later |
|---|---|
| Tokenization | Module 10 (LLM context budgets), Module 13 (LLM cost = tokens) |
| HF Trainer pattern | Module 10 fine-tuning (full + LoRA), Module 12 production training |
| Sentence embeddings | Module 10 RAG retrieval; Module 11 agent tool selection |
| Cross-encoder reranking | Module 10 RAG quality boost |
| `safetensors` format | Standard for all model artifacts going forward |
| `accelerate` | Module 10 distributed fine-tuning |
| `peft` (LoRA) | Module 10 — covered in depth |
| CLIP / SigLIP | Module 10 multimodal RAG |
| SAM-style prompted models | Agent vision tools (Module 11) |
| Whisper | Voice-input agents (Module 11) |
| HF datasets streaming | Module 10 large-scale fine-tuning |

---

## 18. Interview pitfalls — what NOT to say

- **"I'll write my own tokenizer."** Don't. Use the one paired with the model. Mismatches are silent killers.
- **"BERT is small enough to fit."** Quantify — at fp32, BERT-base = 440 MB; at fp16/bf16 = 220 MB. Know your numbers.
- **"I'll use cosine similarity manually with `np.dot`."** Fine for normalized vectors, but say so. Otherwise normalize at write time.
- **"I'll re-embed every query."** Yes for the query, but documents should be cached.
- **"More training data is always better."** With pretrained models, sometimes you only need 1k labeled examples. Don't gather 100k unnecessarily.
- **"`pipeline()` for production."** It works, but doesn't batch well. For throughput, use the model directly with batched inputs.
- **"I evaluated on accuracy."** For NER/retrieval/detection, accuracy is wrong. Use entity-F1, recall@K, mAP.
- **"I freeze the entire backbone."** Fine for limited data; if you have 100k+ labels, full fine-tune with differential LR is better.
- **"I'll build my own RAG with faiss."** OK for prototypes. For production, vector DBs handle metadata, replication, hybrid search out of the box.
- **"CLIP is a classification model."** It's a *contrastive* model — it scores image-text alignment. Zero-shot classification is a useful application, not its core capability.
- **"I trained for 10 epochs."** For fine-tuning encoders, 2-4 epochs is usually optimal. More overfits.
- **"Tokenization is fine, the model just isn't learning."** First check tokenization. Then check tokenization again.
- **"All embeddings are the same; just pick one."** Embedding choice matters more than people admit. Run an eval on your data.
- **"VLMs replace OCR."** They don't — they hallucinate digits and fine-print. For invoices/IDs, dedicated OCR + structured extraction wins.

**How to communicate.** When asked "how would you build X NLP system": narrate (1) is this a classification, generation, or retrieval problem?, (2) which pretrained model fits — encoder vs decoder vs embedding, (3) data + tokenization plan with leakage check, (4) fine-tuning vs zero-shot vs API, (5) evaluation metric matching the business outcome, (6) deployment shape and latency target.

---

## 19. Cheatsheet

```text
TOKENIZATION
  tok = AutoTokenizer.from_pretrained(checkpoint)        # always paired with model
  out = tok(text, padding=True, truncation=True, max_length=256, return_tensors="pt")
  out = tok(text1, text2, ...)                            # pair: token_type_ids = 0/1
  is_split_into_words=True                                # pre-tokenized word list
  return_offsets_mapping=True; word_ids(i)                # subword <-> word/char alignment
  special: cls_token_id, sep_token_id, pad_token_id, eos_token_id
  -100 in labels means "ignore in loss"

HF MODELS (Auto* family)
  AutoModelForSequenceClassification(checkpoint, num_labels=N, ignore_mismatched_sizes=True)
  AutoModelForTokenClassification (NER, POS)
  AutoModelForQuestionAnswering   (extractive QA)
  AutoModelForMaskedLM            (BERT MLM)
  AutoModelForCausalLM            (GPT/Llama-style generation)
  AutoModelForSeq2SeqLM           (T5, BART)
  AutoModelForImageClassification / ObjectDetection / SemanticSegmentation
  AutoModelForVision2Seq          (image -> text VLMs)

PIPELINE
  pipe = pipeline("sentiment-analysis" | "ner" | "zero-shot-classification" | ...)
  prototyping only; switch to batched model for throughput

DATASETS
  ds = load_dataset("imdb")  /  load_dataset("json", data_files=...)
  ds.map(tokenize_fn, batched=True, remove_columns=...)
  ds.with_format("torch")
  ds.filter / .shuffle / .train_test_split

FINE-TUNING (encoder)
  TrainingArguments(lr=2e-5, weight_decay=0.01, batch=32, epochs=3,
                    warmup_ratio=0.1, bf16=True, eval_strategy="epoch",
                    load_best_model_at_end=True)
  Trainer(model, args, train_dataset, eval_dataset, tokenizer, data_collator,
          compute_metrics)
  DataCollatorWithPadding(tokenizer=tok)              # dynamic padding
  trainer.train(); trainer.save_model("dir/")
  for token classification: align labels with word_ids; -100 for non-first subword

EMBEDDINGS
  model = SentenceTransformer("BAAI/bge-base-en-v1.5")
  emb = model.encode(texts, normalize_embeddings=True, batch_size=64)
  cosine = (emb_q @ emb_d.T)                          # normalize once, then dot
  asymmetric: query prefix per model card
  cross-encoder rerank top-50 -> top-5 for quality

VECTOR SEARCH
  brute force: docs @ query (≤100k items)
  faiss IndexHNSWFlat(dim, M=32); .add; .search(q, k)
  IVF / IVF-PQ for >10M vectors
  managed: Pinecone / Weaviate / Qdrant / pgvector / BigQuery

GENERATION (preview)
  AutoModelForCausalLM with apply_chat_template(messages)
  generate(max_new_tokens=200, do_sample=True, temperature=0.7, top_p=0.9)
  Module 10 covers fine-tuning, vLLM serving, RAG

VISION
  timm.create_model(name, pretrained=True, num_classes=N)
  AutoImageProcessor + AutoModelForImageClassification (HF parallel)
  ignore_mismatched_sizes=True when changing num_labels
  RandAugment + RandomErasing as default augmentation
  DINOv2 frozen + linear probe for low-data; CLIP for zero-shot

DETECTION / SEGMENTATION
  YOLO (ultralytics) — real-time, easy to fine-tune
  RT-DETR / DETR (HF) — transformer detection
  Grounding DINO — open-vocab text-prompted
  SAM 2 — segment by point/box prompts; auto mask gen
  COCO format for custom datasets

AUDIO
  pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo")
  resample to 16 kHz; convert to mono (.mean over channels)
  chunk_length_s=30 for long audio

MULTIMODAL (VLMs)
  AutoModelForVision2Seq + AutoProcessor.apply_chat_template
  for OCR-light, captions, VQA — but never for safety-critical extraction

EVAL
  classification: accuracy, macro-F1, AUROC
  NER: seqeval entity-level F1
  retrieval: Recall@K, MRR, nDCG@K
  detection: mAP @ IoU thresholds
  generation: ROUGE / BLEU / BERTScore + LLM-as-judge / human

DEPLOY
  serve fine-tuned encoder with FastAPI (Module 4 + 6)
  ONNX (optimum) for CPU serving (2-3× speedup)
  batching is essential for GPU throughput (Triton, TEI, vLLM)
  cache embeddings; only recompute when model version changes

ANTI-PATTERNS (avoid)
  mismatched tokenizer/model; manual char truncation; missing attention_mask
  unnormalized embedding cosine; no batching; brute-force kNN at scale
  full fine-tune at high LR (2e-5 for transformers)
  ignore_mismatched_sizes forgotten when changing num_labels
  fp32 on Ampere+; pickle-based model files (use safetensors)
  trust-remote-code on random checkpoints
```

---

## 20. Prerequisites & next steps

**Prerequisites covered? You can:**
- Tokenize text correctly, including alignment for NER and offset mapping for QA.
- Pick the right HF auto-class for a task and load matched tokenizer + model.
- Fine-tune an encoder for classification, NER, or QA with Trainer or a manual loop.
- Build embedding pipelines: pick a model, batch-encode, index, retrieve, rerank.
- Use vision foundation models — fine-tune a ViT, run a DINOv2 linear probe, do CLIP zero-shot.
- Use detection + segmentation foundation models (YOLO, Grounding DINO, SAM) zero-shot or fine-tuned.
- Transcribe audio with Whisper, embed audio for similarity, work with VLMs.
- Evaluate with metrics that match the task (entity F1, Recall@K, mAP).
- Deploy a model with FastAPI, batching, ONNX runtime; pick the right serving stack.

**Next steps in the bible:**
- **Module 10 — LLMs and Generative AI.** Fine-tuning at scale (LoRA/QLoRA), RAG, vLLM serving, prompt engineering, evals.
- **Module 11 — Agents.** LangGraph, tool use, multi-step agents.
- **Module 12 — MLOps.** Model registries, monitoring, drift, retraining for everything in this module.
- **Module 13 — LLMOps.** Cost tracking, prompt management, observability for LLM apps.

**External study (only if you want depth):**
- The Hugging Face NLP Course (free, runnable) — the canonical reference.
- *Speech and Language Processing* (Jurafsky & Martin, 3rd ed., free online) — the textbook.
- The papers behind your default models (BERT, RoBERTa, ViT, CLIP, DINOv2, SAM) — read once, refer often.
- The MTEB and MMTEB benchmarks for embedding model selection.

---

*End of Module 9. Module 10 covers LLMs and Generative AI — fine-tuning, LoRA/QLoRA, RAG, prompt engineering, vLLM serving, evals — same structure, 35+ problems.*
