# Module 8 — Deep Learning (PyTorch)

> **Bible Module 8 of 14.** Self-contained. Written for **PyTorch 2.5+ (verified on 2.11), torchvision 0.20+, torchmetrics 1.4+, Lightning 2.x, Python 3.12+**. All code runnable as-is on CPU; GPU code paths are marked. Assumes Modules 1, 2, 4, 6, 7.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: build, train, debug, and deploy neural networks in PyTorch; write a clean, GPU-ready training loop you can extend to any model; use transfer learning for vision and NLP; reach for mixed precision and DDP when scale demands; serialize models for production with TorchScript or ONNX; and pick deep learning over classical ML only when the problem actually warrants it.

**Target reader.** Modules 1 (Python), 2 (numpy/pandas), and 7 (classical ML — pipelines, splits, leakage). No prior PyTorch/TF experience required.

**How to use it.** Same as before. Run every code block; do all 36 problems; keep §19 cheatsheet open.

**Prerequisites.** Module 7 is highly recommended — most concepts (splits, leakage, metrics) carry over.
**Next steps.** Module 9 (NLP & CV — transformers, diffusion). Module 10 (LLMs). Module 11 (Agents).

---

## 1. Where deep learning fits — and where classical ML still wins

| Problem shape | Right tool |
|---|---|
| Tabular, < 10M rows | **Gradient-boosted trees** (Module 7), not deep |
| Images / video | **CNNs** or **Vision Transformers** |
| Text, sequence understanding | **Transformers** (Module 9) |
| Audio / speech | CNN-RNN hybrids, **transformers** |
| Recommendation at scale (multi-modal features) | Two-tower / sequence models |
| Reinforcement learning / control | DL with RL (out of scope here) |
| Time-series with rich features | Often **GBM**; sometimes deep models for long sequences |
| Few hundred labelled examples | **Transfer learning** (pretrained model + fine-tune) |
| Anomaly detection | Autoencoders, normalizing flows |

**The 2026 reality.** Tabular ML is still GBM-territory. Deep models earn their keep when (a) the input is unstructured (pixels, text, audio), (b) you can leverage a large pretrained model, or (c) you need end-to-end multi-modal learning. Don't reach for a transformer when LightGBM works.

### 1.1 PyTorch vs TensorFlow vs JAX

| | PyTorch | TensorFlow / Keras | JAX |
|---|---|---|---|
| Mental model | Imperative ("just Python") | Declarative graphs (eager mostly OK) | Functional, JIT-compiled |
| Research community | **Dominant** | Smaller in 2026 | Growing in research |
| Deployment | TorchScript / ONNX / Triton | TF Serving / TFLite | Less mature |
| Distributed | DDP, FSDP, torch.distributed | TF Distribution, Mesh-TF | shard_map / pjit |
| Pick if… | New project, aligns with HF ecosystem | Existing TF stack | You want functional purity, TPU |

In 2026, **PyTorch is the default**. Hugging Face, vLLM, most research papers, and most ML teams use it. We focus on PyTorch.

---

## 2. Tensors and autograd — the foundation

Every deep model is a function over tensors with parameters that are updated via gradient descent. Master these two ideas before nn.Module.

### 2.1 Tensors

A `torch.Tensor` is like a NumPy `ndarray` with two superpowers: it lives on a GPU when you ask, and it tracks operations for automatic differentiation.

```python
import torch

x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
print(x.shape, x.dtype, x.device)            # torch.Size([2, 2]) torch.float32 cpu

# from numpy
import numpy as np
a = np.array([1., 2., 3.])
t = torch.from_numpy(a)                       # shares memory with NumPy

# common factories (mirror NumPy almost exactly)
torch.zeros(3, 4)
torch.ones(2, 3)
torch.arange(0, 10, 2)
torch.linspace(0, 1, 5)
torch.randn(2, 3)                              # standard normal
torch.rand(2, 3)                               # uniform [0,1)

# move to GPU (or MPS on Apple Silicon)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
x = x.to(device)
```

### 2.2 Operations and broadcasting

Same broadcasting rules as NumPy (Module 2 §2.7).

```python
a = torch.arange(6).reshape(2, 3).float()    # (2, 3)
b = torch.tensor([10., 20., 30.])             # (3,)
a + b                                          # broadcasts to (2, 3)
a @ b                                          # matrix-vector mult: (2,)
a.T                                            # transpose
a.sum(dim=0)                                   # collapse rows -> (3,)
a.mean(dim=1, keepdim=True)                    # (2, 1)
```

Same semantics as NumPy. **One difference:** PyTorch uses `dim` instead of `axis`. Mentally substitute.

### 2.3 Autograd — the engine of learning

Set `requires_grad=True` to track gradients:

```python
x = torch.tensor(2.0, requires_grad=True)
y = x**3 + 4*x                                 # y is now part of a computation graph
y.backward()                                    # populates x.grad
print(x.grad)                                   # 3*x^2 + 4 evaluated at x=2 → 16
```

For vector outputs you need to reduce to a scalar before `backward()`:
```python
x = torch.randn(5, requires_grad=True)
loss = (x ** 2).sum()
loss.backward()
print(x.grad)        # 2*x
```

### 2.4 Tensors are mutable; computation graphs are not

A common gotcha: gradients accumulate by default. You must zero them between optimizer steps or they pile up.

```python
optimizer.zero_grad()      # clears .grad of every parameter
loss.backward()            # populates .grad with new values
optimizer.step()            # updates parameters using .grad
```

Forget `optimizer.zero_grad()` and your gradients are the *sum* of all past gradients — model never converges, or trains erratically.

### 2.5 `torch.no_grad()` — for inference and eval

```python
model.eval()
with torch.no_grad():                  # disables autograd → ~2× faster, no memory for grads
    preds = model(X_val)
```

Always wrap inference in `torch.no_grad()`. For very tight loops, `torch.inference_mode()` is even faster.

### 2.6 Detach and `.item()`

To pull a scalar out of a tensor:
```python
loss_value = loss.item()       # python float; do NOT keep the tensor in your logging history
```

To break the graph (use the value but not its gradient):
```python
y_detached = y.detach()
```

**Memory leak alarm:** appending `loss` (the tensor) to a Python list keeps the entire graph alive. Always `.item()` for logging.

### 2.7 Reproducibility

```python
import random, numpy as np, torch

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # determinism (slower)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

True determinism on GPU also requires `CUBLAS_WORKSPACE_CONFIG` and `torch.use_deterministic_algorithms(True)`. Most teams accept slight nondeterminism in production for the speedup.

---

## 3. nn.Module — building networks

Models are subclasses of `nn.Module`. The pattern: define layers in `__init__`, define the forward pass in `forward`. Backward is generated automatically.

### 3.1 The minimal model

```python
import torch.nn as nn
import torch.nn.functional as F

class MLP(nn.Module):
    def __init__(self, in_dim: int, hidden: int, out_dim: int, dropout: float = 0.1):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden)
        self.fc2 = nn.Linear(hidden, hidden)
        self.fc3 = nn.Linear(hidden, out_dim)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.drop(x)
        x = F.relu(self.fc2(x))
        x = self.drop(x)
        return self.fc3(x)
```

Key facts:
- `super().__init__()` is **required**; it registers parameters.
- Anything assigned to `self` that's a `Module`, `Parameter`, or sub-module is automatically tracked. Plain tensors aren't unless wrapped in `nn.Parameter`.
- `model(x)` invokes `forward(x)` plus hooks. Don't call `forward` directly.

### 3.2 The layers you'll use 90% of the time

```python
nn.Linear(in_features, out_features)                       # dense
nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1)         # conv
nn.ConvTranspose2d(...)                                     # for decoders/upsampling
nn.BatchNorm1d(d) / nn.BatchNorm2d(c) / nn.LayerNorm(d)
nn.Dropout(p=0.1) / nn.Dropout2d(p=0.1)
nn.Embedding(num_embeddings, embedding_dim)                # for token IDs / categoricals
nn.LSTM(input_size, hidden_size, num_layers=2, batch_first=True)
nn.GRU(...)                                                 # cheaper than LSTM, similar quality
nn.MultiheadAttention(embed_dim, num_heads)                # for transformers
nn.TransformerEncoder / nn.TransformerDecoder

# losses
nn.CrossEntropyLoss()                                       # multi-class classification
nn.BCEWithLogitsLoss()                                      # binary classification
nn.MSELoss() / nn.SmoothL1Loss() / nn.L1Loss()              # regression
nn.NLLLoss()                                                # if you already have log-probs
```

### 3.3 Activation functions

Available as functional or as modules. The functional form is conventional inside `forward`:

```python
F.relu(x), F.gelu(x), F.silu(x), F.tanh(x), F.softmax(x, dim=-1)
```

**Choose:**
- `ReLU` — default for vision CNNs.
- `GELU` — default for transformers (NLP).
- `SiLU` (a.k.a. Swish) — default for modern vision and audio.
- `Sigmoid` — only for the final layer of binary classification (and even then prefer `BCEWithLogitsLoss` which folds it in for stability).
- `Softmax` — only at the final layer for multi-class with hand-rolled NLL loss; otherwise let `CrossEntropyLoss` do it.

### 3.4 Sequential — for linear stacks

```python
mlp = nn.Sequential(
    nn.Linear(784, 256), nn.ReLU(),
    nn.Linear(256, 64),  nn.ReLU(),
    nn.Linear(64,  10),
)
```

Concise for simple models. Reach for `nn.Module` subclassing once you need branching, residuals, or multi-input forward.

### 3.5 Initialization — usually fine, sometimes critical

PyTorch initializes most layers reasonably (Kaiming for Linear/Conv, etc.). For a custom architecture or when you see exploding/vanishing gradients early, override:

```python
def init_weights(m):
    if isinstance(m, nn.Linear):
        nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
        if m.bias is not None: nn.init.zeros_(m.bias)

