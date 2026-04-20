# Module 5 — Clustering & Unsupervised

**Questions 66–85.** K-means, DBSCAN, HDBSCAN, PCA, t-SNE, UMAP, LDA. Unsupervised learning is where you earn "senior" credentials — the absence of labels forces you to think about what you're actually measuring and how to validate results.

---

## Q66. Derive K-means. Why does it converge? What can go wrong? { #q66 }

**Algorithm:**

1. Initialize `k` centroids `μ_1, ..., μ_k`.
2. **Assignment step:** assign each point to nearest centroid.

\[
c_i = \arg\min_j \|x_i - \mu_j\|^2
\]

3. **Update step:** recompute centroids as mean of assigned points.

\[
\mu_j = \frac{1}{|C_j|} \sum_{i \in C_j} x_i
\]

4. Repeat until assignments stop changing.

**Objective.** K-means minimizes within-cluster sum of squares (WCSS):

\[
L = \sum_{j=1}^k \sum_{i \in C_j} \|x_i - \mu_j\|^2
\]

**Why it converges.** Each step monotonically decreases `L`:

- Assignment step: each point moves to its nearest centroid → `L` cannot increase.
- Update step: the mean minimizes WCSS of a fixed cluster → `L` cannot increase.

Since `L ≥ 0` and the number of possible assignments is finite, the algorithm terminates.

**What can go wrong:**

1. **Local minima.** K-means converges to local optima. Run multiple times (`n_init=10`) and keep best.
2. **Sensitive to initialization.** K-means++ (smart init) mitigates this.
3. **Assumes spherical clusters.** Fails on elongated, nested, or varying-density data.
4. **Equal-size bias.** Tends to produce clusters of equal size.
5. **Requires pre-specified `k`.** Uses elbow or silhouette heuristic.
6. **Sensitive to feature scale** — always `StandardScaler` first.
7. **Sensitive to outliers** — a single far-outlier pulls its centroid.

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

X_scaled = StandardScaler().fit_transform(X)

kmeans = KMeans(
    n_clusters=5,
    init='k-means++',
    n_init=10,              # run 10 times, keep best
    max_iter=300,
    random_state=42,
)
labels = kmeans.fit_predict(X_scaled)
print(f"Inertia (WCSS): {kmeans.inertia_:.2f}")
```

---

## Q67. Explain K-means++. Why does it help? { #q67 }

**Problem with random init.** Two centroids might be placed in the same dense region, leaving the other side of the data unclaimed → poor local optimum.

**K-means++ (Arthur & Vassilvitskii 2007):**

1. Pick first centroid uniformly at random from data.
2. For each remaining point, compute distance `D(x)` to the nearest existing centroid.
3. Pick next centroid with probability proportional to `D(x)²`.
4. Repeat until `k` centroids chosen.

**Intuition:** probabilistically spreads centroids across the data. Points far from existing centroids are more likely to be chosen next.

**Guarantee:** K-means++ initialization gives an `O(log k)`-competitive solution *on average* compared to the optimal WCSS.

**In practice:**

- `sklearn` uses K-means++ by default.
- Combined with `n_init=10`, this is enough to reliably avoid bad local optima for most real data.

**Further improvement: k-means||** — a scalable parallel variant for big data.

---

## Q68. How do you choose `k` in K-means? { #q68 }

Three approaches:

**1. Elbow method.**

Plot WCSS vs `k`. Look for the "elbow" — the point after which additional clusters add marginal improvement.

```python
import numpy as np
import matplotlib.pyplot as plt

wcss = []
K = range(1, 15)
for k in K:
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km.fit(X_scaled)
    wcss.append(km.inertia_)

plt.plot(K, wcss, 'bx-')
plt.xlabel('k')
plt.ylabel('WCSS')
```

Downside: the elbow is often ambiguous.

**2. Silhouette score.**

For each point `i`, compute:

- `a(i)` = mean distance to other points in same cluster.
- `b(i)` = mean distance to points in the nearest *other* cluster.
- `s(i) = (b - a) / max(a, b)` ∈ [-1, 1]. Higher is better.

```python
from sklearn.metrics import silhouette_score

