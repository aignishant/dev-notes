# 👁️ CNNs & Vision

!!! abstract "Module Scope"
    From the convolution operation to modern vision architectures. Questions **Q21–Q40**. Expect CNN interviews to test both the math of convolutions (receptive field, output shape, padding) and the architectural history (AlexNet → VGG → ResNet → EfficientNet → ViT). Knowing *why* each architecture beat the last is the senior signal.

---

## Q21. The convolution operation — derive output shape and receptive field { #q21 }

<span class="q-badge">Foundational • Must Know</span>

A 2D convolution with kernel $K \times K$, input $(H, W)$, stride $S$, padding $P$, dilation $D$ produces output:

$$H' = \left\lfloor \frac{H + 2P - D(K-1) - 1}{S} \right\rfloor + 1$$

Same formula for $W'$. Memorize this — it comes up constantly.

**Three convolutional "modes"**:

| Mode | Padding | Output shape |
|---|---|---|
| **Valid** | 0 | $H' = H - K + 1$ (shrinks) |
| **Same** | $P = (K-1)/2$ if odd kernel, stride 1 | $H' = H$ (preserves) |
| **Full** | $P = K - 1$ | $H' = H + K - 1$ (grows) |

**Receptive field** — how much of the input one output unit "sees":

After a stack of conv layers, receptive field grows:
$$\text{RF}_\ell = \text{RF}_{\ell-1} + (K_\ell - 1) \prod_{i < \ell} S_i$$

With kernel=3, stride=1 the receptive field grows by 2 per layer: 1 → 3 → 5 → 7...

**Effective receptive field** (ERF) is typically smaller than theoretical — gradient contribution decays with a Gaussian-like profile centered in the patch (Luo et al., 2017). Practical implication: very deep nets don't always "see" the whole image even when theoretical RF covers it.

```python
def conv_output_shape(H, K, S=1, P=0, D=1):
    return (H + 2*P - D*(K-1) - 1) // S + 1

# Example: 224 input, 7x7 kernel, stride 2, padding 3
# (224 + 6 - 6 - 1) // 2 + 1 = 112
```

<div class="tip-box" markdown>
**Interviewer exercise:** "If I want the output to be half the input size, what stride/padding do I use?" Answer: stride 2, kernel 3, padding 1 — this gives $\lfloor (H + 2 - 2) / 2 \rfloor + 1 = H/2$. Memorize this combination; it's used in every downsampling stage.
</div>

---

## Q22. Why convolutions over fully-connected? Parameter sharing and translation equivariance { #q22 }

<span class="q-badge">Conceptual • Must Know</span>

Fully-connected (FC) layer between a $224 \times 224 \times 3$ image and a 1000-unit hidden layer: $224^2 \times 3 \times 1000 \approx 150$M params.

Single conv with 64 filters of size $3 \times 3 \times 3$: $64 \times 3 \times 3 \times 3 = 1{,}728$ params.

Five orders of magnitude fewer. Two reasons why this isn't just parameter efficiency:

**1. Parameter sharing.** The same filter is applied at every spatial location. Learning an edge detector in the top-left corner automatically learns it for the bottom-right.

**2. Translation equivariance.** Shift the input, the output shifts the same way: $f(\text{shift}(x)) = \text{shift}(f(x))$. (Exact equivariance only without padding edge effects, but near enough in practice.) This matches the structure of images — a cat is a cat anywhere in the frame.

**3. Local connectivity.** Each output unit depends on a small spatial neighborhood of the input, encoding the prior that nearby pixels are more related than distant pixels.

These three together = the CNN inductive bias. They let CNNs learn with much less data than FC networks because they don't need to discover translation invariance from scratch.

**When FC still wins**:

- Final classification head (needs to mix all features globally).
- Small-input tabular data (no spatial structure to exploit).

**What breaks equivariance**:

- Padding (edge effects).
- Pooling (especially max-pool — not exactly equivariant).
- BN (running statistics).

<div class="tip-box" markdown>
**Interviewer gotcha:** "Is convolution translation invariant?" No — it's **equivariant**, not invariant. Invariance (output unchanged under shift) is achieved at the *end* of the network via global pooling. Equivariance just means the output shifts with the input — not the same thing.
</div>

---

## Q23. Pooling — max, average, global, and why strided conv replaced it { #q23 }

<span class="q-badge">Foundational</span>

**Max pooling**: $y = \max_{(i,j) \in \text{window}} x_{ij}$. Selects the strongest activation — translation tolerance (small shifts still pick the same max).

**Average pooling**: $y = \text{mean}(\cdot)$. Smoother, commonly used in global-pooling at end of network.

**Why pooling**:

1. **Downsampling** — shrink spatial dimension, grow receptive field, reduce compute for later layers.
2. **Translation tolerance** — small shifts don't change the max.
3. **Some scale invariance** — pooling larger regions handles objects at different sizes.

**Global average pooling (GAP)** — pools each channel down to a single number. Used at the end of modern CNNs (ResNet, etc.) instead of flattening into an FC layer:

- **No parameters** → less overfitting.
- **Size-independent** — works on any input size.
- **Forces channels to encode class information** (acts as a regularizer).

**Strided convolution** replaces pooling in modern architectures (ResNet, EfficientNet). A conv with stride 2 downsamples while simultaneously transforming features — fewer layers, more learnable, comparable or better results.

| Downsampling | Pros | Cons |
|---|---|---|
| Max pool | Non-learnable, translation tolerant | Loses info, not invertible |
| Avg pool | Smooth | Blurs sharp features |
| Strided conv | Learnable, merges ops | More params, slight overhead |
| Dilated conv | Grows RF without downsampling | Stride 1 but equivalent coverage |

```python
# Modern CNN block: strided conv replaces max pool
nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)  # halve H, W

# Classical block: conv + pool
nn.Sequential(
    nn.Conv2d(64, 128, kernel_size=3, padding=1),
    nn.MaxPool2d(2)
)
```