model.apply(init_weights)
```

### 3.6 Counting parameters

Quick sanity check before training:

```python
def count_params(model: nn.Module) -> tuple[int, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable
```

A "100k-param model" trains in seconds; "100M-param" needs a GPU; "10B-param" is multi-GPU and a different module (10).

---

## 4. Datasets, DataLoaders, transforms

The data pipeline matters as much as the model. A bad DataLoader bottlenecks GPU compute.

### 4.1 Dataset and DataLoader

```python
from torch.utils.data import Dataset, DataLoader

class TabularDataset(Dataset):
    def __init__(self, X: torch.Tensor, y: torch.Tensor):
        assert len(X) == len(y)
        self.X, self.y = X, y

    def __len__(self): return len(self.X)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

train_ds = TabularDataset(X_train, y_train)
train_loader = DataLoader(
    train_ds,
    batch_size=128,
    shuffle=True,
    num_workers=4,           # parallel CPU prefetch — set carefully
    pin_memory=True,         # for GPU: page-locked memory speeds host->device copy
    drop_last=True,          # drop the partial last batch (helps batch norm)
    persistent_workers=True, # workers stay alive across epochs (faster)
)
```

### 4.2 The four DataLoader knobs that matter

| Knob | What it does | Default | Tune to |
|---|---|---|---|
| `batch_size` | Samples per gradient step | 1 | Largest that fits in memory |
| `num_workers` | Worker processes for `__getitem__` | 0 (main proc) | 4–8 typical; 0 if data is already in RAM |
| `pin_memory` | Page-lock host memory for fast transfer | False | `True` on GPU |
| `prefetch_factor` | Batches each worker buffers | 2 | 2–4; raise if GPU is starved |

Profile first. If `nvidia-smi` shows GPU utilization fluctuating <90%, your DataLoader is the bottleneck — increase `num_workers` first, then `prefetch_factor`.

### 4.3 Custom dataset for image files

```python
from PIL import Image
from torchvision import transforms as T

class ImageFolderJsonl(Dataset):
    """Images on disk, labels in a jsonl manifest."""
    def __init__(self, manifest_path, transform=None):
        import json
        self.items = [json.loads(l) for l in open(manifest_path)]
        self.transform = transform

    def __len__(self): return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        img = Image.open(item["path"]).convert("RGB")
        if self.transform: img = self.transform(img)
        return img, item["label"]

train_tfm = T.Compose([
    T.Resize(256),
    T.RandomResizedCrop(224),
    T.RandomHorizontalFlip(),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
val_tfm = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

The mean/std normalization values are ImageNet stats — used because most pretrained models expect them. For training from scratch on your own data, compute your own.

### 4.4 The collate_fn — for variable-length data

Default `DataLoader` stacks samples; if your samples have different shapes (variable-length text), provide a `collate_fn`:

```python
def pad_collate(batch):
    seqs, labels = zip(*batch)
    lens = torch.tensor([len(s) for s in seqs])
    padded = torch.nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=0)
    return padded, lens, torch.tensor(labels)
```

For sequence models, this and `pack_padded_sequence` are essential.

---

## 5. The training loop done right

The single most important code template in this module. Memorize it.

### 5.1 The minimal correct loop

```python
import torch
import torch.nn as nn

def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()                                # important — enables dropout, BN
    running_loss, n = 0.0, 0
    for X, y in loader:
        X = X.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)    # set_to_none is faster than zero
        out  = model(X)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * X.size(0)
        n += X.size(0)
    return running_loss / n

@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()                                  # disables dropout, freezes BN
    running_loss, correct, n = 0.0, 0, 0
    for X, y in loader:
        X = X.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)
        out = model(X)
        loss = criterion(out, y)
        running_loss += loss.item() * X.size(0)
        if out.dim() == 2:
            correct += (out.argmax(1) == y).sum().item()
        n += X.size(0)
    return running_loss / n, correct / n
```

### 5.2 The full skeleton with logging and checkpointing

```python
def fit(model, train_loader, val_loader, optimizer, criterion, *,
        epochs: int, device: str = "cuda", scheduler=None,
        grad_clip: float | None = 1.0, ckpt_path: str = "best.pt"):
    best_val = float("inf")
    history = []
    for epoch in range(1, epochs + 1):
        # train
        model.train()
        train_loss, n = 0.0, 0
        for X, y in train_loader:
            X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(X), y)
            loss.backward()
            if grad_clip is not None:
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            train_loss += loss.item() * X.size(0); n += X.size(0)
        train_loss /= n

        # validate
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        if scheduler is not None:
            scheduler.step(val_loss) if hasattr(scheduler, "step") and \
                scheduler.__class__.__name__ == "ReduceLROnPlateau" else scheduler.step()

        # checkpoint best
        if val_loss < best_val:
            best_val = val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
            }, ckpt_path)

        history.append({"epoch": epoch, "train_loss": train_loss,
                         "val_loss": val_loss, "val_acc": val_acc})
        print(f"epoch {epoch:>3} | train {train_loss:.4f} | "
              f"val {val_loss:.4f} | acc {val_acc:.4f}")
    return history
```

### 5.3 Things every loop must include

1. **`model.train()` before training, `model.eval()` before validation.** Dropout and BatchNorm behave differently — forgetting flips half your training.
2. **`optimizer.zero_grad(set_to_none=True)` every step.** `set_to_none=True` is faster than zeroing.
3. **`.to(device, non_blocking=True)`.** With `pin_memory=True`, this overlaps host→device transfer with compute.
4. **`@torch.no_grad()` on eval.** Saves ~50% memory and time.
5. **Gradient clipping** (`clip_grad_norm_`). Prevents NaN for unstable models, especially RNNs and transformers.
6. **`.item()` for logging.** Never accumulate tensors with grad in lists.
7. **Checkpoint by val metric, not last epoch.** Avoids losing the best model to a final overfit.

### 5.4 Early stopping

Same idea as XGBoost. Stop when val hasn't improved for `patience` epochs:

```python
class EarlyStopping:
    def __init__(self, patience: int = 5, min_delta: float = 0.0):
        self.patience, self.min_delta = patience, min_delta
        self.best, self.bad_epochs = float("inf"), 0
    def step(self, val_loss: float) -> bool:
        if val_loss < self.best - self.min_delta:
            self.best, self.bad_epochs = val_loss, 0
            return False    # keep going
        self.bad_epochs += 1
        return self.bad_epochs >= self.patience    # True = stop
```

---

## 6. Optimizers, schedulers, regularization

### 6.1 Optimizers

```python
import torch.optim as optim

# AdamW — the modern default for most problems (especially transformers)
optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)

# SGD with momentum — classic vision default; competitive on CNNs
optimizer = optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)

# Lion — newer, slightly faster than AdamW on some tasks
# optimizer = lion_pytorch.Lion(...)
```

**The choice in 2026:** AdamW for transformers and most other models; SGD+momentum for from-scratch CNN image classification (still standard). **Don't** use plain `Adam` — `AdamW` decouples weight decay correctly.

### 6.2 Learning rate is everything

The most important hyperparameter is learning rate. Order of magnitude matters far more than the second decimal place.

**Typical starting points** (with weight_decay=0.01):
- Transformers from scratch: `1e-4` to `3e-4`.
- Fine-tuning a pretrained transformer: `1e-5` to `5e-5`.
- CNN from scratch: `1e-3` to `3e-3`.
- Fine-tuning a pretrained CNN: `1e-4` (head) and `1e-5` (backbone).

### 6.3 Learning rate schedulers — the four you need

```python
from torch.optim.lr_scheduler import (StepLR, CosineAnnealingLR, OneCycleLR, ReduceLROnPlateau)

# StepLR — drop by gamma every N epochs (classic for vision SGD)
scheduler = StepLR(optimizer, step_size=30, gamma=0.1)

# CosineAnnealing — smoothly anneal from lr to ~0; standard for transformers
scheduler = CosineAnnealingLR(optimizer, T_max=epochs * steps_per_epoch)

# OneCycle — warm up then cool down, popular for fast convergence
scheduler = OneCycleLR(optimizer, max_lr=1e-3,
                        total_steps=epochs * steps_per_epoch)

# ReduceLROnPlateau — drop lr when val plateau (call .step(val_loss))
scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)
```

**Per-step vs per-epoch.** `OneCycleLR` and `CosineAnnealingLR` typically step once per *batch*. `StepLR` and `ReduceLROnPlateau` step once per *epoch*. Read the docs for the scheduler you pick.

### 6.4 Warmup — the LR trick that fixes bad transformer training

Transformers need a learning-rate warmup or they often diverge in the first few hundred steps:

```python
from torch.optim.lr_scheduler import LinearLR, SequentialLR

warmup = LinearLR(optimizer, start_factor=1e-3, end_factor=1.0, total_iters=500)
cosine = CosineAnnealingLR(optimizer, T_max=total_steps - 500)
scheduler = SequentialLR(optimizer, schedulers=[warmup, cosine], milestones=[500])
```

### 6.5 Regularization tools

| Tool | Where |
|---|---|
| **Weight decay** (L2) | Always on — `AdamW(..., weight_decay=0.01)` |
| **Dropout** | Between dense layers; in transformer FFNs/attention |
| **Data augmentation** | The most-effective regularizer for vision |
| **Label smoothing** | `CrossEntropyLoss(label_smoothing=0.1)` — small win, free |
| **Stochastic depth / DropPath** | Deep models |
| **Mixup / CutMix** | Image classification |
| **Gradient clipping** | Stability — clip the norm at 1.0 |

### 6.6 Differential learning rates

Common in transfer learning: lower lr on the backbone, higher on the new head:

```python
optimizer = optim.AdamW([
    {"params": model.backbone.parameters(), "lr": 1e-5},
    {"params": model.head.parameters(),     "lr": 1e-3},
], weight_decay=0.01)
```

---

## 7. Loss functions and metrics

### 7.1 Picking a loss

| Task | Loss |
|---|---|
| Multi-class classification | `nn.CrossEntropyLoss()` (input: logits, target: long class index) |
| Binary classification | `nn.BCEWithLogitsLoss()` (input: logits, target: float 0/1) |
| Multi-label classification | `nn.BCEWithLogitsLoss()` (input: logits, target: floats) |
| Regression | `nn.MSELoss()` (also `SmoothL1`/`L1` for outliers) |
| Imbalanced classification | `BCEWithLogitsLoss(pos_weight=...)` or focal loss |
| Sequence-to-sequence (token level) | `CrossEntropyLoss(ignore_index=PAD_ID)` |

**`*WithLogitsLoss`** = applies sigmoid/softmax internally with numerical stability. Always prefer over a separate `Sigmoid` + `BCELoss`.

### 7.2 Class-imbalance loss

```python
# pos_weight — tell BCE that positive class is 9× rarer than negative
pos_weight = torch.tensor([(y_train == 0).sum() / max(1, (y_train == 1).sum())])
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))
```

For multi-class with imbalance: `CrossEntropyLoss(weight=class_weights)` where `class_weights[c] = total / count[c]`.

### 7.3 Metrics — torchmetrics

`torchmetrics` integrates with PyTorch and handles GPU/distributed correctly.

```python
import torchmetrics

# binary
auroc = torchmetrics.classification.BinaryAUROC().to(device)
acc   = torchmetrics.classification.BinaryAccuracy().to(device)

# update each batch; compute at end
for X, y in val_loader:
    out = model(X.to(device))
    proba = torch.sigmoid(out)
    auroc.update(proba, y.to(device))
    acc.update(proba, y.to(device))

print("AUROC:", auroc.compute().item())
auroc.reset()
```

For multi-class: `MulticlassAUROC`, `MulticlassF1Score`, `MulticlassConfusionMatrix`. For regression: `MeanSquaredError`, `MeanAbsoluteError`, `R2Score`.


---

## 8. Transfer learning — the highest-leverage move in DL

For nearly every practical problem with images, text, or audio, **start from a pretrained model**. Training from scratch is for research; production almost always fine-tunes.

### 8.1 The pattern (vision)

```python
import torch
import torch.nn as nn
from torchvision import models

# 1. Load pretrained backbone
weights = models.ResNet50_Weights.DEFAULT
backbone = models.resnet50(weights=weights)

# 2. Replace the head for your problem
n_classes = 10
backbone.fc = nn.Linear(backbone.fc.in_features, n_classes)

# 3. Choose what to train
#    Option A: freeze backbone, train head only (fastest, smallest data)
for p in backbone.parameters(): p.requires_grad = False
for p in backbone.fc.parameters(): p.requires_grad = True

#    Option B: full fine-tune with differential LR (best with enough data)
for p in backbone.parameters(): p.requires_grad = True
optimizer = torch.optim.AdamW([
    {"params": backbone.fc.parameters(),     "lr": 1e-3},
    {"params": [p for n, p in backbone.named_parameters() if "fc" not in n], "lr": 1e-5},
], weight_decay=0.01)

# 4. Use the same preprocessing the model was trained with
transform = weights.transforms()    # built-in: resize/crop/normalize matching ImageNet
```

### 8.2 The pattern (NLP — preview of Module 9)

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
tok = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)
# fine-tune with AdamW, LR ~2e-5, 2-4 epochs
```

Module 9 covers transformer fine-tuning in detail. The principle here: a checkpoint trained on billions of tokens / millions of images carries enormous prior knowledge.

### 8.3 The freeze/unfreeze decision

| Data size | Strategy |
|---|---|
| < 1k samples | Freeze backbone; train new head only |
| 1k–10k | Freeze backbone for a few epochs, then unfreeze + low LR |
| 10k–100k | Full fine-tune with differential LR |
| > 100k | Full fine-tune; consider training from scratch if domain is unusual |

### 8.4 Catastrophic forgetting and the gradual unfreeze

If you fine-tune with a high learning rate, you can wipe out the pretrained weights ("catastrophic forgetting"). Defenses:
- Use 10–100× lower LR on the backbone than on the new head.
- Train the head first with backbone frozen; *then* unfreeze and continue with low LR everywhere.
- Use shorter training (2–4 epochs is plenty for fine-tuning).

---

## 9. Mixed precision and performance

Mixed precision = use `float16` (or `bfloat16`) for most ops, keep `float32` master copies for stability. **2× throughput, half the GPU memory.** Free win on any modern GPU.

### 9.1 The autocast + GradScaler pattern (CUDA)

```python
from torch.amp import autocast, GradScaler

scaler = GradScaler()           # only needed for float16; bfloat16 doesn't need scaling

for X, y in loader:
    X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
    optimizer.zero_grad(set_to_none=True)

    with autocast(device_type="cuda", dtype=torch.float16):
        out = model(X)
        loss = criterion(out, y)

    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)                      # for gradient clipping etc.
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    scaler.step(optimizer)
    scaler.update()
```

For `bfloat16` (Ampere/H100, often safer than fp16):
```python
with autocast(device_type="cuda", dtype=torch.bfloat16):
    out = model(X)
    loss = criterion(out, y)
loss.backward()                  # no scaler needed for bf16
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
optimizer.step()
```

### 9.2 channels_last memory format (vision)

For convolutional models on Ampere+ (A10/A100/H100), switch to channels-last layout for ~10–30% speedup:

```python
model = model.to(memory_format=torch.channels_last)
X = X.to(memory_format=torch.channels_last)
```

### 9.3 `torch.compile` — JIT for free speed

Since PyTorch 2.0, you can JIT-compile models for ~30% speedup with one line:

```python
model = torch.compile(model)        # uses TorchInductor
```

Caveats:
- First batch is slower (compile overhead).
- Some ops aren't supported; fall back gracefully.
- Recompiles when input shapes change drastically — pad to fixed shapes if practical.

### 9.4 Gradient accumulation — large batch on small GPU

When your effective batch size is too large to fit, accumulate gradients across micro-batches:

```python
ACCUM_STEPS = 4
optimizer.zero_grad(set_to_none=True)

for i, (X, y) in enumerate(loader):
    out = model(X.to(device))
    loss = criterion(out, y.to(device)) / ACCUM_STEPS
    loss.backward()                                # accumulates
    if (i + 1) % ACCUM_STEPS == 0:
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
```

Effective batch size = `batch_size × ACCUM_STEPS`. Trade compute for memory.

### 9.5 Checkpointing activations — even bigger memory wins

For very deep models (transformers >1B params), recomputing activations during backward saves memory at the cost of a second forward:

```python
from torch.utils.checkpoint import checkpoint
class Block(nn.Module):
    def forward(self, x):
        return checkpoint(self._forward, x, use_reentrant=False)
    def _forward(self, x):
        ...    # the actual computation
```

Used heavily in LLM training — Module 10.

---

## 10. Distributed training (DDP basics)

Most teams' first taste of "more than one GPU" is **DistributedDataParallel** (DDP). Here's the minimum to know.

### 10.1 The DDP mental model

- One process per GPU.
- Each process trains on a different shard of the data.
- Gradients are averaged across processes after each `backward()`.
- All optimizer steps are identical → all processes have identical weights.

### 10.2 The pattern

```python
import os
import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

def setup():
    dist.init_process_group(backend="nccl")           # nccl on GPU; gloo on CPU
    rank       = dist.get_rank()
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    return rank, local_rank

def cleanup():
    dist.destroy_process_group()

def main():
    rank, local_rank = setup()
    device = torch.device(f"cuda:{local_rank}")

    model = MyModel().to(device)
    model = DDP(model, device_ids=[local_rank])

    sampler = DistributedSampler(train_ds, shuffle=True)
    loader  = DataLoader(train_ds, batch_size=64, sampler=sampler,
                          num_workers=4, pin_memory=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        sampler.set_epoch(epoch)                       # ensures different shuffling per epoch
        for X, y in loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(X), y)
            loss.backward()
            optimizer.step()

        if rank == 0:                                  # only rank 0 logs / checkpoints
            torch.save(model.module.state_dict(), f"ckpt_{epoch}.pt")
    cleanup()

if __name__ == "__main__":
    main()
```

Launch with:
```bash
torchrun --nproc-per-node=8 train.py        # 8 GPUs on this node
torchrun --nnodes=2 --nproc-per-node=8 --rdzv-backend=c10d --rdzv-endpoint=$MASTER:29500 train.py
```

### 10.3 FSDP — the next step up for very big models

When the model itself doesn't fit on one GPU, use **Fully Sharded Data Parallel** (FSDP). FSDP shards model params, gradients, and optimizer state across ranks. Out of scope here in detail; the pattern is similar to DDP. For LLMs (Module 10), FSDP or DeepSpeed is the standard.

### 10.4 The single mistake to avoid

**Forgetting `sampler.set_epoch(epoch)` makes every epoch see the same data order.** Models train but learn slower. Subtle bug — easy to miss.

---

## 11. PyTorch Lightning — when to drop the boilerplate

Lightning wraps the training loop into a clean, opinionated structure. You write a `LightningModule`; Lightning handles devices, distributed, checkpointing, logging, mixed precision.

```python
import lightning as L
import torch.nn as nn
import torch.nn.functional as F

class LitClassifier(L.LightningModule):
    def __init__(self, model, lr=3e-4):
        super().__init__()
        self.model = model
        self.lr = lr
        self.save_hyperparameters(ignore=["model"])

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        loss = F.cross_entropy(self(x), y)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        out = self(x)
        loss = F.cross_entropy(out, y)
        acc = (out.argmax(1) == y).float().mean()
        self.log_dict({"val_loss": loss, "val_acc": acc}, prog_bar=True)

    def configure_optimizers(self):
        opt = torch.optim.AdamW(self.parameters(), lr=self.lr, weight_decay=0.01)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=10)
        return {"optimizer": opt, "lr_scheduler": sched}