for k in range(2, 15):
    km = KMeans(n_clusters=k, n_init=10).fit(X_scaled)
    score = silhouette_score(X_scaled, km.labels_)
    print(f"k={k}: silhouette = {score:.3f}")
```

**3. Gap statistic.**

Compare the observed WCSS to the expected WCSS under a null distribution (uniform data). The optimal `k` is where the gap is largest.

```python
# No sklearn implementation; use gap_statistic library
from gap_statistic import OptimalK
optimalK = OptimalK(parallel_backend='joblib')
n_clusters = optimalK(X_scaled, cluster_array=np.arange(2, 15))
```

**4. Business logic.**

Sometimes `k` is determined by the problem. "We want to segment customers into 4 tiers (bronze/silver/gold/platinum)" → `k = 4`, done.

<div class="tip-box" markdown>
**Realistic interviewer answer:** "I'd start with silhouette score to get a technical signal, then cross-check with business needs. Pure data-driven `k` can give mathematically optimal but operationally useless cluster counts (e.g., 37 customer segments — unmaintainable)."
</div>

---

## Q69. Explain DBSCAN. What are the hyperparameters? { #q69 }

**Density-Based Spatial Clustering of Applications with Noise (Ester 1996).**

**Hyperparameters:**

- `eps` (ε): radius around a point.
- `min_samples`: minimum neighbors for a point to be a core point.

**Definitions:**

- **Core point:** has ≥ `min_samples` within `eps`.
- **Border point:** within `eps` of a core point but has < `min_samples` neighbors itself.
- **Noise point:** neither core nor border.

**Algorithm:**

1. For each core point, form a cluster with it and all directly density-reachable neighbors.
2. Merge clusters that share core points.
3. Assign border points to nearby core's cluster.
4. Everything else is noise.

**Key advantages:**

- Automatically determines number of clusters.
- Handles arbitrary cluster shapes (non-convex, elongated).
- Robust to outliers — labels them as noise.

**Key disadvantages:**

- Very sensitive to `eps`. Needs tuning.
- Struggles with varying-density clusters (a single ε can't fit both dense and sparse clusters).
- Doesn't scale to high dimensions (curse of dimensionality hits distance metric).

```python
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

# Heuristic for eps: plot k-distance and find the "knee"
k = 5
nbrs = NearestNeighbors(n_neighbors=k).fit(X_scaled)
distances, _ = nbrs.kneighbors(X_scaled)
distances = np.sort(distances[:, -1])

import matplotlib.pyplot as plt
plt.plot(distances)
plt.ylabel(f'{k}-distance')
# Pick eps at the "knee"