<div class="tip-box" markdown>
**Interviewer tip:** "Why did ResNet keep the max pool?" ResNet-50's first stage has stride-2 conv (7×7, stride 2) followed by max pool (3×3, stride 2) — that's 4x downsampling before any residual blocks. Modern variants like ResNet-D replace these with all-conv alternatives. Getting this detail right signals that you've actually read the papers.
</div>

---

## Q24. 1×1 convolution — why it's everywhere { #q24 }

<span class="q-badge">Underrated</span>

A $1 \times 1$ convolution looks useless (one pixel!) but is genuinely one of the most versatile tools in CNN architecture:

**1. Dimensionality reduction / expansion** along the channel dimension.

A $1 \times 1$ conv with $C_{\text{in}} = 256$, $C_{\text{out}} = 64$ reduces 256-channel features to 64 channels — like a per-pixel linear projection.

**2. Adds nonlinearity without changing spatial resolution.**

$1 \times 1$ conv → ReLU → $3 \times 3$ conv: inserts a nonlinearity mid-block without spatial downsampling.

**3. Enables the "bottleneck" block** (ResNet-50+):
```
 256 ch → 1x1 conv → 64 ch → 3x3 conv → 64 ch → 1x1 conv → 256 ch
         (reduce)             (process)             (expand)
```
Reduces params and FLOPs dramatically vs a direct $3 \times 3$ conv on 256 channels.

**4. Cross-channel mixing.** The $3 \times 3$ conv mixes spatially; $1 \times 1$ conv mixes across channels. Together they decouple spatial and channel mixing (this insight led to depthwise separable convs).

**Formally**: a $1 \times 1$ conv with $C_{\text{in}}$ input and $C_{\text{out}}$ output channels is equivalent to applying the same learnable linear transformation $W \in \mathbb{R}^{C_{\text{out}} \times C_{\text{in}}}$ at each spatial location.

```python
# Bottleneck block (ResNet-50 style)
class Bottleneck(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        mid = out_ch // 4
        self.conv1 = nn.Conv2d(in_ch, mid, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(mid)
        self.conv2 = nn.Conv2d(mid, mid, 3, stride, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(mid)
        self.conv3 = nn.Conv2d(mid, out_ch, 1, bias=False)
        self.bn3 = nn.BatchNorm2d(out_ch)
        # ... residual connection
```

<div class="tip-box" markdown>
**Fun fact:** 1×1 convs debuted in the Network-in-Network paper (Lin et al., 2013) and became mainstream via GoogLeNet's Inception module. Many architectures are essentially dance patterns of 1×1 and 3×3 convs.
</div>

---

## Q25. Depthwise separable convolutions — MobileNet's core trick { #q25 }

<span class="q-badge">Practical</span>

A standard $K \times K$ conv with $C_{\text{in}}$ input and $C_{\text{out}}$ output channels computes:

$$\text{FLOPs} = C_{\text{in}} \times C_{\text{out}} \times K^2 \times H \times W$$

**Depthwise separable conv** decomposes this into two cheaper steps:

**1. Depthwise conv**: one $K \times K$ filter per input channel (no channel mixing):
$$\text{FLOPs}_{\text{depthwise}} = C_{\text{in}} \times K^2 \times H \times W$$

**2. Pointwise conv** ($1 \times 1$): mixes channels:
$$\text{FLOPs}_{\text{pointwise}} = C_{\text{in}} \times C_{\text{out}} \times H \times W$$

**Total**: 
$$\text{Total} = C_{\text{in}} \times H \times W (K^2 + C_{\text{out}})$$

**Reduction ratio** vs standard conv:
$$\frac{K^2 + C_{\text{out}}}{K^2 C_{\text{out}}} = \frac{1}{C_{\text{out}}} + \frac{1}{K^2}$$

For $K=3, C_{\text{out}}=128$: ratio $\approx 1/128 + 1/9 \approx 0.12$ — 8× fewer FLOPs.

This is what makes **MobileNet** (Howard et al., 2017), **Xception**, and **EfficientNet** practical on phones.

```python
class DepthwiseSeparableConv(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        self.depthwise = nn.Conv2d(
            in_ch, in_ch, kernel_size=3, stride=stride,
            padding=1, groups=in_ch, bias=False  # groups=in_ch = depthwise
        )
        self.pointwise = nn.Conv2d(in_ch, out_ch, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(in_ch)
        self.bn2 = nn.BatchNorm2d(out_ch)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.relu(self.bn1(self.depthwise(x)))
        x = self.relu(self.bn2(self.pointwise(x)))
        return x
```

**Tradeoff**: cheaper but slightly less expressive — usually a fine trade when compute is scarce (mobile, edge). For unconstrained compute, standard convs still win in raw accuracy per parameter.

<div class="scenario" markdown>
**Scenario:** Deploying a vision model on a $50 phone.<br>
**Answer:** Start with **MobileNet-V3** or **EfficientNet-Lite** — both use depthwise separable. Apply **INT8 quantization** (PyTorch Mobile / TFLite) for another 2-4× speedup. Measure on-device latency, not FLOPs — memory bandwidth and kernel overhead often dominate on mobile.
</div>

---

## Q26. AlexNet → VGG → GoogLeNet — the pre-residual CNN era { #q26 }

<span class="q-badge">History</span>

**AlexNet (2012)** — Krizhevsky, Sutskever, Hinton. The paper that started modern deep learning:

- 8 layers (5 conv, 3 FC). 60M params.
- **ReLU** (faster training than tanh).
- **Dropout** (FC layers).
- **Data augmentation** (random crops, flips, color jitter).
- Trained on 2 GPUs with model parallelism — split layers across GPUs.
- Won ImageNet 2012 by ~10% absolute — the shock that killed handcrafted feature engineering.

**VGG (2014)** — Simonyan & Zisserman:

- Up to 19 layers. **Uniform $3 \times 3$ convs** throughout.
- Insight: two $3\times 3$ convs = one $5 \times 5$ RF with fewer params. Three $3 \times 3$ = one $7 \times 7$.
- Structural simplicity made it popular as a feature extractor.
- 138M params (VGG-16) — huge, mostly in FC layers.