trainer = L.Trainer(
    max_epochs=10, accelerator="auto", devices="auto",
    precision="bf16-mixed",                   # mixed precision for free
    gradient_clip_val=1.0,
    callbacks=[L.pytorch.callbacks.EarlyStopping("val_loss", patience=3)],
    log_every_n_steps=10,
)
trainer.fit(LitClassifier(model), train_loader, val_loader)
```

### 11.1 When to use Lightning

- **Use it** when you want clean code, multi-GPU/TPU support, less ops work, and you're comfortable with Lightning's structure.
- **Don't use it** when you need very low-level control (custom backward, multi-optimizer dance, custom collective communication). Raw PyTorch is more transparent.

For research + production tabular/vision/NLP, Lightning is the productivity sweet spot.

---

## 12. Debugging deep models

Deep learning bugs are different. The model "trains" but doesn't *learn*. Here's the debug ladder.

### 12.1 Overfit a single batch — the sanity-check sanity-check

Take 4 samples; train until loss is near zero. If you can't, your model or loss is broken — not your data.

```python
X_tiny, y_tiny = next(iter(train_loader))
X_tiny, y_tiny = X_tiny[:4].to(device), y_tiny[:4].to(device)
for step in range(500):
    optimizer.zero_grad(set_to_none=True)
    loss = criterion(model(X_tiny), y_tiny)
    loss.backward(); optimizer.step()
    if step % 50 == 0:
        print(step, loss.item())