db = DBSCAN(eps=0.5, min_samples=5).fit(X_scaled)
labels = db.labels_
# Label -1 = noise
print(f"Clusters: {len(set(labels)) - (1 if -1 in labels else 0)}")
print(f"Noise points: {(labels == -1).sum()}")
```

<div class="scenario" markdown>
**Typical use cases for DBSCAN:**

- Spatial data (GPS points, sensor networks).
- Anomaly detection — noise points are anomalies.
- Image segmentation at the pixel level.
- Document clustering where the number of topics is unknown.
</div>

---

## Q70. HDBSCAN vs DBSCAN — why is HDBSCAN usually better? { #q70 }

**HDBSCAN (Campello 2013)** extends DBSCAN with hierarchical reasoning.

**Key innovation:** instead of a single `eps`, HDBSCAN considers all possible `eps` values and builds a cluster hierarchy. Then it extracts the "most stable" flat clustering from the hierarchy.

**Advantages over DBSCAN:**

1. **No `eps` parameter.** Only `min_cluster_size` — much more intuitive.
2. **Handles varying-density clusters.** Naturally — the hierarchy captures clusters at their own density scales.
3. **Soft membership scores.** Can output `outlier_score` and probability of cluster membership.

**Algorithm sketch:**

1. Compute **mutual reachability distance** — `max(core_k(a), core_k(b), d(a, b))`.
2. Build minimum spanning tree on these distances.
3. Build condensed cluster tree from MST.
4. Extract clusters that are stable (persist across a range of density thresholds).

```python
import hdbscan

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=15,
    min_samples=5,             # defaults to min_cluster_size if None
    cluster_selection_method='eom',  # 'eom' = excess of mass (default)
    metric='euclidean',
)
labels = clusterer.fit_predict(X_scaled)
# Soft cluster membership
probabilities = clusterer.probabilities_
outlier_scores = clusterer.outlier_scores_
```

**When HDBSCAN struggles:**

- High-dimensional data (curse of dim affects the distance metric). Reduce dim first with UMAP.
- Very large datasets (>1M rows). Can be slow; use `core_dist_n_jobs` for parallelism.

---

## Q71. What's hierarchical clustering? Single vs complete vs average linkage? { #q71 }

**Hierarchical clustering** builds a **dendrogram** — a tree of cluster merges or splits.

**Two types:**

- **Agglomerative (bottom-up):** start with each point as own cluster; merge closest pairs until one cluster.
- **Divisive (top-down):** start with one cluster; recursively split.

Agglomerative is more common.

**Linkage criteria — how to measure distance between clusters:**

| Linkage | Formula | Behavior |
|---|---|---|
| **Single** | `min d(a, b)` for `a ∈ A, b ∈ B` | Chaining — forms long, snake-like clusters |
| **Complete** | `max d(a, b)` | Tight, roughly equal-sized clusters |
| **Average (UPGMA)** | Mean pairwise distance | Balanced; common default |
| **Ward** | Minimize WCSS increase when merging | Similar to K-means clusters; most popular |

**Visual:** single linkage can produce "chaining" — two clusters connected by a single bridge are merged too aggressively. Ward is more robust.

```python
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt

# Build and visualize dendrogram
Z = linkage(X_scaled, method='ward')
fig, ax = plt.subplots(figsize=(12, 5))
dendrogram(Z, truncate_mode='level', p=5)

# Fit at specific n_clusters
hc = AgglomerativeClustering(
    n_clusters=5,
    linkage='ward',
)
labels = hc.fit_predict(X_scaled)
```

**When to use hierarchical over K-means:**

- You want to inspect the hierarchy (taxonomy discovery).
- You don't know `k` upfront and want to cut the tree at different depths.
- Clusters are nested (subgroups within subgroups).

**When not to:**

- Large data. Complexity is O(n³) naive, O(n² log n) optimized. Infeasible beyond ~20K rows.

---

## Q72. What's spectral clustering? When would you use it? { #q72 }

**Idea.** Use eigenvectors of a similarity graph to cluster.

**Algorithm:**

1. Build similarity matrix `W` — e.g., `W_ij = exp(-‖x_i - x_j‖² / 2σ²)`.
2. Compute graph Laplacian: `L = D - W` (or normalized version), where `D` is the degree matrix.
3. Compute the `k` smallest eigenvectors of `L`.
4. Stack eigenvectors into matrix `U ∈ R^(n × k)`.
5. Cluster rows of `U` with K-means.

**Intuition.** The eigenvectors of `L` encode the graph's community structure. In this transformed space, clusters that are "well-connected internally but poorly connected externally" become linearly separable.

**Strengths:**

- Handles non-convex, arbitrary-shaped clusters.
- Works well on graphs or relational data.
- Theoretical guarantees (Cheeger inequality, graph cut theory).

**Weaknesses:**

- Computing eigenvectors is O(n³) naively — doesn't scale.
- Sensitive to `σ` in the similarity function.
- Doesn't work well for hierarchical / nested clusters.

```python
from sklearn.cluster import SpectralClustering

sc = SpectralClustering(
    n_clusters=3,
    affinity='rbf',
    gamma=1.0,
    assign_labels='kmeans',
    random_state=42,
)
labels = sc.fit_predict(X_scaled)
```

**Use cases:**

- Image segmentation (pixels + spatial similarity).
- Network community detection.
- Manifold learning where clusters have complex shapes.

---

## Q73. Explain Gaussian Mixture Models (GMM) for clustering. { #q73 }

Covered mathematically in Q62 (EM derivation). Focusing here on clustering use:

**Key differences from K-means:**

1. **Soft clustering** — each point has probability of belonging to each cluster.
2. **Ellipsoidal clusters** — handles elongated, rotated shapes.
3. **Allows cluster overlap** — useful when points genuinely belong to multiple clusters.

**Covariance types:**

- `'full'` — each component has its own full covariance matrix. Most flexible, most parameters.
- `'tied'` — all components share one covariance matrix.
- `'diag'` — each component has a diagonal covariance (axis-aligned ellipsoids).
- `'spherical'` — each component has a single scalar variance. Essentially K-means.

**Choosing k with BIC:**

```python
from sklearn.mixture import GaussianMixture
import numpy as np