**GoogLeNet / Inception (2014)** — Szegedy et al.:

- 22 layers but only ~7M params (vs VGG's 138M).
- **Inception module**: parallel branches of different kernel sizes ($1\times1$, $3\times3$, $5\times5$, max-pool), concatenated.
- **$1\times1$ convs for dimensionality reduction** before expensive $3\times3$ and $5\times5$ — the "bottleneck" idea before ResNet.
- No FC layers — global average pooling at end.

**What they all lacked**: a way to train beyond ~30 layers. Adding depth hurt performance (degradation, not overfitting — train error *rose*). This was the problem ResNet solved.

| Model | Depth | Params | Top-5 error |
|---|---|---|---|
| AlexNet | 8 | 60M | 16.4% |
| VGG-16 | 16 | 138M | 7.3% |
| GoogLeNet | 22 | 7M | 6.7% |
| ResNet-152 | 152 | 60M | 3.6% |

<div class="tip-box" markdown>
**Interviewer trivia:** "Why did they use 3×3 convs in VGG specifically?" Two 3×3 convs have the same receptive field as one 5×5, but with fewer params ($2 \times 9 = 18$ vs $25$) and two nonlinearities instead of one. The insight — "deeper with smaller kernels" — became the universal best practice.
</div>

---

## Q27. ResNet — why residual connections changed everything { #q27 }

<span class="q-badge">Foundational • Must Know</span>

**The degradation problem (He et al., 2015)**: adding layers to a plain CNN beyond ~30 layers *increased* training error. Not overfitting (train error rose), not vanishing gradients (BN was there), but an optimization issue — identity mappings are hard to learn through deep nonlinear stacks.

**Residual block**:

$$\mathbf{y} = F(\mathbf{x}, W) + \mathbf{x}$$

Where $F$ is a few conv layers. The **skip connection** $+\mathbf{x}$ forces the block to learn the *residual* (delta from identity) instead of a full transformation.

**Why this fixes degradation**:

1. **Identity is free.** If $F \to 0$, the block is the identity — adding a block can't hurt, so deeper is at worst equal to shallower.
2. **Gradient flow.** Backprop through the skip connection is a plain addition — gradient arrives at earlier layers unattenuated.

   $$\frac{\partial L}{\partial \mathbf{x}} = \frac{\partial L}{\partial \mathbf{y}} \left(1 + \frac{\partial F}{\partial \mathbf{x}}\right)$$
   
   That `1` is the key — even if the $\partial F / \partial \mathbf{x}$ term shrinks, gradient can still propagate through the identity path.
3. **Loss landscape smoothing.** Empirically, residual nets have much smoother loss landscapes (Li et al., 2018) — making SGD easier.

```python
class BasicBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, 1, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_ch)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_ch != out_ch:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, stride, bias=False),
                nn.BatchNorm2d(out_ch)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)                  # skip connection
        return F.relu(out)
```

**Variants**:

- **ResNet-18 / 34**: basic blocks (two $3\times3$ convs).
- **ResNet-50 / 101 / 152**: bottleneck blocks ($1\times1 \to 3\times3 \to 1\times1$).
- **ResNeXt**: group convolutions inside bottleneck.
- **Wide ResNet**: fewer but wider layers.

<div class="tip-box" markdown>
**Senior-level insight:** ResNet works not because it's "deeper" but because it makes deep optimization **tractable**. This same principle — gradient-friendly skip connections — appears in transformers (residual around every sublayer), UNet (skip connections across encoder/decoder), LSTMs (cell state). Residual is a core 2020s DL primitive.
</div>

---

## Q28. Batch normalization in CNNs — practical gotchas { #q28 }

<span class="q-badge">Practical</span>

BN is standard in CNNs, but there's nuance.

**Where does BN go?** The convention is:

```
Conv → BN → ReLU
```

Some architectures (pre-activation ResNet, PreAct-ResNet) use:

```
BN → ReLU → Conv
```

Pre-activation has cleaner gradient paths and empirically helps deeper networks.

**Removing bias from conv before BN**: since BN re-centers the output, the conv's bias becomes redundant. Standard PyTorch pattern: `Conv2d(..., bias=False)` before BN.

**Inference mode**: BN uses *running statistics* (exponential moving averages from training). Always call `model.eval()` before inference — forgetting this uses the current batch's statistics and gives garbage results with batch size 1.

```python
model.eval()               # switches BN, Dropout to eval mode
with torch.no_grad():       # disables autograd to save memory
    preds = model(x)
```

**Sync BatchNorm for multi-GPU**: vanilla BN normalizes per-GPU (shard of the batch). Statistics differ across GPUs → noisy. `nn.SyncBatchNorm` syncs stats across all GPUs, matching what single-GPU BN would do.

**Batch size problems**:

| Batch size | BN behavior |
|---|---|
| 1 (fine-tune) | Running stats only; batch stats meaningless |
| 2–8 | Noisy batch stats → unstable training |
| 16–64 | BN works well |
| 1000+ (large-scale) | BN running stats stale unless carefully tracked |

**When to disable BN during fine-tuning**:

- You're fine-tuning with a small batch on pretrained weights.
- Freezing BN (`track_running_stats=False` and `eval()` mode) preserves pretrained statistics.

<div class="scenario" markdown>
**Scenario:** You ship a model to production. Latency explodes on batch size 1 requests.<br>
**Answer:** Possible causes: (1) forgot `model.eval()` — BN computes batch stats from 1 sample, gives bad outputs. (2) Forgot `with torch.no_grad()` — allocates gradient memory. (3) Model in FP32 when FP16/INT8 would be sufficient. The eval()+no_grad pair is essential inference discipline.
</div>

---

## Q29. Dilated / atrous convolutions — RF without downsampling { #q29 }

<span class="q-badge">Specialized</span>

**Dilated convolution** skips pixels in the kernel — a $3\times3$ kernel with dilation $D$ covers a $(K-1) \cdot D + 1$ spatial extent while using only 9 parameters.

$$y[i,j] = \sum_{m,n} w[m,n] \cdot x[i + Dm, j + Dn]$$

For $D = 2$, the kernel covers a $5\times5$ region; $D = 4$ covers $9\times9$.

**Why it's useful**:

- **Exponential receptive field** without losing spatial resolution (no downsampling).
- Essential for **semantic segmentation**: need pixel-wise predictions, can't downsample.
- **DeepLab** (Chen et al., 2016) used atrous convolutions + Atrous Spatial Pyramid Pooling (ASPP) to achieve SOTA segmentation.

**Tradeoffs**:

- Introduces **gridding artifacts** — adjacent output pixels may depend on disjoint sets of input pixels (if dilations aren't chosen carefully).
- More memory than strided conv because spatial dim doesn't shrink.

**Use cases**:

1. **Semantic segmentation** (DeepLab, UNet variants).
2. **Audio generation** (WaveNet — dilated 1D convs give efficient long receptive field over audio samples).
3. **Dense prediction tasks** generally.

```python
# DeepLab-style ASPP (Atrous Spatial Pyramid Pooling)
class ASPP(nn.Module):
    def __init__(self, in_ch, out_ch, rates=(6, 12, 18)):
        super().__init__()
        self.conv1x1 = nn.Conv2d(in_ch, out_ch, 1)
        self.dilated_convs = nn.ModuleList([
            nn.Conv2d(in_ch, out_ch, 3, padding=r, dilation=r)
            for r in rates
        ])
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.pool_conv = nn.Conv2d(in_ch, out_ch, 1)
        self.project = nn.Conv2d(out_ch * (len(rates) + 2), out_ch, 1)

    def forward(self, x):
        h, w = x.shape[2:]
        feats = [self.conv1x1(x)]
        feats += [c(x) for c in self.dilated_convs]
        gp = F.interpolate(self.pool_conv(self.global_pool(x)), (h, w))
        feats.append(gp)
        return self.project(torch.cat(feats, dim=1))
```

<div class="tip-box" markdown>
**Interviewer tip:** WaveNet (DeepMind, 2016) stacks dilated convs with exponentially increasing dilation (1, 2, 4, 8, ..., 512) — a single stack sees 1024 past samples with only 10 layers. This trick enabled raw audio generation. Dilated convs are a deep example of using architecture to encode task structure (long-range temporal dependencies).
</div>

---

## Q30. Transposed convolution — upsampling learnably { #q30 }

<span class="q-badge">Specialized</span>

**Transposed convolution** (a.k.a. "deconvolution", "fractionally-strided convolution") learns a learnable upsampling — the operational inverse of a strided conv's spatial shape change.

**Output shape** for input $(H, W)$, kernel $K$, stride $S$, padding $P$:
$$H' = (H - 1) S - 2P + K$$

**Use cases**:

1. **Semantic segmentation** — upsampling encoded features back to input resolution (UNet decoder).
2. **Generative models** — transforming a latent vector into an image (DCGAN).
3. **Super-resolution** — learned upsampling.

```python
# Double spatial size
up = nn.ConvTranspose2d(
    in_channels=256, out_channels=128,
    kernel_size=4, stride=2, padding=1
)
x = torch.randn(1, 256, 16, 16)
y = up(x)  # (1, 128, 32, 32)
```

**Checkerboard artifacts** — a notorious failure mode. When kernel size isn't divisible by stride, output pixels receive different numbers of kernel contributions → visible checkerboard pattern in generated images. Fix: use kernel size that's a multiple of stride (e.g., kernel=4, stride=2), or use **pixel shuffle / sub-pixel conv**, or use bilinear upsample + 1×1 conv.

**Pixel shuffle (sub-pixel convolution)** — alternative learnable upsampling:

1. Conv produces $C \cdot r^2$ channels.
2. Rearrange channels to spatial dimensions (factor $r$).

No checkerboard, fewer parameters, used in super-resolution nets.

```python
# Upsample by factor of 2 using pixel shuffle
upsample = nn.Sequential(
    nn.Conv2d(64, 256, 3, 1, 1),  # 256 = 64 * 4 (factor 2²)
    nn.PixelShuffle(2)             # (N, 256, H, W) → (N, 64, 2H, 2W)
)
```

<div class="tip-box" markdown>
**"Deconvolution" pet peeve:** transposed conv is **not** the mathematical inverse of conv. It's the adjoint — matching shapes, not recovering the input. Don't call it "deconvolution" in front of rigorous interviewers.
</div>

---

## Q31. UNet and encoder-decoder CNNs — segmentation architecture { #q31 }

<span class="q-badge">Applied</span>

**UNet** (Ronneberger et al., 2015) — originally for biomedical segmentation, now a universal template for pixel-wise tasks.

**Structure**:

```
Input → [Conv+Pool]×N → Bottleneck → [Upconv+Concat+Conv]×N → Output
         │                                │
         │───── skip connection ──────────│
```

- **Encoder (contracting path)**: standard CNN — convs + max pooling to shrink spatial dim and grow channels.
- **Decoder (expanding path)**: transposed convs or upsample + conv to grow spatial dim back.
- **Skip connections**: feature maps from encoder concatenated to decoder at the same spatial resolution → preserves high-frequency details.

**Why skips**: encoders lose spatial precision through pooling. Decoders need that precision back for pixel-accurate output. Skips re-inject low-level features at high resolution.

**Use cases beyond biomedical segmentation**:

- Satellite image segmentation.
- Image-to-image translation (pix2pix uses UNet generator).
- **Diffusion models** — the denoiser in Stable Diffusion is a UNet (scaled up massively, with attention layers inside).

```python
class UNetBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1), nn.ReLU(inplace=True),
        )
    def forward(self, x):
        return self.block(x)

class UNet(nn.Module):
    def __init__(self, in_ch=3, num_classes=10):
        super().__init__()
        self.e1 = UNetBlock(in_ch, 64)
        self.e2 = UNetBlock(64, 128)
        self.bot = UNetBlock(128, 256)
        self.up1 = nn.ConvTranspose2d(256, 128, 2, 2)
        self.d1 = UNetBlock(256, 128)
        self.up2 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.d2 = UNetBlock(128, 64)
        self.out = nn.Conv2d(64, num_classes, 1)
        self.pool = nn.MaxPool2d(2)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(self.pool(e1))
        b  = self.bot(self.pool(e2))
        d1 = self.d1(torch.cat([self.up1(b), e2], dim=1))
        d2 = self.d2(torch.cat([self.up2(d1), e1], dim=1))
        return self.out(d2)
```

<div class="scenario" markdown>
**Scenario:** Training a UNet on small medical dataset (200 images) for tumor segmentation.<br>
**Answer:** Priorities: (1) **heavy augmentation** — flips, rotations, elastic deformations (Ronneberger's paper is famous for this), (2) **patch-based training** if images are large, (3) **pretrained encoder** (ResNet or EfficientNet) with UNet-style decoder (called "UNet with a backbone"), (4) **Dice or focal loss** for class imbalance (tumor pixels are rare), (5) **cross-validation** — 200 images is tiny; use 5-fold.
</div>

---

## Q32. Object detection — R-CNN → Faster R-CNN → YOLO → DETR { #q32 }

<span class="q-badge">Applied</span>

Detection evolved through four phases, each solving the previous era's bottleneck:

**1. Two-stage detectors (proposal + classification)**

- **R-CNN (2014)**: Selective Search generates 2000 regions → CNN classifies each. Slow (47 sec/image).
- **Fast R-CNN (2015)**: share CNN computation across regions using RoI pooling.
- **Faster R-CNN (2015)**: replaces Selective Search with a learned Region Proposal Network. End-to-end trainable. Still dominant in some benchmarks for accuracy.
- **Mask R-CNN (2017)**: adds segmentation branch to Faster R-CNN.

**2. One-stage detectors (dense prediction)**

- **YOLO** (2016+): single CNN predicts boxes + classes directly on a grid. Much faster, initially less accurate.
- **SSD**: multi-scale feature maps, default anchor boxes.
- **RetinaNet**: introduced **focal loss** to handle extreme foreground-background imbalance — matched two-stage accuracy.
- **YOLOv5 / v8 / v10** (2020+): modern one-stage, very production-friendly.

**3. Anchor-free detectors**

- **FCOS, CenterNet**: predict center points + box regression directly, no anchor boxes to tune.

**4. Transformer-based detection**

- **DETR (2020)**: set prediction with transformer decoder. No anchors, no NMS. Slow to train but end-to-end beautiful.
- **Deformable DETR**: faster training, focuses attention on sparse key points.
- **DINO / Grounding DINO**: 2023-2026 SOTA; unifies detection + grounding with text queries.

| Year | SOTA | Speed | Bells & whistles |
|---|---|---|---|
| 2014 | R-CNN | 0.02 FPS | Selective Search |
| 2015 | Faster R-CNN | 5 FPS | Region Proposal Network |
| 2017 | RetinaNet | 10 FPS | Focal loss |
| 2020 | DETR | 10 FPS | Transformer set prediction |
| 2024 | YOLOv10 | 100+ FPS | Anchor-free, NMS-free |

**Key metric**: mAP (mean Average Precision) at IoU thresholds (COCO: mAP@[0.5:0.95]).

<div class="tip-box" markdown>
**Interviewer tip:** Know the **two-stage vs one-stage tradeoff**. Two-stage is generally more accurate (precision-limited benchmarks). One-stage is faster and simpler to deploy. For a real-time mobile app, use **YOLOv8 or v10**. For a medical imaging / precision-critical app, use **Faster R-CNN / Mask R-CNN**.
</div>

---

## Q33. Non-maximum suppression (NMS) — and why detection has to deduplicate { #q33 }

<span class="q-badge">Applied</span>

Detectors output many overlapping boxes for the same object. **NMS** greedily picks the best and suppresses its neighbors.

**Algorithm**:

```
1. Sort predicted boxes by confidence.
2. Take highest-confidence box, add to keep list.
3. Remove all remaining boxes with IoU > threshold against it.
4. Repeat until no boxes left.
```

**IoU (Intersection over Union)**:

$$\text{IoU}(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

Typical NMS thresholds: 0.5 for general detection, 0.3 for dense scenes.

**Problems with vanilla NMS**:

1. **Hard threshold** — two nearby real objects may be suppressed.
2. **Sequential** — not parallelizable, slow for many boxes.
3. **Independent of score** — a box with IoU 0.51 is completely killed, while 0.49 survives.

**Soft-NMS** (Bodla et al., 2017) — instead of zeroing the score of overlapping boxes, decay it:

$$s_i \leftarrow s_i \cdot f(\text{IoU}(M, b_i))$$

With $f$ = linear or Gaussian penalty. Better recall in crowded scenes (e.g., pedestrians).

**DIoU-NMS** — uses Distance-IoU (considers box center distance) instead of plain IoU — better for same-class overlapping objects.

**NMS-free architectures**: DETR uses **bipartite matching loss** so each object has one predicted box → no NMS needed. YOLOv10 also made strides toward NMS-free.

```python
import torchvision.ops as ops
# boxes: (N, 4) in (x1, y1, x2, y2) format
# scores: (N,)
keep = ops.nms(boxes, scores, iou_threshold=0.5)
keep_boxes = boxes[keep]
keep_scores = scores[keep]
```

<div class="scenario" markdown>
**Scenario:** Crowd counting — many tightly packed pedestrians. NMS is merging distinct people.<br>
**Answer:** Three options: (1) **lower IoU threshold** — say 0.3 — but risk missing real dupes. (2) **Soft-NMS** — decay overlapping scores instead of killing — standard fix for crowded scenes. (3) **Specialized crowd models** (density map regression instead of detection) — sidestep NMS entirely.
</div>

---

## Q34. Transfer learning and fine-tuning — when to do what { #q34 }

<span class="q-badge">Practical</span>

**Pretrained CNN → new task**. The original training (usually ImageNet) taught the network to extract general visual features — edges, textures, part-of-object detectors — that transfer to most new tasks.

**Strategies**, in increasing adaptation:

**1. Feature extraction** (freeze everything, train only classifier head):

- Use when: target task is small and similar to pretrain.
- Example: classify dog breeds with < 1000 images.

**2. Fine-tune later layers only** (freeze early, train last few blocks + head):

- Use when: target task is mid-size and somewhat similar.
- Rationale: early layers = generic features (edges); later layers = task-specific (ImageNet classes).

**3. Full fine-tuning** (unfreeze everything, low LR):

- Use when: target task is large or very different.
- Use **differential learning rates** — lower LR for pretrained layers (1e-5), higher for new head (1e-3).

**4. Train from scratch**: only when task is very different from pretrain (e.g., medical MRI scans) *and* you have massive data.

```python
# Feature extraction
model = torchvision.models.resnet50(weights='DEFAULT')
for p in model.parameters():
    p.requires_grad = False
# Replace classifier head
model.fc = nn.Linear(model.fc.in_features, num_classes)

# Fine-tune with differential LRs
params = [
    {'params': model.conv1.parameters(), 'lr': 1e-5},
    {'params': model.layer1.parameters(), 'lr': 1e-5},
    {'params': model.layer4.parameters(), 'lr': 1e-4},
    {'params': model.fc.parameters(),     'lr': 1e-3},
]
optimizer = torch.optim.AdamW(params)
```

**Tips**:

- **Always match preprocessing** of the pretrained model (same mean/std normalization, same input size).
- **Don't apply aggressive augmentation early** — can destroy pretrained feature structure.
- **Warm-up strategy** — train head only for a few epochs, then unfreeze gradually (Howard & Ruder, ULMFiT).

<div class="tip-box" markdown>
**Interviewer tip:** "Which pretrained model should I use?" In 2026, strong defaults:
- **General vision**: DINOv2, CLIP, or modern ViT-L trained on LAION.
- **Efficient mobile**: EfficientNetV2, MobileNetV4.
- **Medical/industrial niche**: often start with ImageNet and fine-tune, or use domain-specific pretrains if available.
</div>

---

## Q35. Data augmentation for vision — from flips to MixUp and CutMix { #q35 }

<span class="q-badge">Practical</span>

Augmentation is the single cheapest way to add "more data" — crucial for small datasets and standard in all modern training.

**Classical augmentations**:

| Technique | When |
|---|---|
| Random crop + resize | Default everywhere |
| Horizontal flip | Most natural scenes (cats are symmetric) |
| Color jitter (brightness, contrast, saturation) | Lighting-invariant tasks |
| Rotation | Objects without canonical orientation |
| Random erasing (cutout) | Forces attention to non-obscured parts |
| AutoAugment / RandAugment | Learned augmentation policies |

**Modern augmentations**:

**MixUp** (Zhang et al., 2018):

$$\tilde x = \lambda x_i + (1-\lambda) x_j, \quad \tilde y = \lambda y_i + (1-\lambda) y_j$$

Mixes two samples linearly. Regularizes by encouraging linear behavior between samples.

**CutMix** (Yun et al., 2019): cut a rectangle from image $x_j$ and paste on $x_i$; label = pixel-proportional mix. Less artifactual than MixUp (natural image patches).

**MixUp vs CutMix** — both improve generalization ~1–2% ImageNet. CutMix often preferred for localization-heavy tasks (detection).

```python
# MixUp
def mixup(x, y, alpha=0.2):
    lam = np.random.beta(alpha, alpha)
    idx = torch.randperm(x.size(0))
    x_mix = lam * x + (1 - lam) * x[idx]
    y_a, y_b = y, y[idx]
    return x_mix, y_a, y_b, lam

# Loss = lam * CE(pred, y_a) + (1 - lam) * CE(pred, y_b)
```

**When augmentation fails**:

- Augmentations that change the label. Rotating MNIST 180° turns a "6" into a "9".
- Aggressive color jitter for medical images (color has diagnostic value).
- Aligned datasets (satellite imagery) where rotations introduce unnatural patterns.

**Automated augmentation** (RandAugment, AutoAugment, TrivialAugment): meta-learned or randomly-sampled policies. TrivialAugment (Müller & Hutter, 2021) is the no-tuning hero — randomly pick one augmentation, apply with random strength. Nearly as good as AutoAugment with none of the search cost.

<div class="scenario" markdown>
**Scenario:** Medical pathology dataset, 500 images, severe overfitting.<br>
**Answer:** Aggressive augmentation is the biggest lever: flips (both axes — pathology has no canonical orientation), rotations, small affine distortions, color/stain variation, elastic deformation (mimics tissue deformation). Combine with **strong weight decay** (1e-3), **dropout**, and a **pretrained backbone**. MixUp can help here — regularizes and helps with label noise (pathology labels are often noisy).
</div>

---

## Q36. Vision Transformers (ViT) — attention replaces convolution { #q36 }

<span class="q-badge">Modern</span>

**ViT** (Dosovitskiy et al., 2020):

1. Split image into $P \times P$ patches (e.g., $16 \times 16$).
2. Linearly project each patch to embedding dim → sequence of tokens.
3. Add learnable position embeddings + class ([CLS]) token.
4. Feed through standard Transformer encoder.
5. [CLS] token → MLP head → class prediction.

```
Image (224x224) → patches (14x14 of 16x16) → linear proj → 196 tokens + CLS
      → Transformer(L layers, d=768, heads=12) → classifier on CLS
```

**Why it works (with enough data)**:

- No convolution inductive bias → fully flexible attention over all patch pairs.
- Global receptive field from layer 1 (CNN needs many layers).
- Scales better than CNN with data and compute — ViTs on 300M+ images beat ResNets at every scale.

**Data hunger**:

- On ImageNet-1k from scratch, ViT underperforms ResNet. Needs ~10M+ images or strong pretraining.
- JFT-300M (Google internal) gave ViT its initial advantage.
- In 2026, public LAION / DataComp pretrained ViTs are SOTA.

**Key variants**:

- **DeiT** (data-efficient ViT, 2021): knowledge distillation + better augmentation → ViT training on ImageNet-1k alone.
- **Swin Transformer**: hierarchical, windowed attention — CNN-like efficiency, transformer modeling.
- **MAE (Masked Autoencoder)**: self-supervised pretraining by masking 75% of patches and reconstructing.
- **DINO / DINOv2**: self-supervised ViT with self-distillation — current best open representation model for vision.

```python
# Using pretrained ViT via timm
import timm
model = timm.create_model('vit_base_patch16_224', pretrained=True,
                          num_classes=num_classes)
```

<div class="tip-box" markdown>
**Interviewer insight:** "When is CNN still preferable?" Answer: (1) small datasets (<100k images) — CNN bias wins. (2) Edge deployment — mobile-optimized CNNs (MobileNet, EfficientNet) still have the best accuracy/FLOPs ratio. (3) Tasks with very high-resolution inputs — ViT's $O(L^2)$ is painful for dense-pixel predictions.
</div>

---

## Q37. Swin Transformer — windowed attention for vision { #q37 }

<span class="q-badge">Modern</span>

ViT's $O(L^2)$ attention is expensive when $L$ = number of patches is large (high resolution or small patches). **Swin Transformer** (Liu et al., 2021) solves this with:

**1. Windowed attention**: restrict self-attention to non-overlapping local windows of size $M \times M$ (e.g., $7 \times 7$).

- Reduces $O(L^2)$ to $O(LM)$ — linear in $L$ for fixed window size.

**2. Shifted windows**: alternate layers have windows shifted by half → enables cross-window interaction.

**3. Hierarchical patches**: spatial resolution halves every few stages (like a CNN), producing multi-scale features. Great for detection/segmentation.

```
Stage 1: patches at 1/4 resolution, window 7×7
Stage 2: patches at 1/8 resolution
Stage 3: patches at 1/16 resolution
Stage 4: patches at 1/32 resolution
```

**Why Swin matters**:

- First ViT to match/exceed CNN on detection and segmentation (where high-res matters).
- Linear complexity → handles high-res images.
- Hierarchical features → plug into existing detection/segmentation heads.

**Comparison** (ImageNet-1k top-1):

| Model | Params | Top-1 |
|---|---|---|
| ResNet-50 | 25M | 76.1% |
| ViT-B/16 | 86M | 77.9% (ImageNet only) |
| DeiT-B | 86M | 81.8% |
| Swin-B | 88M | 83.5% |
| ConvNeXt-B | 89M | 83.8% |

**ConvNeXt** (2022) is a response — modernized ResNet (depthwise convs, LayerNorm, GELU, inverse bottleneck) that matches Swin without transformers. Shows the gap wasn't about attention — it was about modern training + design choices.

<div class="tip-box" markdown>
**Interviewer question:** "Is the future of vision transformer or CNN?" There's no clear consensus as of 2026. Transformers dominate large-scale multimodal models (CLIP, Gemini vision, GPT-4V). CNNs (ConvNeXt V2, efficient variants) remain strong for mobile and data-efficient regimes. Hybrid approaches (conv early layers + attention later) are common. The safe answer: "it depends on data scale and deployment constraints."
</div>

---

## Q38. Self-supervised learning for vision — SimCLR, MoCo, BYOL, DINO, MAE { #q38 }

<span class="q-badge">Modern • Important</span>

Labels are expensive. Self-supervised learning (SSL) pretrains on unlabeled images by solving pretext tasks, producing features that transfer as well as (or better than) supervised pretraining.

**Two broad families**:

**Contrastive methods** — pull positive pairs (two augmentations of same image) together, push negatives apart:

- **SimCLR (2020)**: InfoNCE loss over large batch; strong augmentations; nonlinear projection head. Needs batch sizes of 4096+ for many negatives.
- **MoCo (2019, v2/v3)**: momentum encoder + queue of negatives → decouples batch size from number of negatives.
- **BYOL (2020)**: no negatives! Just predict target encoder's output via online encoder. Works because target encoder lags online (EMA).
- **SimSiam (2021)**: simplifies BYOL with stop-gradient. Surprisingly effective.

**Masked modeling** — mask parts of input, reconstruct:

- **MAE (Masked Autoencoder, 2021)**: mask 75% of patches, reconstruct pixels with an asymmetric encoder-decoder. Encoder only sees visible patches (fast).
- **BEiT**: predict discrete visual tokens (similar to BERT).

**Distillation-based**:

- **DINO (2021) / DINOv2 (2023)**: self-distillation — student predicts teacher's output. Teacher is EMA of student. Produces exceptional zero-shot features with strong localization.

| Method | Key idea | Batch size | Hardware |
|---|---|---|---|
| SimCLR | In-batch negatives | 4096+ | 8+ GPUs |
| MoCo | Momentum + queue | 256 | 4 GPUs |
| BYOL | No negatives, EMA target | 1024 | 4 GPUs |
| MAE | Mask + reconstruct pixels | Any | Efficient (encoder skip masked) |
| DINOv2 | Self-distillation | 1024 | Complex, SOTA features |

**Modern practice (2026)**: start with **DINOv2** ViT-L or ViT-G for vision feature extraction — outperforms ImageNet-supervised backbones on most downstream tasks and works zero-shot for many.

```python
# Using DINOv2 via torch.hub
dinov2 = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14')
features = dinov2(images)  # (B, 768) features
```

<div class="scenario" markdown>
**Scenario:** Building a medical imaging classifier with 2000 labeled images + 100,000 unlabeled images.<br>
**Answer:** Pretrain with **MAE or SimCLR** on the 100k unlabeled images, then fine-tune on 2k labeled. This typically beats supervised pretraining by 3-5% accuracy because the pretraining domain matches target. DINOv2 features as a baseline, then see if domain-specific SSL improves.
</div>

---

## Q39. Adversarial examples and robustness { #q39 }

<span class="q-badge">Conceptual</span>

**Adversarial example**: input with tiny, often imperceptible perturbation that causes the model to misclassify confidently.

Classical example (Szegedy et al., 2013 / Goodfellow et al., 2014): image of a panda + carefully crafted noise → classified as gibbon with 99% confidence.

**How they're made** — **FGSM (Fast Gradient Sign Method)**:

$$x_{\text{adv}} = x + \epsilon \cdot \text{sign}(\nabla_x L(f(x), y))$$

Take one gradient step in the direction that most increases the loss. $\epsilon$ is the perturbation budget (often $L_\infty$ constrained).

**PGD (Projected Gradient Descent)**: iterate FGSM, project back to $\epsilon$-ball each step. Stronger attacker.

**Why this happens (intuitively)**:

- Neural nets are locally linear → many directions in input space have high gradient magnitude → small perturbation in those directions moves the prediction a lot.
- Decision boundaries are close to data in high-dim.
- Training data doesn't sample adversarial directions → model never sees them.

**Defenses**:

| Defense | Mechanism | Tradeoff |
|---|---|---|
| **Adversarial training** | Include adversarial examples in training | -5% clean acc, +robust acc |
| **Randomized smoothing** | Input noise + majority vote | Provable but weak bounds |
| **Input preprocessing** | JPEG compression, resizing | Easily bypassed |
| **Feature denoising** | Explicit denoising layers | Moderate gains |

**Practical robustness** (CIFAR-10, ImageNet benchmark):

- Clean accuracy: 95%+ (standard models).
- PGD-robust accuracy: 60–70% after adversarial training (state of the art).
- Large gap — neural nets are fundamentally vulnerable.

**Why it matters for production**:

- **Security-sensitive applications** (content moderation, face recognition, malware detection) face real adversarial threats.
- **Physical-world attacks** — stop sign with sticker attacks self-driving cars.
- **Robustness correlates with interpretability** — robust models often have more sensible gradients.

<div class="tip-box" markdown>
**Interviewer tip:** Adversarial robustness is a deep research area. Most production systems don't do adversarial training (too expensive, hurts clean accuracy). They rely on **defense in depth**: input validation, rate limiting, monitoring prediction confidence, ensemble disagreement, human review for high-stakes decisions.
</div>

---

## Q40. Interpretability for CNNs — Grad-CAM, saliency, concept attribution { #q40 }

<span class="q-badge">Applied</span>

For non-trivial CNNs, "why did it predict this?" is a real question from PMs, clinicians, auditors. Standard interpretability tools:

**1. Saliency maps** (vanilla, 2013) — gradient of output w.r.t. input:

$$S_i = \frac{\partial f_c(\mathbf{x})}{\partial x_i}$$

Shows which pixels most affect class $c$'s score. Noisy and sensitive to specific pixels.

**2. Grad-CAM** (Selvaraju et al., 2017) — the interview standard:

- Compute gradient of target class score w.r.t. **last conv layer's feature maps**.
- Global-average-pool gradients per channel → importance weights $\alpha_k$.
- Weighted sum of feature maps → coarse heatmap at feature-map resolution.
- Upsample to input size, overlay on image.

$$L^c_{\text{Grad-CAM}} = \text{ReLU}\left(\sum_k \alpha_k A^k\right)$$

Much cleaner than saliency. Works for any CNN. Interpretable, class-specific.

**3. Integrated Gradients** (Sundararajan et al., 2017) — theoretically grounded attribution:

$$\text{IG}_i(x) = (x_i - x'_i) \int_0^1 \frac{\partial f(x' + \alpha(x - x'))}{\partial x_i} d\alpha$$

Satisfies axioms (sensitivity, implementation invariance) that saliency violates.

**4. SHAP for images** (Lundberg & Lee, 2017) — pixel-level Shapley values. Slow but principled.

**5. Concept activation vectors (TCAV)** — test whether "concepts" (stripes, redness) affect predictions. Requires labeled concept examples.

```python
import torch
import torch.nn.functional as F
from torchvision.models import resnet50

model = resnet50(weights='DEFAULT').eval()

# Grad-CAM
def grad_cam(model, image, class_idx, target_layer):
    features = []
    gradients = []
    def fwd_hook(module, input, output): features.append(output)
    def bwd_hook(module, grad_input, grad_output): gradients.append(grad_output[0])
    
    h1 = target_layer.register_forward_hook(fwd_hook)
    h2 = target_layer.register_full_backward_hook(bwd_hook)
    
    logits = model(image)
    model.zero_grad()
    logits[0, class_idx].backward()
    
    # alpha = global avg pool of gradients
    alpha = gradients[0].mean(dim=[2, 3], keepdim=True)
    cam = F.relu((alpha * features[0]).sum(dim=1))
    
    h1.remove(); h2.remove()
    return cam
```

**Use cases**:

- **Debugging** — why is my model confusing cats and dogs?
- **Bias auditing** — is it using the background instead of the object? (Classic case: camels on sand, cows on grass.)
- **Clinical decision support** — highlight the region that drove a tumor diagnosis.

<div class="tip-box" markdown>
**Honest caveat:** Interpretability tools produce **plausible-looking** visualizations but have known failure modes. Adebayo et al. (2018) showed saliency can produce similar maps even for randomly-initialized networks. Always validate interpretations with controlled experiments, not just visual inspection.
</div>

---

## ✅ Module Recap

- **Convolutions** encode translation equivariance, local connectivity, parameter sharing — the inductive bias that lets CNNs learn with less data than MLPs.
- Modern CNNs are stacks of **bottleneck blocks** (ResNet), **depthwise separable** convs (MobileNet), or **hierarchical windowed attention** (Swin).
- **ResNet's residual connection** is the single most important architectural innovation — enabled deep training and is now universal (transformers, UNets, LSTMs all use it).
- **ViT and its descendants** dominate at large scale and with good pretraining; CNNs remain strong at small scale and mobile.
- **Transfer learning** is the default in practice — always start from pretrained weights unless your task is truly novel.
- **Augmentation** is the cheapest way to add data. MixUp / CutMix / RandAugment / TrivialAugment are modern essentials.

→ Next: [🔁 RNNs & Sequences](rnns.md)