# expected: loss → near 0 within a few hundred steps
```

A model that can't overfit 4 samples can't generalize to thousands.

### 12.2 Check shapes constantly

The most common bug. Print shapes after every layer the first time you train.

```python
def shape_hook(name):
    def hook(module, inp, out):
        print(name, "->", out.shape)
    return hook

for name, mod in model.named_modules():
    mod.register_forward_hook(shape_hook(name))
```

Remove the hook before training for real.

### 12.3 NaN / Inf

```python
torch.autograd.set_detect_anomaly(True)            # in dev only — slow
```

Print loss every step. If it goes NaN:
- Lower the LR by 10×.
- Add gradient clipping.
- Check for division-by-zero in custom ops.
- Switch from `float16` to `bfloat16`.
- Verify input normalization.

### 12.4 The data, not the model

For 80% of "model isn't learning" bugs, the cause is the data:
- Forgot to normalize input.
- Labels misaligned with samples.
- Data-augmentation pipeline producing garbage.
- The classes are imbalanced and you forgot a class weight.

Always visualize a batch: print 5 inputs and labels; do they make sense?

### 12.5 The exploding/vanishing gradient diagnostic

```python
def log_grad_norms(model):
    norms = {}
    for name, p in model.named_parameters():
        if p.grad is not None:
            norms[name] = p.grad.norm().item()
    return norms
```

After `loss.backward()` and before `optimizer.step()`, inspect. Healthy norms are roughly the same magnitude across layers; one layer 1000× bigger or smaller is a problem.

### 12.6 Common `nn.CrossEntropyLoss` mistakes

- `target` must be `long` class indices, not one-hot floats.
- `input` must be **logits** (no `softmax` applied).
- Reductions: default is `mean`; use `none` if you need per-sample losses.

Same kind of confusion with `BCEWithLogitsLoss` (no sigmoid, target is float 0/1).

---

## 13. Saving, loading, and deployment

### 13.1 The state_dict pattern (always use this)

```python
# save
torch.save({
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "epoch": epoch,
    "val_loss": val_loss,
}, "checkpoint.pt")

# load
ckpt = torch.load("checkpoint.pt", map_location="cpu", weights_only=True)
model.load_state_dict(ckpt["model_state_dict"])
```

**Don't pickle the whole `nn.Module`** (e.g., `torch.save(model, ...)`). It couples the file to your file paths and class definitions. Save state_dict; rebuild the model from code at load time.

`weights_only=True` in `torch.load` (default in 2.6+) prevents arbitrary code execution — important when loading from untrusted sources.

### 13.2 The deploy bundle

Just like Module 7, the model isn't a single file. It's a bundle:
```
model_v1/
├── model.pt                # state_dict
├── architecture.py         # class definition
├── tokenizer/              # for NLP, the tokenizer files
├── preprocessing.json      # mean, std, normalization
├── metrics.json            # test scores
└── manifest.yaml           # version, training data hash, code SHA
```

Or as a single `model.pt` containing everything if you're disciplined; or use the **safetensors** format for safer serialization (no pickle, no code execution risk).

### 13.3 TorchScript — for portable inference

TorchScript captures the model as a graph that runs in C++ without Python.

```python
# scripting (for simple control flow)
scripted = torch.jit.script(model)
scripted.save("model.script.pt")

# tracing (for fixed-shape forward)
traced = torch.jit.trace(model, example_input)
traced.save("model.trace.pt")

# load in Python
loaded = torch.jit.load("model.trace.pt")
loaded.eval()
out = loaded(x)
```

`script` works for general code; `trace` only captures the path used by the example inputs (dynamic control flow won't work). TorchScript powers the LibTorch C++ runtime — useful for mobile, embedded, low-latency serving.

### 13.4 ONNX export — cross-framework portability

```python
import torch.onnx

torch.onnx.export(
    model.eval(),
    args=example_input,
    f="model.onnx",
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
    opset_version=20,
)
```

Then run with `onnxruntime` (Python, C++, JS). Often 1.5–3× faster than vanilla PyTorch on CPU. Standard format for cross-framework deployment.

### 13.5 FastAPI serving (Modules 4 + 6 integration)

```python
import torch
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Load once at startup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = MyModel().to(device)
model.load_state_dict(torch.load("model.pt", map_location=device, weights_only=True))
model.eval()

class Inputs(BaseModel):
    features: list[float]

@app.post("/predict")
@torch.inference_mode()                       # disables autograd entirely
def predict(payload: Inputs):
    x = torch.tensor([payload.features], dtype=torch.float32, device=device)
    out = model(x)
    proba = torch.softmax(out, dim=1)[0].cpu().tolist()
    return {"probabilities": proba}

@app.get("/health")
def health(): return {"status": "ok"}
```

For real production, batch many incoming requests together (Triton Inference Server, Ray Serve, or a custom batching middleware) — the GPU is fastest at batch_size > 1, not at one-request-at-a-time.

---

## 14. Anti-patterns

| Anti-pattern | Right way |
|---|---|
| Forgetting `model.train()` / `model.eval()` | Always set explicitly before train and eval |
| Forgetting `optimizer.zero_grad()` | `zero_grad(set_to_none=True)` every step |
| Appending `loss` (tensor) to a list | `loss.item()` — never keep grad-tracked tensors |
| Calling `model.forward(x)` directly | Always `model(x)` (runs hooks) |
| `nn.Sigmoid()` + `nn.BCELoss()` | `BCEWithLogitsLoss()` — numerically stable |
| Softmax + NLLLoss by hand | `CrossEntropyLoss()` — same thing, faster |
| One-hot targets for `CrossEntropyLoss` | Class indices (long) only |
| `torch.save(model, ...)` | `torch.save(model.state_dict(), ...)` |
| `pickle.load` untrusted weights | `weights_only=True` (default in 2.6+) or safetensors |
| Tuning lr by tiny increments | Tune in log space — orders of magnitude matter |
| Plain `Adam` | `AdamW` (decoupled weight decay) |
| Training transformers without warmup | Use linear warmup + cosine |
| `requires_grad=False` only on the head you want frozen | Set on all backbone params *and* check `optimizer` only sees grad-able params |
| Single-GPU code that calls `.cuda()` everywhere | `.to(device)`; let environment pick |
| `num_workers=0` for big datasets | 4–8 workers; profile GPU starvation |
| `pin_memory=False` on GPU | `True` plus `non_blocking=True` |
| BatchNorm with batch_size=1 | Use GroupNorm or LayerNorm instead |
| Mixed-precision without `GradScaler` (fp16) | Required for fp16; bf16 doesn't need scaler |
| Random split on time-series or grouped data | Same as Module 7 — group/time-aware splits |
| Skipping the "overfit one batch" sanity check | Always run it before a real training run |

---

## 15. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 5 tensors/autograd (P1–P5), 4 networks (P6–P9), 4 dataloaders (P10–P13), 6 training loops (P14–P19), 4 optim/schedulers (P20–P23), 3 transfer learning (P24–P26), 4 amp/perf (P27–P30), 3 debugging (P31–P33), 1 distributed (P34), 2 deploy (P35–P36).

---

### Problem 1 — Tensor basics with broadcasting

**Statement.** Given `x` of shape `(B, T, D)` (batch, sequence, feature), produce a per-sequence z-score normalization (mean 0, std 1 along the time dim).

**Solution.**
```python
import torch
x = torch.randn(8, 50, 64)
mean = x.mean(dim=1, keepdim=True)            # (B, 1, D)
std  = x.std(dim=1,  keepdim=True, unbiased=False) + 1e-6
z = (x - mean) / std
print(z.shape, z.mean(), z.std())
```

**Why `keepdim`.** Without it, broadcasting fails because shapes drop to `(B, D)`.

**Real-world.** Per-utterance feature normalization in audio; per-sequence stats in time-series.

**Follow-ups.** LayerNorm with learnable params (`nn.LayerNorm(D)` over last dim). Per-batch normalization (BatchNorm).

---

### Problem 2 — Compute a Jacobian-vector product without forming the Jacobian

**Statement.** Given `f(x)` and a vector `v`, compute `J @ v` where `J = ∂f/∂x` — without materializing `J`.

**Solution.**
```python
import torch

def f(x): return torch.stack([x[0]**2 + x[1], x[1]*x[2], x[0]*x[2]])