bics = []
for k in range(1, 10):
    gmm = GaussianMixture(n_components=k, covariance_type='full',
                          n_init=5, random_state=42)
    gmm.fit(X_scaled)
    bics.append(gmm.bic(X_scaled))

best_k = np.argmin(bics) + 1
```

**BIC** (Bayesian Information Criterion) balances fit and complexity:

\[
BIC = -2 \log L + p \log n
\]

Lower BIC is better. Penalizes models with more parameters.

<div class="tip-box" markdown>
**Senior signal:** "When I suspect clusters are Gaussian-ish but want the uncertainty-aware soft assignments, I use GMM. For robustness against non-Gaussian clusters, DBSCAN or HDBSCAN. For pure speed on spherical data, K-means."
</div>

---

## Q74. Derive PCA. What does it optimize? { #q74 }

**Goal.** Find orthogonal directions of maximum variance in the data.

**Setup.** Assume data `X ∈ R^(n × d)` is centered (mean subtracted).

**First principal component:**

\[
w_1 = \arg\max_{\|w\|=1} w^T \Sigma w
\]

where `Σ = (1/n) X^T X` is the sample covariance.

**Solution via Lagrange multipliers.** Write:

\[
L(w, \lambda) = w^T \Sigma w - \lambda (w^T w - 1)
\]

Setting `∂L/∂w = 0` gives:

\[
\Sigma w = \lambda w
\]

So `w_1` is the eigenvector with largest eigenvalue `λ_1`. The variance along `w_1` equals `λ_1`.

**Subsequent components** are eigenvectors of next-largest eigenvalues, orthogonal to previous.

**Dual view — reconstruction error.** PCA also minimizes squared reconstruction error:

\[
\min_W \sum_i \|x_i - W W^T x_i\|^2, \quad \text{s.t. } W^T W = I
\]

These two views give the *same* solution.

**Implementation via SVD.** Let `X = UΣV^T`. Principal components are columns of `V`; singular values `σ_i` relate to variance `σ_i² / n`.

```python
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

X_scaled = StandardScaler().fit_transform(X)

pca = PCA(n_components=10)
X_reduced = pca.fit_transform(X_scaled)

# How much variance does each component explain?
print(pca.explained_variance_ratio_)
print(f"Cumulative: {pca.explained_variance_ratio_.cumsum()}")
```

<div class="tip-box" markdown>
**Interviewer probe:** "Why standardize before PCA?" — PCA maximizes *variance*. Without standardization, features with larger scales dominate; PCA returns "the feature with the biggest numbers" — not informative.
</div>

---

## Q75. How do you choose the number of PCA components? { #q75 }

**Methods:**

**1. Explained variance threshold.**

Keep components until you've captured X% of variance (commonly 90% or 95%):

```python
import numpy as np

pca = PCA()
pca.fit(X_scaled)
cumvar = pca.explained_variance_ratio_.cumsum()
n_components = np.argmax(cumvar >= 0.95) + 1
```

**2. Scree plot (elbow).**

Plot eigenvalues vs component index. Look for the "elbow" where they flatten out.

```python
import matplotlib.pyplot as plt

plt.plot(pca.explained_variance_, 'o-')
plt.xlabel('Component')
plt.ylabel('Eigenvalue')
plt.yscale('log')
```

**3. Kaiser criterion.**

Keep components with eigenvalue > 1 (for standardized data). Heuristic; not always reliable.

**4. Cross-validation on downstream task.**

If PCA is a preprocessing step, select `n_components` via CV on the supervised task.

```python
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

for n in [5, 10, 20, 50, 100]:
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('pca', PCA(n_components=n)),
        ('clf', LogisticRegression()),
    ])
    score = cross_val_score(pipe, X, y, cv=5).mean()
    print(f"n={n}: {score:.3f}")
```

---

## Q76. What's the difference between PCA and t-SNE? { #q76 }

| Property | PCA | t-SNE |
|---|---|---|
| Linearity | Linear projection | Non-linear manifold |
| Preserves | Global variance | Local neighborhoods |
| Deterministic | Yes | No (random init) |
| New data | `transform()` works | Requires retraining |
| Component count | Any | Usually 2 or 3 (viz) |
| Interpretability | Loadings available | None |
| Speed | Fast | Slow (O(n²)) |

**t-SNE (van der Maaten & Hinton 2008)**:

1. Compute pairwise similarities in high dim using Gaussian kernels.
2. Compute pairwise similarities in low dim using heavy-tailed Student's t-distribution.
3. Minimize KL divergence between the two.

**Key hyperparameters:**

- `perplexity` — effective number of neighbors considered (typical: 30-50).
- `learning_rate` — crucial; default 200 often wrong. Use `n_samples / 12` as rule of thumb.
- `n_iter` — 1000 minimum.

```python
from sklearn.manifold import TSNE

tsne = TSNE(
    n_components=2,
    perplexity=30,
    learning_rate=X.shape[0] / 12,  # auto-like
    init='pca',                     # initialize with PCA for stability
    n_iter=1000,
    random_state=42,
)
X_tsne = tsne.fit_transform(X_scaled)
```

**t-SNE pitfalls:**

1. **Cluster size doesn't mean density.** Bigger clusters in t-SNE don't have more variance.
2. **Distances between clusters are meaningless.** Only within-cluster structure is reliable.
3. **Changing perplexity drastically changes results.** Run multiple settings.
4. **Don't use for downstream tasks.** t-SNE is for visualization, not feature engineering.

---

## Q77. UMAP vs t-SNE — when to use which? { #q77 }

**UMAP (McInnes 2018)** — Uniform Manifold Approximation and Projection.

Based on a different mathematical foundation (Riemannian geometry, fuzzy topological structure), but conceptually similar to t-SNE.

| Property | t-SNE | UMAP |
|---|---|---|
| Speed | Slow (O(n²)) | Faster (O(n log n)) |
| Preserves global structure | Poor | Better |
| Can embed new points | No | Yes |
| Scales to big data | ≤ 100K | Millions |
| Can use for feature engineering | No | Yes |
| Parameter sensitivity | High | Moderate |

**UMAP hyperparameters:**

- `n_neighbors` — local vs global tradeoff (low = local, high = global). Default 15.
- `min_dist` — how tightly points cluster in output. Default 0.1.

```python
import umap

reducer = umap.UMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    metric='euclidean',
    random_state=42,
)
X_umap = reducer.fit_transform(X_scaled)

# Embed new data
X_new_umap = reducer.transform(X_new)
```

**Choose UMAP when:**

- You need speed on large data (>50K).
- You want to embed new points later.
- Global structure matters (cluster-to-cluster distances).

**Choose t-SNE when:**

- Smaller data (< 20K).
- You're comparing to published t-SNE visualizations.
- You have time to tune perplexity.

<div class="scenario" markdown>
**Modern default:** UMAP has largely replaced t-SNE for new work. It's the default in `scanpy` (genomics), `bertopic` (topic modeling), and most modern embedding viz pipelines.
</div>

---

## Q78. What's LDA (Linear Discriminant Analysis)? How does it differ from PCA? { #q78 }

**LDA goal:** find directions that maximize *class separation*.

**PCA goal:** find directions of maximum *variance* (unsupervised).

**Fisher's LDA objective** for 2 classes:

\[
J(w) = \frac{w^T S_B w}{w^T S_W w}
\]

where:

- `S_B` = between-class scatter: `(μ_1 - μ_2)(μ_1 - μ_2)^T`.
- `S_W` = within-class scatter: sum of per-class covariances.

Maximized by solving generalized eigenvalue problem:

\[
S_W^{-1} S_B w = \lambda w
\]

**For K classes**, LDA finds at most `K - 1` discriminant directions.

**Example:** 3-class problem in 100D → LDA reduces to 2D (maximally separating the 3 classes).

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

lda = LinearDiscriminantAnalysis(n_components=2)
X_lda = lda.fit_transform(X_train, y_train)

# LDA can also be used as a classifier
y_pred = lda.predict(X_test)
```