x = torch.tensor([1., 2., 3.], requires_grad=True)
v = torch.tensor([0.1, 0.2, 0.3])

# vjp: v^T J — note this is "transpose-J times v"
y = f(x)
vjp = torch.autograd.grad(y, x, grad_outputs=v, create_graph=False)[0]
print(vjp)
```

**Why.** For real models, `J` is gigantic (params × outputs). Reverse-mode autograd computes `v^T J` cheaply — that's literally what `loss.backward()` does (with `v = 1`).

**Real-world.** Influence functions, second-order optimizers, neural ODEs.

**Follow-ups.** `torch.func.vjp` and `torch.func.jvp` (forward-mode).

---

### Problem 3 — Memory-leak by accidentally retaining the graph

**Statement.** Why does this code grow memory each step?

```python
losses = []
for X, y in loader:
    out = model(X)
    loss = criterion(out, y)
    losses.append(loss)        # ← BUG
    loss.backward()
    optimizer.step()
```

**Diagnosis.** `loss` is still part of the autograd graph. Appending it keeps the entire forward graph alive across iterations.

**Fix.**
```python
losses.append(loss.item())                 # python float; no graph reference
# or
losses.append(loss.detach().cpu())         # tensor without grad
```

**Real-world.** A staple bug. Symptom: GPU memory steadily climbs; eventually OOMs after many steps.

**Follow-ups.** Spot it with `torch.cuda.memory_summary()`. Use `tracemalloc` for CPU.

---

### Problem 4 — Manually implement a linear layer with autograd

**Statement.** Write a function `mylinear(x, W, b)` whose gradient w.r.t. `W` matches `nn.Linear`.

**Solution.**
```python
import torch

def mylinear(x, W, b):
    return x @ W.T + b

x = torch.randn(4, 3, requires_grad=False)
W = torch.randn(2, 3, requires_grad=True)
b = torch.randn(2,    requires_grad=True)

y = mylinear(x, W, b).sum()
y.backward()
print(W.grad.shape, b.grad.shape)         # (2,3), (2,)

# Compare with nn.Linear
import torch.nn as nn
lin = nn.Linear(3, 2)
with torch.no_grad():
    lin.weight.copy_(W); lin.bias.copy_(b)
y2 = lin(x).sum()
W.grad = None; b.grad = None
y2.backward()
# nn.Linear backward gives identical W.grad up to numerics
```

**Real-world.** Demystifies what "the linear layer" is. Helpful when implementing custom ops.

**Follow-ups.** Implement a custom `torch.autograd.Function` with a hand-coded backward.

---

### Problem 5 — Reproducible training across runs

**Statement.** Two runs of identical code give slightly different validation losses. Make them deterministic.

**Solution.**
```python
import os, random, numpy as np, torch

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    # for full determinism, also:
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    torch.use_deterministic_algorithms(True, warn_only=True)
```

Plus: seed the DataLoader workers via `worker_init_fn`, and set `generator=torch.Generator().manual_seed(seed)` on the loader.

**Real-world.** Determinism costs ~5–20% throughput. Enable for paper-quality experiments; relax for production training where seed-level reproducibility doesn't matter.

**Follow-ups.** Even with all this, multi-GPU bf16 training is slightly nondeterministic. Document expected variance.

---

### Problem 6 — Build an MLP with proper init

**Solution.**
```python
import torch.nn as nn
import torch.nn.functional as F

class MLP(nn.Module):
    def __init__(self, in_dim, hidden, out_dim, layers=3, dropout=0.1):
        super().__init__()
        dims = [in_dim] + [hidden]*(layers-1) + [out_dim]
        self.layers = nn.ModuleList([nn.Linear(d_in, d_out)
                                       for d_in, d_out in zip(dims[:-1], dims[1:])])
        self.drop = nn.Dropout(dropout)
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
            if m.bias is not None: nn.init.zeros_(m.bias)

    def forward(self, x):
        for layer in self.layers[:-1]:
            x = self.drop(F.relu(layer(x)))
        return self.layers[-1](x)
```

**Real-world.** Tabular MLPs (TabNet, ResNet-tabular) compete with GBMs in some niches but rarely win. Useful baseline.

**Follow-ups.** Residual connections. LayerNorm/BatchNorm. Auxiliary heads.

---

### Problem 7 — A small CNN for 32×32 images

**Solution.**
```python
class TinyCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2),                                           # 32 -> 16
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2),                                           # 16 -> 8
            nn.AdaptiveAvgPool2d(1),                                   # 8 -> 1
        )
        self.classifier = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.features(x).flatten(1)
        return self.classifier(x)
```

**Why `AdaptiveAvgPool2d(1)`.** Replaces a flattening that depends on input size, so the model accepts any input >= ~32×32.

**Real-world.** Modern image classification uses pretrained ResNet/EfficientNet/ViT. This template is for rapid prototyping or constrained edge models.

**Follow-ups.** Replace BN with GroupNorm (works at small batches). Add residual connections.

---

### Problem 8 — A residual block

**Solution.**
```python
class ResBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.fc1 = nn.Linear(dim, dim)
        self.fc2 = nn.Linear(dim, dim)
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)

    def forward(self, x):
        x = x + F.gelu(self.fc1(self.norm1(x)))
        x = x + F.gelu(self.fc2(self.norm2(x)))
        return x
```

**Why residual.** Lets gradients flow through identity paths even when the layer's gradient is small. Foundational for deep networks (ResNet, Transformers, U-Net).

**Real-world.** Replace pre-norm vs post-norm based on the architecture (transformers tend to pre-norm for stability).

**Follow-ups.** Stochastic depth. SE blocks (squeeze-excitation). Pre-vs-post norm.

---

### Problem 9 — Counting and freezing parameters

**Solution.**
```python
def count_params(model):
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable

def freeze(module: nn.Module):
    for p in module.parameters():
        p.requires_grad = False

# example: freeze ResNet50 backbone, train head
backbone = torchvision.models.resnet50(weights="DEFAULT")
freeze(backbone)
backbone.fc = nn.Linear(backbone.fc.in_features, 10)        # new params requires_grad=True

total, trainable = count_params(backbone)
print(f"total {total:,}  trainable {trainable:,}")           # ~25M total, ~20K trainable
```

**Real-world.** Always print param counts before training. A "small fine-tune" with 20M trainable params explains your slow convergence.

**Follow-ups.** Per-layer parameter counts. LoRA/adapters for parameter-efficient fine-tuning (Module 10).

---

### Problem 10 — Custom Dataset for tabular data

**Solution.**
```python
import torch
from torch.utils.data import Dataset, DataLoader

class TabularDataset(Dataset):
    def __init__(self, X_np, y_np):
        self.X = torch.from_numpy(X_np).float()
        self.y = torch.from_numpy(y_np).long()
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]

train_ds = TabularDataset(X_train_np, y_train_np)
loader = DataLoader(train_ds, batch_size=128, shuffle=True,
                     num_workers=2, pin_memory=True)
```

**Edge cases.** If `X_np` is huge (multi-GB) and won't fit in RAM, store as memory-mapped numpy / parquet and read on `__getitem__`.

**Follow-ups.** `WeightedRandomSampler` for imbalance. Pre-fetched augmentation.

---

### Problem 11 — Variable-length sequence batching with collate_fn

**Solution.**
```python
from torch.nn.utils.rnn import pad_sequence

def pad_collate(batch):
    seqs, labels = zip(*batch)            # each seq is a 1D tensor of variable length
    lens = torch.tensor([len(s) for s in seqs])
    padded = pad_sequence(seqs, batch_first=True, padding_value=0)
    return padded, lens, torch.tensor(labels)

loader = DataLoader(seq_ds, batch_size=64, shuffle=True, collate_fn=pad_collate)
```

For RNNs, downstream you'd `pack_padded_sequence(padded, lens, batch_first=True, enforce_sorted=False)` and unpack the output. For transformers, you build an attention mask from `lens` instead.

**Real-world.** Standard pattern for any sequence model on uneven inputs.

**Follow-ups.** Bucketing by length to minimize padding waste. Dynamic batching.

---

### Problem 12 — Weighted sampling for imbalance

**Statement.** Class 0 has 95% of samples; class 1 has 5%. Make each batch see roughly equal classes.

**Solution.**
```python
from torch.utils.data import WeightedRandomSampler
import numpy as np

# weight each sample inversely proportional to its class frequency
class_counts = np.bincount(y_train_np)        # [9500, 500]
class_weights = 1.0 / class_counts            # [~1e-4, 2e-3]
sample_weights = class_weights[y_train_np]    # one weight per sample

sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)
loader = DataLoader(train_ds, batch_size=128, sampler=sampler, num_workers=4)
```

**Real-world.** Combined with `class_weight` in the loss is rarely needed — pick one. Sampling tends to be cleaner; loss weighting doesn't change batch composition.

**Follow-ups.** Anti-aliasing for streaming data. Hard-example mining.

---

### Problem 13 — Profile a slow DataLoader

**Statement.** GPU utilization is 30%. Find the bottleneck.

**Diagnosis order:**
1. Time the loader alone:
```python
import time
t0 = time.time()
for X, y in loader:
    pass