**LDA vs PCA for classification:**

- PCA: keeps directions of high variance, which may not discriminate classes.
- LDA: keeps directions that discriminate classes, supervised.

**LDA's assumptions:**

1. Features are normally distributed per class.
2. All classes share the same covariance matrix (→ relaxed by **QDA**).
3. Classes have enough samples to estimate covariance.

**QDA (Quadratic Discriminant Analysis)** — relaxes the shared-covariance assumption. Each class gets its own Σ. More flexible, more parameters.

---

## Q79. Kernel PCA — what's the point? { #q79 }

**Idea.** Apply PCA in a high-dimensional feature space implicitly via the kernel trick.

**Why:** regular PCA finds *linear* subspaces. Kernel PCA finds *non-linear* manifolds.

**Algorithm:**

1. Compute kernel matrix `K_ij = k(x_i, x_j)`.
2. Center the kernel matrix.
3. Compute top `d` eigenvectors of `K`.
4. Project test point via kernel evaluations:

\[
\phi(x_t) \cdot v = \sum_i \alpha_i K(x_i, x_t)
\]

**Common kernels:**

- **RBF** (Gaussian) — most flexible.
- **Polynomial** — captures feature interactions.
- **Cosine** — for text-like data.

```python
from sklearn.decomposition import KernelPCA

kpca = KernelPCA(
    n_components=10,
    kernel='rbf',
    gamma=0.1,              # RBF width
    fit_inverse_transform=True,  # enables inverse_transform
)
X_kpca = kpca.fit_transform(X_scaled)
```

**Limitations:**

- Computes full `n × n` kernel matrix — O(n²) memory, O(n³) time.
- Not interpretable (no feature loadings).
- Parameter tuning (γ, kernel) is non-trivial.

**Alternatives for non-linear dim reduction:**

- Autoencoders (deep learning).
- UMAP / t-SNE for visualization.
- Nystroem + PCA for scalable approximation.

---

## Q80. How do autoencoders do dimensionality reduction? { #q80 }

**Structure:**

```
Input x → Encoder f → Latent z (bottleneck) → Decoder g → Reconstruction x̂
```

**Objective:**

\[
\min_{f, g} \sum_i \|x_i - g(f(x_i))\|^2
\]

`z = f(x)` is the low-dimensional representation.

**Variants:**

- **Undercomplete autoencoder.** Bottleneck smaller than input. Classic compression.
- **Sparse autoencoder.** Penalize non-zero activations in `z`.
- **Denoising autoencoder.** Corrupt input, reconstruct clean → learns robust features.
- **Variational autoencoder (VAE).** Probabilistic — `z` is a distribution; enables generation.
- **Contractive autoencoder.** Penalize Jacobian magnitude → invariant to small input perturbations.

```python
import torch
import torch.nn as nn

class AE(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z), z

model = AE(input_dim=784, latent_dim=32)
```

**Autoencoder vs PCA:**

- With **linear activations + MSE loss**, autoencoder recovers PCA exactly.
- Non-linear autoencoder can capture curved manifolds.
- PCA is closed-form; autoencoder requires training.
- PCA transform is deterministic; autoencoder can overfit.

<div class="tip-box" markdown>
**Senior perspective:** "Autoencoders are overkill for most tabular dim reduction. They shine on high-dim unstructured data — images, time series, audio — where linear methods fundamentally can't capture the manifold."
</div>

---

## Q81. What's t-SNE's crowding problem, and how does t-SNE solve it? { #q81 }

**Crowding problem.** When mapping from high-dim to 2D, there's simply not enough space in 2D to preserve all pairwise distances. Distant points in high-dim end up crowded together in low-dim.

**SNE's original failure.** Used Gaussian in both high-dim and low-dim. Both have light tails → far apart points get squished together equally in low-dim.

**t-SNE's fix.** Use Gaussian in high-dim, but **Student's t-distribution (df=1)** in low-dim.

The t-distribution has **heavy tails** — so points that are "moderately far" in high-dim can be placed *very* far in low-dim, freeing up space for close neighborhoods.

\[
q_{ij} = \frac{(1 + \|y_i - y_j\|^2)^{-1}}{\sum_{k \neq l} (1 + \|y_k - y_l\|^2)^{-1}}
\]

**Consequence of this fix:**

- Clusters in t-SNE are tighter and better separated than in SNE.
- Near neighborhoods (< perplexity rank) are preserved.
- Global distances are distorted — don't interpret them.

<div class="scenario" markdown>
**Interview red flag:** saying "cluster A is 3x further from cluster C than from cluster B in t-SNE" → wrong. Only within-cluster structure and which points cluster together is reliable.
</div>

---

## Q82. Evaluating clustering without labels — internal metrics. { #q82 }

When you have no ground truth, three main internal metrics:

**1. Silhouette coefficient** (covered in Q68):

\[
s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}
\]

Range: [-1, 1]. Higher is better. ~0.5+ is strong.

**2. Davies-Bouldin index:**

\[
DB = \frac{1}{k} \sum_i \max_{j \neq i} \frac{\sigma_i + \sigma_j}{d(\mu_i, \mu_j)}
\]

Where `σ_i` is cluster spread, `d(μ_i, μ_j)` is centroid distance. **Lower is better.**

**3. Calinski-Harabasz index** (variance ratio):

\[
CH = \frac{trace(B_k) / (k-1)}{trace(W_k) / (n-k)}
\]

Ratio of between-cluster to within-cluster variance. **Higher is better.**

```python
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

print(f"Silhouette: {silhouette_score(X_scaled, labels):.3f}")
print(f"Davies-Bouldin: {davies_bouldin_score(X_scaled, labels):.3f}")
print(f"Calinski-Harabasz: {calinski_harabasz_score(X_scaled, labels):.1f}")
```

**When you have some labels:**

- **Adjusted Rand Index (ARI)** — measures agreement with ground truth, adjusted for chance.
- **Normalized Mutual Information (NMI)** — mutual information between clusters and labels.
- **Fowlkes-Mallows** — geometric mean of pairwise precision and recall.

```python
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

ari = adjusted_rand_score(y_true, labels)
nmi = normalized_mutual_info_score(y_true, labels)
```

<div class="tip-box" markdown>
**Gotcha:** internal metrics all assume spherical, well-separated clusters. They systematically favor K-means-like structure. For DBSCAN-style non-convex clusters, internal metrics can mislead — always visually inspect with UMAP / t-SNE.
</div>

---

## Q83. What's topic modeling with LDA (Latent Dirichlet Allocation)? { #q83 }

**Note:** this LDA = Latent Dirichlet Allocation (topic model), not Linear Discriminant Analysis.

**Generative story:**

For each document `d`:

1. Draw topic distribution `θ_d ~ Dirichlet(α)`.
2. For each word `w` in the document:
   a. Draw topic `z ~ Categorical(θ_d)`.
   b. Draw word `w ~ Categorical(β_z)`, where `β_z` is the word distribution for topic `z`.

**Goal.** Infer `θ_d` (topic mixes per document) and `β_k` (word distributions per topic) given observed documents.

**Inference:** variational Bayes or collapsed Gibbs sampling.

```python
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(max_df=0.95, min_df=5, stop_words='english')
X_counts = cv.fit_transform(documents)

lda = LatentDirichletAllocation(
    n_components=10,           # number of topics
    learning_method='online',
    random_state=42,
)
doc_topics = lda.fit_transform(X_counts)

# Print top words per topic
feature_names = cv.get_feature_names_out()
for i, topic in enumerate(lda.components_):
    top_words = [feature_names[j] for j in topic.argsort()[-10:]]
    print(f"Topic {i}: {top_words}")
```

**Modern alternatives:**

- **BERTopic** — combines BERT embeddings + UMAP + HDBSCAN + topic term ranking. Often gives more coherent, interpretable topics than vanilla LDA.
- **Top2Vec** — similar philosophy.