print(f"Loader-only epoch: {time.time() - t0:.2f}s")
```
2. Compare with full training step time. If loader alone ≈ training step, your data pipeline is the bottleneck.
3. Increase `num_workers` (try 4, 8, 16). Watch CPU usage; saturated CPU means you've maxed it.
4. Set `pin_memory=True` and use `non_blocking=True` on `.to(device)`.
5. Ensure expensive transforms are done in `__init__` once, not per `__getitem__`.
6. For images: use Pillow-SIMD or `torchvision.io` (faster decoding).

**Real-world.** A slow loader makes GPU sit idle — you're paying for an A100 to read JPEGs. Worth fixing.

**Follow-ups.** WebDataset / FFCV / DALI for max-throughput pipelines on big datasets.

---

### Problem 14 — A correct minimal training loop

(See §5.1 for the template. Memorize it.)

**Real-world.** When interviewing or onboarding, this loop is the litmus test. Common mistakes: missing `model.train()`/`eval()`, forgotten `zero_grad`, accumulating tensors with grad, calling `.forward()` directly.

**Follow-ups.** Add gradient clipping (`clip_grad_norm_`). Add scheduler step. Add metric tracking with `torchmetrics`.

---

### Problem 15 — Full training run with checkpointing

(See §5.2 for the full skeleton.)

**Real-world.** Save best by val metric (not by last epoch). Save optimizer state too — you may need to resume training.

**Follow-ups.** Resume from checkpoint:
```python
ckpt = torch.load("best.pt", weights_only=True)
model.load_state_dict(ckpt["model_state_dict"])
optimizer.load_state_dict(ckpt["optimizer_state_dict"])
start_epoch = ckpt["epoch"] + 1
```

---

### Problem 16 — Train/val with metric tracking via torchmetrics

**Solution.**
```python
import torchmetrics

acc = torchmetrics.classification.MulticlassAccuracy(num_classes=10).to(device)
f1  = torchmetrics.classification.MulticlassF1Score(num_classes=10, average="macro").to(device)

@torch.no_grad()
def evaluate(model, loader):
    model.eval()
    acc.reset(); f1.reset()
    total_loss, n = 0.0, 0
    for X, y in loader:
        X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
        out = model(X)
        loss = F.cross_entropy(out, y)
        total_loss += loss.item() * X.size(0); n += X.size(0)
        acc.update(out, y); f1.update(out, y)
    return total_loss / n, acc.compute().item(), f1.compute().item()
```

**Why torchmetrics.** Handles GPU placement, distributed reduction, numerical stability of streaming metrics. Don't roll your own AUROC across batches — torchmetrics does it correctly.

**Follow-ups.** `MetricCollection` for grouping. Multi-class confusion matrix.

---

### Problem 17 — Implement early stopping

**Solution.** (See §5.4 for `EarlyStopping` class.)

**Usage:**
```python
es = EarlyStopping(patience=5, min_delta=0.001)
for epoch in range(epochs):
    ...
    if es.step(val_loss):
        print(f"early stop at epoch {epoch}")
        break
```

**Real-world.** Avoid mixing early stopping with `OneCycleLR` — the latter assumes a known total step count. Use `CosineAnnealingLR` or `ReduceLROnPlateau` instead.

---

### Problem 18 — Gradient accumulation for big effective batch

**Statement.** You want effective batch 256 but only batch 64 fits.

**Solution.** (See §9.4.)

```python
ACCUM_STEPS = 4
optimizer.zero_grad(set_to_none=True)
for i, (X, y) in enumerate(loader):
    X, y = X.to(device), y.to(device)
    loss = criterion(model(X), y) / ACCUM_STEPS
    loss.backward()
    if (i + 1) % ACCUM_STEPS == 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
```

**Caveat.** Batch norm sees only the smaller per-step batch — for very small batches, switch to LayerNorm or GroupNorm.

**Follow-ups.** Combine with mixed precision and DDP for the full toolbox.

---

### Problem 19 — Save and resume training mid-run

**Solution.**
```python
# during training
torch.save({
    "epoch": epoch,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
    "scaler_state_dict": scaler.state_dict() if scaler else None,
    "rng": {
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        "numpy": np.random.get_state(),
        "python": random.getstate(),
    },
    "best_val": best_val,
}, "ckpt.pt")

# resume
ckpt = torch.load("ckpt.pt", map_location=device, weights_only=False)
model.load_state_dict(ckpt["model_state_dict"])
optimizer.load_state_dict(ckpt["optimizer_state_dict"])
if scheduler and ckpt["scheduler_state_dict"]:
    scheduler.load_state_dict(ckpt["scheduler_state_dict"])
torch.set_rng_state(ckpt["rng"]["torch"])
np.random.set_state(ckpt["rng"]["numpy"])
random.setstate(ckpt["rng"]["python"])
if ckpt["rng"]["cuda"]:
    torch.cuda.set_rng_state_all(ckpt["rng"]["cuda"])
start_epoch = ckpt["epoch"] + 1
```

**Real-world.** Spot-instance training (Module 6) needs frequent checkpointing — every N steps, not every epoch.

**Follow-ups.** Async checkpointing (don't block training). S3 upload + atomic rename so partial files don't corrupt resume.

---

### Problem 20 — Pick LR via the LR-finder method

**Statement.** Train for 100 steps, exponentially increasing LR from 1e-7 to 1; plot loss; pick the LR where loss decreases fastest (steepest slope).

**Solution.**
```python
def lr_find(model, loader, optimizer, criterion, device,
             start_lr=1e-7, end_lr=1.0, num_steps=100):
    history_lr, history_loss = [], []
    factor = (end_lr / start_lr) ** (1.0 / num_steps)
    for g in optimizer.param_groups: g["lr"] = start_lr

    model.train()
    iterator = iter(loader)
    for step in range(num_steps):
        try: X, y = next(iterator)
        except StopIteration:
            iterator = iter(loader); X, y = next(iterator)
        X, y = X.to(device), y.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(X), y)
        loss.backward()
        optimizer.step()
        history_lr.append(optimizer.param_groups[0]["lr"])
        history_loss.append(loss.item())
        for g in optimizer.param_groups: g["lr"] *= factor
        if loss.item() > 4 * min(history_loss): break    # diverging
    return history_lr, history_loss
```

Pick the LR ~10× lower than where the loss minimizes — that's your starting LR.

**Real-world.** Saves hours of trial and error. Standard fastai-popularized technique.

**Follow-ups.** Reset model + optimizer state after the LR find. Use the found LR with OneCycleLR.

---

### Problem 21 — OneCycleLR for fast training

**Solution.**
```python
from torch.optim.lr_scheduler import OneCycleLR
import torch.optim as optim

optimizer = optim.AdamW(model.parameters(), lr=1e-7, weight_decay=0.01)
scheduler = OneCycleLR(
    optimizer, max_lr=3e-4,
    total_steps=epochs * steps_per_epoch,
    pct_start=0.1,                    # 10% warmup
    anneal_strategy="cos",
    div_factor=25,                    # initial_lr = max_lr / div_factor
    final_div_factor=1e4,             # final_lr = initial_lr / final_div_factor
)

# important: step EVERY BATCH, not every epoch
for epoch in range(epochs):
    for X, y in loader:
        ...
        loss.backward(); optimizer.step()
        scheduler.step()              # per-step
```

**Real-world.** Fastest path to good convergence on many problems. Originally popularized by fastai.

**Follow-ups.** Cosine schedule with restarts (`CosineAnnealingWarmRestarts`).

---

### Problem 22 — Differential learning rates for fine-tuning

**Solution.**
```python
optimizer = optim.AdamW([
    {"params": backbone.parameters(),     "lr": 1e-5},
    {"params": new_head.parameters(),     "lr": 1e-3},
], weight_decay=0.01)
```

**Why.** The pretrained backbone has near-optimal weights — small updates only. The head is fresh and needs aggressive learning.

**Real-world.** Standard for vision and NLP fine-tuning. Combined with freezing/unfreezing scheduled across epochs.

**Follow-ups.** Layer-wise learning-rate decay: deeper layers get 1× LR, earlier layers get 0.5×, 0.25×, etc.

---

### Problem 23 — Schedule LR for transformer training (warmup + cosine)

**Solution.**
```python
from torch.optim.lr_scheduler import LinearLR, CosineAnnealingLR, SequentialLR

optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
warmup_steps = 1000
total_steps = 50_000

warmup = LinearLR(optimizer, start_factor=1e-3, end_factor=1.0, total_iters=warmup_steps)
cosine = CosineAnnealingLR(optimizer, T_max=total_steps - warmup_steps)
scheduler = SequentialLR(optimizer, schedulers=[warmup, cosine], milestones=[warmup_steps])

# step every batch
```

**Real-world.** This exact pattern is in nearly every transformer training script.

**Follow-ups.** `transformers` library has `get_cosine_schedule_with_warmup` as a one-liner.

---

### Problem 24 — Fine-tune ResNet50 on a 10-class image dataset

**Solution.**
```python
import torch
import torch.nn as nn
import torchvision.models as models

weights = models.ResNet50_Weights.DEFAULT
model = models.resnet50(weights=weights)
n_classes = 10
model.fc = nn.Linear(model.fc.in_features, n_classes)

# stage 1: freeze backbone, train head only (3 epochs)
for p in model.parameters(): p.requires_grad = False
for p in model.fc.parameters(): p.requires_grad = True
optimizer = torch.optim.AdamW(model.fc.parameters(), lr=1e-3, weight_decay=0.01)
# ... train for a few epochs ...

# stage 2: unfreeze, full fine-tune with differential LR (15 epochs)
for p in model.parameters(): p.requires_grad = True
optimizer = torch.optim.AdamW([
    {"params": model.fc.parameters(),                                    "lr": 1e-4},
    {"params": [p for n, p in model.named_parameters() if "fc" not in n], "lr": 1e-5},
], weight_decay=0.01)
# ... continue training ...
```

**Real-world.** Two-stage pattern wins more often than going straight to full fine-tune. Especially with <10k training images.

**Follow-ups.** EMA of model weights for smoother val loss. CutMix/Mixup augmentation.

---

### Problem 25 — Use weights.transforms() to match training preprocessing

**Statement.** The pretrained model was trained on 224×224 ImageNet-normalized inputs. Don't re-derive the preprocessing — use the bundled transform.

**Solution.**
```python
from torchvision import models, transforms as T
weights = models.ResNet50_Weights.DEFAULT
model = models.resnet50(weights=weights)
preprocess = weights.transforms()              # exactly what the model was trained with

# at inference
img = preprocess(pil_image).unsqueeze(0)
with torch.inference_mode():
    out = model(img)
```

**Why.** Many "my pretrained model is bad" bugs are subtle preprocessing mismatches (wrong mean, wrong crop size, BGR vs RGB).

**Follow-ups.** For training, augment around the base preprocessing.

---

### Problem 26 — When NOT to fine-tune

**Statement.** You have 30k labeled images of medical scans, very different from ImageNet (grayscale, much higher resolution). Fine-tuning ResNet helps only marginally.

**Decision.**
- For fundamentally different distributions, training from scratch with a domain-appropriate architecture is sometimes better.
- Or use a pretrained model that was trained on a closer domain (medical-specific foundation models, DINO-pretrained).
- Self-supervised pretraining on your unlabeled data (SimCLR, DINOv2) when you have lots of unlabeled examples.

**Real-world.** Don't always reach for ImageNet pretrained — check if a domain-specific checkpoint exists first (e.g., MedSAM, ESM for proteins, audio models for audio).

---

### Problem 27 — Mixed precision training (CUDA)

**Solution.** (See §9.1.)

```python
from torch.amp import autocast, GradScaler
scaler = GradScaler()

for X, y in loader:
    X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
    optimizer.zero_grad(set_to_none=True)
    with autocast(device_type="cuda", dtype=torch.float16):
        loss = criterion(model(X), y)
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    scaler.step(optimizer)
    scaler.update()
```

**Real-world.** ~2× throughput, half the memory. Worth setting up for any model that takes >30 min to train. Use bf16 on Ampere/H100 (no scaler needed).

**Follow-ups.** `torch.float8_e4m3fn` for cutting-edge H100 training.

---

### Problem 28 — Use channels_last for conv models

**Solution.**
```python
model = model.to(device, memory_format=torch.channels_last)
# in the loop:
X = X.to(device, non_blocking=True, memory_format=torch.channels_last)
```

**Why.** NCHW is PyTorch's default but cuDNN's tensor cores prefer NHWC. Switching layout gives 10–30% speedup on Ampere+.

**Real-world.** Free win on ResNet/EfficientNet/UNet — but profile to confirm.

**Follow-ups.** Combine with `torch.compile(model)`.

---

### Problem 29 — `torch.compile` your model

**Solution.**
```python
model = torch.compile(model)        # default mode is 'default' = TorchInductor
# more aggressive:
model = torch.compile(model, mode="max-autotune")
```

First batch is slower (compile time); subsequent batches are 20–50% faster.

**Caveats.**
- Re-compiles when input shapes change drastically — pad inputs.
- Works best with static graphs; some control flow is supported but slows compilation.
- Save / load: compiled models pickle the original module; load and re-compile.

**Real-world.** As of 2026, `torch.compile` is mature for most models. Try it; benchmark.

---

### Problem 30 — Profile a training step

**Solution.**
```python
import torch
from torch.profiler import profile, ProfilerActivity, schedule

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    schedule=schedule(wait=1, warmup=1, active=3),
    record_shapes=True, with_stack=True,
) as prof:
    for step, (X, y) in enumerate(loader):
        if step >= 5: break
        out = model(X.to(device)); loss = criterion(out, y.to(device))
        loss.backward(); optimizer.step(); optimizer.zero_grad()
        prof.step()

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=20))
prof.export_chrome_trace("trace.json")    # open in chrome://tracing
```

**Real-world.** First, simple `time.time()` around the step to know if it's slow. Then profiler when you need to know *which* op.

**Follow-ups.** PyTorch Profiler Tensorboard plugin; nsys for full GPU traces.

---

### Problem 31 — Overfit a single batch (the diagnostic)

**Solution.** (See §12.1.)

```python
X, y = next(iter(train_loader))
X, y = X[:4].to(device), y[:4].to(device)
model.train()
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
for step in range(500):
    opt.zero_grad(set_to_none=True)
    loss = criterion(model(X), y)
    loss.backward(); opt.step()
    if step % 50 == 0: print(step, loss.item())
# expected: loss → ~0
```

**If it doesn't drop to ~0:**
- Loss/output mismatch (e.g., one-hot targets with CrossEntropyLoss).
- Wrong shapes silently broadcasting.
- Frozen parameters (`requires_grad=False` on the wrong things).
- Output saturation (final activation killing gradient).

**Real-world.** First debugging step before any other tuning. Shaves hours off "my model isn't learning."

---

### Problem 32 — Detect NaN / Inf in training

**Solution.**
```python
def has_nan_or_inf(tensor: torch.Tensor) -> bool:
    return bool(torch.isnan(tensor).any() or torch.isinf(tensor).any())

# inside the loop, after backward:
for name, p in model.named_parameters():
    if p.grad is not None and has_nan_or_inf(p.grad):
        print(f"NaN/Inf in {name}.grad — pause and inspect")
        torch.autograd.set_detect_anomaly(True)
        break
```

**Common fixes:**
- Lower LR by 10×.
- Add gradient clipping (`clip_grad_norm_(params, 1.0)`).
- Switch fp16 → bf16.
- Add `eps` to divisions (`x / (y + 1e-6)`).
- Verify input data has no NaN.

**Real-world.** Single most common training failure mode. Always add a guard early.

---

### Problem 33 — Visualize a batch (data sanity check)

**Solution.**
```python
import matplotlib.pyplot as plt
X, y = next(iter(train_loader))
mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
std  = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
fig, axs = plt.subplots(2, 4, figsize=(12, 6))
for ax, img, label in zip(axs.flat, X[:8], y[:8]):
    img = (img.cpu() * std + mean).clamp(0, 1).permute(1, 2, 0).numpy()
    ax.imshow(img); ax.set_title(int(label.item())); ax.axis("off")
```

**Real-world.** "My model isn't learning" is most often "my data pipeline is broken." Visualizing 5 augmented examples almost always exposes the bug — extreme augmentation, BGR/RGB swap, label/input mismatch.

**Follow-ups.** WandB / TensorBoard image logging during training.

---

### Problem 34 — DDP setup for 4 GPUs on one node

**Solution.** (See §10.2 for full code.)

Launch:
```bash
torchrun --nproc-per-node=4 train.py
```

Inside `train.py`:
```python
import os, torch, torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

dist.init_process_group(backend="nccl")
local_rank = int(os.environ["LOCAL_RANK"])
torch.cuda.set_device(local_rank)
device = torch.device(f"cuda:{local_rank}")

model = MyModel().to(device)
model = DDP(model, device_ids=[local_rank])

sampler = DistributedSampler(train_ds)
loader = DataLoader(train_ds, batch_size=64, sampler=sampler, pin_memory=True, num_workers=4)

optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
for epoch in range(epochs):
    sampler.set_epoch(epoch)            # ← critical
    for X, y in loader:
        ...
    if dist.get_rank() == 0:            # only rank 0 saves
        torch.save(model.module.state_dict(), f"epoch{epoch}.pt")

dist.destroy_process_group()
```

**Real-world.** Effective batch size = `batch_size_per_gpu × num_gpus`. Adjust LR accordingly (linear scaling rule: 2× GPUs ≈ 2× LR; with warmup).

**Follow-ups.** FSDP for >1B param models. Mixed precision works inside DDP unchanged.

---

### Problem 35 — Save state_dict + load in a fresh process

**Solution.**
```python
# train.py
torch.save(model.state_dict(), "model.pt")

# serve.py — fresh process, doesn't import training script
import torch
import torch.nn as nn

class MyModel(nn.Module):
    """Architecture must be importable in serve.py."""
    ...

model = MyModel()
model.load_state_dict(torch.load("model.pt", map_location="cpu", weights_only=True))
model.eval()
```

**Real-world.** Production serving images often differ from training (no datasets, no augmentations). Importing only the architecture keeps the serving image small.

**Follow-ups.** safetensors format (no pickle, faster, mmap-friendly). Versioned model registry (Module 12).

---

### Problem 36 — Export to ONNX and run with onnxruntime

**Solution.**
```python
import torch
import torch.onnx