**When vanilla LDA still wins:**

- Small data (BERTopic needs ~1000+ docs to do well).
- Very domain-specific vocabulary where BERT doesn't help.
- Explainability requirements (α and β are interpretable Dirichlet parameters).

---

## Q84. What's matrix factorization? Explain NMF vs SVD. { #q84 }

Matrix factorization decomposes a matrix `X ∈ R^(n × d)` into a product of lower-rank matrices:

\[
X \approx W H
\]

where `W ∈ R^(n × k)` and `H ∈ R^(k × d)` with `k << min(n, d)`.

**SVD (Singular Value Decomposition):**

\[
X = U \Sigma V^T
\]

- `U, V` orthogonal, `Σ` diagonal.
- Optimal rank-`k` approximation under Frobenius norm (Eckart-Young theorem).
- Can have negative values.

**NMF (Non-negative Matrix Factorization):**

Same decomposition, but requires `W ≥ 0, H ≥ 0`.

- Results are "parts-based" — decomposes data into additive components.
- More interpretable than SVD when data is non-negative (counts, pixel intensities).
- No closed-form solution; solved via multiplicative updates or ALS.

```python
from sklearn.decomposition import NMF, TruncatedSVD

# SVD (for sparse matrices)
svd = TruncatedSVD(n_components=50, random_state=42)
X_svd = svd.fit_transform(X)

# NMF — requires X >= 0
nmf = NMF(n_components=10, init='nndsvd', random_state=42)
W = nmf.fit_transform(X_nonneg)
H = nmf.components_
```

**Use cases:**

- **SVD** — LSA for text (synonym discovery), image compression, general-purpose low-rank approx.
- **NMF** — topic modeling with non-negative components, spectrogram decomposition, gene expression clustering.
- **Recommender systems** — both can factor a user-item matrix (covered in Module 7).

---

## Q85. What are autoencoders' failure modes for anomaly detection? { #q85 }

**Typical approach:** train autoencoder on normal data. Reconstruction error is anomaly score.

**Failure mode 1 — autoencoder generalizes too well.**

A sufficiently expressive autoencoder can reconstruct anomalies too (it learns identity-like mapping). Solution:

- Keep bottleneck small.
- Use **denoising** autoencoder — force the model to learn semantic compression, not memorization.
- Use **contractive** autoencoder — penalize sensitivity to input perturbations.

**Failure mode 2 — some anomalies have low reconstruction error by coincidence.**

Numeric anomalies in the "interpolation" region (not extreme in any single feature, but jointly unusual) can have low error.

*Fix:* combine reconstruction with latent-space anomaly scores. A VAE-based approach:

\[
\text{Anomaly score} = \text{reconstruction error} + \text{KL divergence from prior}
\]

**Failure mode 3 — training contamination.**

If "normal" training data contains outliers, the autoencoder learns to reconstruct them too. Solution:

- Robust autoencoder variants (RCVA, robust deep AE).
- Pre-filter training set with simpler anomaly detector (Isolation Forest → top 5% removed).

**Failure mode 4 — distribution shift in deployment.**

Autoencoder trained on last year's normal data sees this year's normal data and flags it as anomaly.

*Fix:* monitor reconstruction error distribution over time; retrain if it shifts.

```python
import torch.nn as nn

class DenoisingAE(nn.Module):
    def __init__(self, input_dim, latent_dim=16, noise=0.1):
        super().__init__()
        self.noise = noise
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(),
            nn.Linear(64, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64), nn.ReLU(),
            nn.Linear(64, input_dim),
        )

    def forward(self, x):
        if self.training:
            x_noisy = x + self.noise * torch.randn_like(x)
        else:
            x_noisy = x
        return self.decoder(self.encoder(x_noisy))

# Anomaly score = MSE between x and reconstruction
def anomaly_score(model, x):
    with torch.no_grad():
        return ((model(x) - x) ** 2).mean(dim=1)
```

<div class="scenario" markdown>
**Production reality:** for tabular anomaly detection, Isolation Forest is almost always the first choice — faster, no tuning, interpretable. Autoencoders are for high-dimensional unstructured data (images, sensor sequences) where linear methods cannot capture normality.
</div>