model.eval()
example = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model, example, "model.onnx",
    input_names=["input"], output_names=["logits"],
    dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    opset_version=20,
)
```

```python
# serve with onnxruntime — no PyTorch needed
import onnxruntime as ort
import numpy as np
sess = ort.InferenceSession("model.onnx", providers=["CPUExecutionProvider"])
X_np = np.random.randn(8, 3, 224, 224).astype(np.float32)
out = sess.run(["logits"], {"input": X_np})[0]
```

**Real-world.** ONNX is the cross-framework lingua franca. Often 1.5–3× faster on CPU than PyTorch eager. Mobile, embedded, browser deployments use it.

**Follow-ups.** TensorRT for NVIDIA GPU optimization (5–20× speedup over ONNX). OpenVINO for Intel CPU.

---

## 16. Three mini-projects

### Mini-project A — A complete tabular DL model
Take the same churn dataset from Module 7. Build a 3-layer MLP with batchnorm and dropout. Compare against LightGBM honestly: same splits, same metrics, same Optuna budget. Document where DL wins, where it loses (likely it loses on AUC; possibly wins if you have lots of categorical embeddings).

**Skills exercised:** §3, §5, §6 — shows that DL isn't always the answer for tabular.

### Mini-project B — Image classifier with transfer learning
A 10-class image dataset (CIFAR-10 if needed). Fine-tune ResNet50 in two stages (head-only then full). Add CutMix augmentation. Evaluate top-1 and top-5. Save TorchScript + ONNX exports. Serve via FastAPI on CPU; benchmark p50/p95 latency.

**Skills exercised:** §4, §8, §9, §13. End-to-end vision model.

### Mini-project C — DDP training on synthetic data
Set up a 4-GPU DDP trainer (or simulate with 4 CPU processes via gloo backend) for an MLP. Compare wall-clock speedup vs single GPU. Add bf16 mixed precision. Add gradient accumulation. Verify the result matches single-GPU training to within numerical noise.

**Skills exercised:** §9, §10. Foundation for distributed work.

---

## 17. Real-world usage map

| Concept | Where it returns later |
|---|---|
| `nn.Module` + training loop | Every model in Modules 9-11 follows this template |
| Transfer learning | Module 9 (NLP), Module 10 (LLM fine-tuning) |
| Mixed precision | LLM training in Module 10 (essential at >1B params) |
| DDP / FSDP | LLM pretraining and large-scale fine-tuning |
| `torch.compile` | Inference speedup throughout serving |
| Gradient accumulation | Big-batch training when GPU memory is the constraint |
| Lightning | Production ML training pipelines (Module 12) |
| TorchScript / ONNX | Cross-framework serving in Modules 12, 13 |
| Profiler | Diagnosing training-loop bottlenecks anywhere |
| Custom Dataset | Streaming RAG datasets, multi-modal inputs (Module 10) |
| Activation checkpointing | LLM training to fit larger models on a single GPU |

---

## 18. Interview pitfalls — what NOT to say

- **"Deep learning is always better than tree models on tabular data."** Almost never true in 2026. Defend the choice based on the data shape.
- **"`Adam` is the same as `AdamW`."** No — AdamW decouples weight decay; default for transformers.
- **"I'll just use a learning rate of 0.001."** Magnitude matters; don't quote a single value without context. Different for fine-tuning vs from-scratch.
- **"BatchNorm everywhere."** It hurts at small batches and in transformers. Use LayerNorm or GroupNorm there.
- **"`requires_grad=False` is enough to freeze."** Also pass only the trainable params to the optimizer (some optimizers' state is per-param).
- **"I store losses in a list."** With grad-tracked tensors, that's a memory leak. `.item()` first.
- **"`.cuda()` everywhere."** `.to(device)` — let environment decide.
- **"I trained for 100 epochs because more is better."** Early stopping; keep the best by val metric.
- **"My model isn't learning so I'll add more layers."** Almost certainly wrong. Run "overfit one batch" first; then check data.
- **"I'll save the whole model with `torch.save(model)`."** Save state_dict only; rebuild architecture in serving code.
- **"I can use `requests` inside an async route."** (Module 4 territory.) Same kind of trap recurs in serving with `pickle.load(weights)` from untrusted sources — use `weights_only=True`.
- **"Deep learning needs a million examples."** Not with transfer learning. 1k labeled images often suffice.
- **"I tested on the train set."** Or worse, "I trained on the test set." Same Module 7 sins.

**How to communicate.** In a DL interview, narrate (1) data and target shape, (2) baseline (linear model, GBM), (3) architecture choice, (4) loss + optimizer + schedule, (5) regularization and augmentation, (6) train/val/test discipline (no leakage), (7) debugging (overfit one batch first), (8) serialization + serving plan.

---

## 19. Cheatsheet

```text
TENSORS
  torch.tensor / .from_numpy / .zeros / .ones / .arange / .linspace / .randn
  .shape .dtype .device .ndim
  .to(device, non_blocking=True), .to(dtype=torch.bfloat16)
  .reshape / .view / .permute / .flatten / .squeeze / .unsqueeze
  same broadcasting rules as numpy; PyTorch uses dim, not axis

AUTOGRAD
  requires_grad=True for leaf tensors that need gradients
  loss.backward()        # populates .grad
  optimizer.zero_grad(set_to_none=True)
  with torch.no_grad():  # disables autograd
  with torch.inference_mode():  # even faster
  loss.item()  / .detach()  for logging without leaking the graph

nn.MODULE
  class Net(nn.Module):
      def __init__(self):
          super().__init__()
          self.layers = nn.Sequential(...)
      def forward(self, x): return self.layers(x)
  model.train() / model.eval()
  model.parameters() / .named_parameters()
  model.state_dict() / model.load_state_dict(d)

LAYERS
  Linear, Conv2d (kernel_size, stride, padding), ConvTranspose2d
  BatchNorm1d/2d, LayerNorm, GroupNorm
  Dropout, Dropout2d
  Embedding, LSTM/GRU, MultiheadAttention, TransformerEncoder

LOSSES (use *WithLogitsLoss when possible)
  CrossEntropyLoss        (multi-class; logits in, long target)
  BCEWithLogitsLoss       (binary or multi-label; logits in, float target)
  MSELoss / SmoothL1Loss / L1Loss  (regression)

OPTIMIZERS / SCHEDULERS
  AdamW(lr=3e-4, weight_decay=0.01)         # transformers default
  SGD(lr=0.1, momentum=0.9, weight_decay=5e-4)  # CNN from-scratch
  CosineAnnealingLR / OneCycleLR / ReduceLROnPlateau / SequentialLR(warmup+cosine)
  per-batch step for OneCycleLR/Cosine; per-epoch for StepLR/Plateau

DATA
  Dataset: __init__, __len__, __getitem__
  DataLoader(ds, batch_size, shuffle, num_workers, pin_memory, persistent_workers)
  pad_collate / pack_padded_sequence for variable-length
  WeightedRandomSampler for imbalance

TRAINING LOOP (the canonical form)
  for X, y in loader:
      X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
      optimizer.zero_grad(set_to_none=True)
      out = model(X); loss = criterion(out, y)
      loss.backward()
      torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
      optimizer.step()
  ALWAYS: model.train()/.eval(); zero_grad; .item() for logs

MIXED PRECISION (CUDA)
  fp16 path:
    scaler = GradScaler()
    with autocast(device_type="cuda", dtype=torch.float16): loss = ...
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer); clip_grad_norm_(...)
    scaler.step(optimizer); scaler.update()
  bf16 path: just autocast(dtype=torch.bfloat16); no scaler needed

PERFORMANCE
  channels_last memory format for conv (Ampere+)
  torch.compile(model) — 20-50% speedup
  gradient accumulation: loss /= K; backward; step every K
  activation checkpoint for huge models
  pin_memory=True + non_blocking=True

DDP (single-node multi-GPU)
  torchrun --nproc-per-node=N train.py
  dist.init_process_group(backend="nccl")
  model = DDP(model, device_ids=[local_rank])
  sampler.set_epoch(epoch)            # critical
  if rank == 0: save / log

DEBUGGING
  overfit one batch as the first check
  print shapes after each layer with forward hook
  torch.autograd.set_detect_anomaly(True) for NaN
  log gradient norms; visualize a batch; check class balance
  CrossEntropyLoss expects LOGITS in and LONG class indices

TRANSFER LEARNING
  weights = ResNet50_Weights.DEFAULT
  model = resnet50(weights=weights)
  model.fc = nn.Linear(model.fc.in_features, n)
  preprocess = weights.transforms()    # match training preprocessing
  freeze backbone for stage 1; differential LR for stage 2

SAVE/LOAD
  torch.save({"model_state_dict":..., "optimizer_state_dict":..., "epoch":..., "rng":...},"ckpt.pt")
  ckpt = torch.load("ckpt.pt", map_location="cpu", weights_only=True)
  model.load_state_dict(ckpt["model_state_dict"])
  state_dict pattern, never pickle entire module

DEPLOY
  TorchScript: torch.jit.script(model).save("m.pt")
  ONNX: torch.onnx.export(model, example, "m.onnx", dynamic_axes=..., opset_version=20)
  Serve via FastAPI: load once at startup, batch requests, @torch.inference_mode()

ANTI-PATTERNS (avoid)
  forgetting train()/eval(); missed zero_grad; .forward() direct
  Sigmoid+BCELoss (use BCEWithLogitsLoss); Softmax+NLLLoss (use CrossEntropyLoss)
  one-hot targets for CrossEntropyLoss; appending loss tensors to lists
  saving full model not state_dict; pickle untrusted weights
  plain Adam not AdamW; missed warmup for transformers
  BatchNorm at small batch; cuda() instead of .to(device)
  num_workers=0 with big data; pin_memory=False on GPU
```

---

## 20. Prerequisites & next steps

**Prerequisites covered? You can:**
- Manipulate tensors, move them between devices, and reason about autograd.
- Build an `nn.Module` with the right layer choices, init, and counts.
- Write a correct training loop with `.train()` / `.eval()`, `zero_grad`, gradient clipping, and metric tracking.
- Pick optimizer + LR + scheduler appropriate to the problem (transformers vs CNN, from-scratch vs fine-tune).
- Use transfer learning the right way: freeze, train head, unfreeze, differential LR.
- Profile and fix data-loader bottlenecks; enable mixed precision; use `torch.compile`.
- Set up DDP for multi-GPU on a single node.
- Use Lightning when you want clean code with multi-GPU/precision/logging baked in.
- Debug models — overfit one batch, watch shapes, watch gradients, visualize a batch.
- Save and load state_dicts robustly; export to TorchScript / ONNX; serve via FastAPI.

**Next steps in the bible:**
- **Module 9 — NLP & CV.** Transformers via Hugging Face, vision foundation models, audio basics. Most production "AI" runs on these.
- **Module 10 — LLMs.** Fine-tuning, LoRA/QLoRA, RAG, vLLM serving. The post-2023 frontier.
- **Module 11 — Agents.** LangGraph, CrewAI, tool use, agent loops.
- **Module 12 — MLOps.** Pipelines, registries, monitoring, drift detection.

**External study (only if you want depth):**
- *Deep Learning* (Goodfellow, Bengio, Courville) — the theory canon; chapters 6–9 are the foundation.
- *Dive into Deep Learning* (d2l.ai) — free, runnable, MIT–Berkeley collaboration; PyTorch + JAX + TF.
- The PyTorch tutorials site — surprisingly polished; the "blitz" is the canonical first read.
- The fastai book and course — pragmatic, covers transfer learning + LR finder + CutMix etc.

---

*End of Module 8. Module 9 covers NLP & Computer Vision — Hugging Face transformers, fine-tuning, vision foundation models, multimodal — same structure, 35+ problems.*
