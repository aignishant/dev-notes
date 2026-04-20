# Module 5 — Unsupervised Learning

Twenty-five questions across clustering, dimensionality reduction, and anomaly detection. These algorithms get asked whenever the interviewer wants to test whether you can work **without labels** — which is the reality of most production data science.

---

## Q71. Explain K-means step by step. { #q71 }

**Algorithm (Lloyd's algorithm):**

1. Initialize $K$ centroids (randomly or via K-means++).
2. **Assign step:** Each point goes to its nearest centroid (Euclidean distance).
3. **Update step:** Each centroid becomes the mean of points assigned to it.
4. Repeat 2–3 until assignments don't change (or max iterations).

**Objective function** it minimizes:

$$
J = \sum_{i=1}^{n} \sum_{k=1}^{K} \mathbb{1}[c_i = k] \|x_i - \mu_k\|^2
$$

This is the **within-cluster sum of squares** (WCSS).

**Convergence:** Each iteration decreases (or keeps equal) $J$. Since $J$ is bounded below by 0, the algorithm converges — but to a **local** minimum.

```python
from sklearn.cluster import KMeans

kmeans = KMeans(
    n_clusters=5,
    init='k-means++',
    n_init=10,       # multiple random starts
    max_iter=300,
    random_state=42
).fit(X)

labels = kmeans.labels_
centers = kmeans.cluster_centers_
inertia = kmeans.inertia_  # final WCSS
```

---

## Q72. Why does K-means need multiple random initializations? { #q72 }

**Problem:** K-means converges to a local minimum of WCSS. Bad initialization → bad local minimum.

**Example:** In a dataset with 3 natural clusters, if two initial centroids happen to fall near the same cluster, K-means can settle with that one cluster split into two, and the other two merged.

**Solution 1 — Multiple restarts (`n_init`):** Run K-means many times with different random inits, return the result with the lowest WCSS.

**Solution 2 — K-means++:** Smart initialization. Pick the first centroid randomly, then pick each subsequent centroid with probability proportional to its squared distance from the nearest already-chosen centroid. This spreads centroids out from the start.

K-means++ alone typically gets within 2× of optimal WCSS with high probability — combined with `n_init=10`, you're almost always at a good solution.

```python
# sklearn default is k-means++
KMeans(init='k-means++', n_init=10)

# Naive random
KMeans(init='random', n_init=10)
```

---

## Q73. How do you pick the number of clusters K? { #q73 }

No single "right" answer — multiple methods, use several together:

**1. Elbow method:**

Plot WCSS vs K. Look for the "elbow" where adding more clusters stops reducing WCSS significantly.

```python
inertias = [KMeans(n_clusters=k, n_init=10).fit(X).inertia_ for k in range(1, 16)]
import matplotlib.pyplot as plt
plt.plot(range(1, 16), inertias, 'o-')
```

Weakness: the elbow is subjective.

**2. Silhouette score:**

For each point, compute:
- $a$ = mean distance to points in its own cluster.
- $b$ = mean distance to points in the nearest other cluster.
- Silhouette = $(b - a) / \max(a, b)$.

Higher = better (max 1). Average across all points.

```python
from sklearn.metrics import silhouette_score
scores = [silhouette_score(X, KMeans(k, n_init=10).fit_predict(X)) for k in range(2, 16)]
```

**3. Gap statistic:**

Compare WCSS to what you'd see under a reference null distribution (uniform in the data's bounding box). The K with the largest gap is optimal.

**4. BIC / AIC (for GMM):** Penalized likelihood — not directly applicable to K-means, but works for its probabilistic cousin.

**5. Domain knowledge:** If stakeholders say "we operate in 5 geographies," try K = 5 first.

<div class="tip-box" markdown>
**Interviewer trap:** "Is there a statistical test for K?" — Not for K-means. All methods are heuristic. Honest answer: "I'd combine silhouette + elbow + domain knowledge, and ultimately pick the K that gives *actionable* clusters."
</div>

---

## Q74. What are K-means' limitations? { #q74 }

Seven limitations:

1. **Assumes spherical, equal-size clusters.** Struggles with elongated, unequal-density, or non-convex shapes.
2. **Sensitive to initialization.** Mitigated by K-means++ and multiple restarts.
3. **Must specify K upfront.**
4. **Not robust to outliers.** Outliers pull centroids away from their true locations.
5. **Only handles numerical features.** Requires one-hot for categoricals; distance becomes meaningless with one-hot.
6. **Curse of dimensionality.** Euclidean distance loses meaning in high-D; K-means becomes useless above ~50 features without dim reduction.
7. **Hard assignments.** A point either belongs or doesn't — no soft membership.

**Alternatives for each:**

- Non-spherical clusters → DBSCAN, spectral clustering.
- Unknown K → DBSCAN, HDBSCAN.
- Outliers → K-medoids (PAM), trimmed K-means.
- Categorical → K-modes, K-prototypes.
- High-dim → PCA/UMAP first, then cluster.
- Soft assignments → GMM.

---

## Q75. Explain DBSCAN. { #q75 }

**DBSCAN** (Density-Based Spatial Clustering of Applications with Noise):

Define two hyperparameters:
- **ε (eps):** neighborhood radius.
- **minPts:** minimum points to form a dense region.

Classify each point:

- **Core point:** has at least `minPts` within ε.
- **Border point:** within ε of a core point, but not a core itself.
- **Noise point:** neither.

A cluster is a connected component of core points (reachable through ε-neighborhoods), plus border points.

**Advantages over K-means:**

- No need to specify number of clusters.
- Finds arbitrarily-shaped clusters.
- Identifies noise/outliers naturally.

**Disadvantages:**

- Sensitive to ε choice — too small → everything's noise; too large → everything's one cluster.
- Struggles with clusters of very different densities.
- Curse of dimensionality (same as KNN).

**Picking ε:** Plot k-distance graph — sorted distances of each point to its $k$th nearest neighbor (typically $k = \text{minPts}$). The "knee" of the curve suggests ε.

```python
from sklearn.cluster import DBSCAN

dbscan = DBSCAN(eps=0.5, min_samples=5).fit(X)
labels = dbscan.labels_  # -1 indicates noise
```

---

## Q76. HDBSCAN vs DBSCAN — what's the improvement? { #q76 }

**HDBSCAN** (Hierarchical DBSCAN) eliminates DBSCAN's fixed-ε problem by building a hierarchy of clusters across all density thresholds and selecting the most "stable" clusters.

**Algorithm:**

1. Transform data by "mutual reachability distance" (smooths outlier effects).
2. Build minimum spanning tree based on this distance.
3. Convert to hierarchy by greedily adding edges in decreasing density.
4. Use stability scoring to pick the flat clustering.

**Advantages over DBSCAN:**

- **No ε hyperparameter.**
- **Handles varying densities** — each cluster can have its own density.
- **More robust** to parameter choice (only `min_cluster_size` matters much).

**In practice:** HDBSCAN is almost always the better choice when you'd reach for DBSCAN.

```python
import hdbscan

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=50,
    min_samples=10,
    cluster_selection_epsilon=0.0
)
labels = clusterer.fit_predict(X)

# Membership probability per point
probs = clusterer.probabilities_
# Outlier score (higher = more outlier)
outlier_scores = clusterer.outlier_scores_
```

---

## Q77. Hierarchical clustering: agglomerative vs divisive. { #q77 }

**Agglomerative (bottom-up):**

1. Start with each point as its own cluster.
2. Merge the two closest clusters.
3. Repeat until one cluster remains (or until a stopping criterion).

**Divisive (top-down):**

1. Start with all points in one cluster.
2. Split the least cohesive cluster.
3. Repeat.

Agglomerative is far more common (divisive is NP-hard for exact solution).

**Linkage criteria** (how to measure cluster-to-cluster distance):

| Linkage | Definition | Produces |
|---|---|---|
| Single | $\min_{x \in A, y \in B} d(x, y)$ | Chained, elongated clusters |
| Complete | $\max_{x \in A, y \in B} d(x, y)$ | Compact, equal-diameter clusters |
| Average (UPGMA) | mean pairwise dist | Balanced |
| Ward | Minimize WCSS increase | Compact, equal-size; works well in practice |

**Result:** A **dendrogram** — tree showing the merge order. Cut the dendrogram at a chosen level to get a flat clustering.

```python
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, dendrogram

# Flat clustering with K clusters
hc = AgglomerativeClustering(n_clusters=5, linkage='ward').fit(X)

# Or build full dendrogram
Z = linkage(X, method='ward')
dendrogram(Z, truncate_mode='level', p=5)
```

**Use cases:**

- When you want a **hierarchy** (not just a flat partition), e.g., taxonomies.
- Small datasets (< 10K) — $O(n^2)$ memory is prohibitive above.
- Exploratory analysis where K is unknown.

---

## Q78. What is spectral clustering? { #q78 }

**Spectral clustering** uses the spectrum (eigenvalues) of a similarity matrix to cluster data that are not linearly separable in the original feature space.

**Algorithm:**

1. Construct a similarity graph (e.g., k-NN graph, Gaussian similarity).
2. Compute the graph Laplacian $L = D - W$ (where $D$ is degree matrix, $W$ is similarity matrix).
3. Find the smallest $K$ eigenvectors of $L$.
4. Stack them into an $n \times K$ matrix; treat each row as a point.
5. Run K-means on these rows.

**Why it works:** Eigenvectors of the Laplacian encode the graph's cluster structure. Points in the same cluster map to similar vectors in the eigenspace, where K-means works well even if the original data has complex geometry.

**Strengths:**

- Can cluster non-convex shapes (two concentric circles, moons).
- Works when clusters are defined by connectivity, not proximity.

**Weaknesses:**

- $O(n^3)$ eigendecomposition — bad for large $n$.
- Choice of similarity function matters a lot.

```python
from sklearn.cluster import SpectralClustering

sc = SpectralClustering(
    n_clusters=3,
    affinity='nearest_neighbors',
    n_neighbors=10,
    random_state=42
).fit(X)
```

---

## Q79. Derive PCA from scratch. { #q79 }

**Goal:** Find orthogonal directions that capture maximum variance in the data.

**Setup:** Data matrix $X \in \mathbb{R}^{n \times p}$, centered (subtract mean).

**Step 1 — Covariance matrix:**

$$
\Sigma = \frac{1}{n-1} X^\top X
$$

**Step 2 — Eigendecomposition:**

$$
\Sigma v = \lambda v
$$

Eigenvectors are the principal components; eigenvalues are the variances along each component.

**Step 3 — Project:**

$$
Z = X V_k
$$

where $V_k$ is the matrix of top $k$ eigenvectors.

**Alternative via SVD (numerically preferred):**

$$
X = U \Sigma V^\top
$$

- $V$ columns are the principal components.
- $U \Sigma$ gives the projected coordinates.
- Eigenvalues of $\Sigma$ are $\sigma_i^2 / (n-1)$.

**Why SVD is preferred:** More numerically stable; works even when $X^\top X$ would be ill-conditioned.

```python
from sklearn.decomposition import PCA

# Retain 95% of variance
pca = PCA(n_components=0.95)
X_reduced = pca.fit_transform(X)

print(f"Components: {pca.n_components_}")
print(f"Variance explained: {pca.explained_variance_ratio_}")
print(f"Total variance retained: {pca.explained_variance_ratio_.sum():.3f}")
```

---

## Q80. Why scale data before PCA? { #q80 }

PCA identifies directions of maximum variance. If one feature has a much larger scale, it will dominate the covariance matrix regardless of its actual importance.

**Example:** Dataset with `height_cm` (range 150–200) and `age_years` (range 0–100). `height` will have 50× the variance of a typical spread. PCA will pick it as PC1 without any real insight.

**Fix:** Standardize each feature to mean 0, variance 1 before PCA:

```python
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('pca', PCA(n_components=5))
]).fit_transform(X)
```

**Exception:** If your features are on the **same natural scale** and their relative magnitudes are meaningful (e.g., gene expression levels, image pixel intensities), don't scale — you'd be destroying information.

---

## Q81. When is PCA a good idea, and when is it a bad idea? { #q81 }

**Good:**

- **Visualization:** Project to 2D or 3D for exploring data.
- **Noise reduction:** Discarding low-variance components often removes noise.
- **Speeding up downstream ML:** Reduces feature count → faster training for KNN, SVM, neural nets.
- **Multicollinearity:** PCA features are orthogonal by construction.
- **Image compression:** Natural image patches have most variance in few components.

**Bad:**

- **Classification where labels matter:** PCA ignores class structure. Discards low-variance but class-discriminative directions. Use LDA or supervised PCA instead.
- **Sparse data:** PCA destroys sparsity (dense projections). Use sparse PCA or truncated SVD.
- **Non-linear manifolds:** PCA is linear. For non-linear structure, use t-SNE/UMAP (visualization) or kernel PCA (general).
- **Interpretability needed:** PCA components are linear combinations of original features → hard to interpret. Feature selection might be better.

<div class="scenario" markdown>
**Scenario:** A candidate says "I ran PCA, kept the top 10 components, and fed them to my random forest. Accuracy dropped." Why?

**Possible reasons:** (1) PCA discarded low-variance but highly predictive features. (2) Tree models don't need decorrelation. (3) Scaling issues before PCA distorted directions. (4) Loss of feature interpretability in the tree. **Best answer:** PCA is usually counterproductive for tree-based models — they handle correlation and high-dim data natively. Save PCA for distance/linear models.
</div>

---

## Q82. Explain t-SNE vs UMAP. { #q82 }

Both are **non-linear dimensionality reduction for visualization**.

**t-SNE (2008):**

- Computes pairwise similarities in high-D (Gaussian kernel).
- Computes pairwise similarities in low-D (Student's t-distribution).
- Minimizes KL divergence between the two distributions.
- Key hyperparameter: **perplexity** (~5–50, controls effective neighborhood size).
- Tends to preserve **local** structure well, distorts global.

**UMAP (2018):**

- Builds a weighted graph in high-D using fuzzy simplicial sets.
- Optimizes a low-D graph to match, minimizing cross-entropy.
- Key hyperparameters: `n_neighbors`, `min_dist`.
- Preserves **both local and global** structure better than t-SNE.
- Much faster (5–10× on large datasets).

**When to pick each:**

| Criterion | t-SNE | UMAP |
|---|---|---|
| Large data (> 100K) | Slow | Fast |
| Global structure | Preserves local well, global badly | Better balance |
| Clustering on reduced dims | Don't | Sometimes OK |
| Reproducibility | Stochastic, different runs differ | Same (with seed) |
| Transform new data | No (need to refit) | Yes (`.transform()`) |

```python
# t-SNE
from sklearn.manifold import TSNE
X_tsne = TSNE(n_components=2, perplexity=30, random_state=42).fit_transform(X)

# UMAP
import umap
reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=42)
X_umap = reducer.fit_transform(X)
# Transform new data later
X_new_umap = reducer.transform(X_new)
```

!!! warning "Don't use t-SNE/UMAP for ML pipelines"
    These are **visualization tools**, not dim-reduction for downstream models. Distances and densities in the embedding are not faithful; clustering on t-SNE coordinates gives misleading results.

---

## Q83. What is Kernel PCA? { #q83 }

**Kernel PCA** applies the kernel trick to PCA, enabling **non-linear** dimensionality reduction.

Replaces the covariance matrix computation with the kernel matrix $K \in \mathbb{R}^{n \times n}$, where $K_{ij} = k(x_i, x_j)$.

Center the kernel matrix, then eigendecompose. The top eigenvectors, properly normalized, give the non-linear projections.

```python
from sklearn.decomposition import KernelPCA

# RBF kernel PCA
kpca = KernelPCA(n_components=2, kernel='rbf', gamma=0.1).fit_transform(X)

# Polynomial
kpca_poly = KernelPCA(n_components=2, kernel='poly', degree=3).fit_transform(X)
```

**Pros:** Captures non-linear structure; more faithful than PCA for curved manifolds.

**Cons:** Full $n \times n$ kernel matrix → $O(n^2)$ memory, $O(n^3)$ eigendecomposition. Prohibitive above $n = 10K$.

**When to use:** Small-data non-linear dim reduction. For large data, UMAP is usually a better choice.

---

## Q84. What is ICA (Independent Component Analysis)? { #q84 }

**ICA** finds a linear transformation where the components are **statistically independent** (not just uncorrelated like PCA).

**Classic use case — blind source separation (cocktail party problem):** Multiple microphones record overlapping voices. ICA separates the original voice signals.

**Key insight:** Gaussian variables that are uncorrelated *are* independent. For Gaussian data, ICA = PCA. ICA's power comes from **non-Gaussianity** — it maximizes a measure of non-Gaussianity (kurtosis, negentropy) to find independent sources.

**Algorithm (FastICA):**

1. Center and whiten data (make covariance identity).
2. Find directions that maximize non-Gaussianity via gradient-based optimization.

**PCA vs ICA:**

| Aspect | PCA | ICA |
|---|---|---|
| Goal | Max variance | Max independence (min Gaussianity) |
| Components | Orthogonal | Statistically independent |
| Unique ordering | By variance | No natural ordering |
| Works on Gaussian data | Yes | Degenerates |
| Use case | Dim reduction, noise removal | Source separation |

```python
from sklearn.decomposition import FastICA

ica = FastICA(n_components=3, random_state=42).fit_transform(X)
```

---

## Q85. What is NMF (Non-negative Matrix Factorization)? { #q85 }

**NMF** factorizes a non-negative matrix $V$ into two non-negative matrices:

$$
V \approx W H
$$

where $V \in \mathbb{R}_+^{n \times p}$, $W \in \mathbb{R}_+^{n \times k}$, $H \in \mathbb{R}_+^{k \times p}$.

**Interpretation:**

- Each row of $W$ is a sample's representation in a $k$-dimensional "parts" space.
- Each row of $H$ is a "part" — a vector in the original feature space.
- Each sample is a non-negative combination of parts.

**Why non-negative matters:** Forces **additive** (part-based) representations. Classic example: faces decompose into facial features (eyes, mouth, nose) — unlike PCA, which produces ghostly eigenfaces.

**Use cases:**

- **Topic modeling:** Rows = documents, columns = words, $W$ = topic weights per doc, $H$ = word weights per topic.
- **Recommender systems:** Rows = users, columns = items, $W$ = user latent factors, $H$ = item latent factors.
- **Hyperspectral image unmixing.**
- **Audio source separation.**

```python
from sklearn.decomposition import NMF

nmf = NMF(n_components=10, init='nndsvd', max_iter=500).fit(V)
W = nmf.transform(V)
H = nmf.components_
```

---

## Q86. What is an Autoencoder? How does it compare to PCA? { #q86 }

**Autoencoder:** A neural network trained to reconstruct its input.

```
input → encoder → bottleneck (low-dim) → decoder → output
                     ↑
            the learned representation
```

Loss: $L = \|x - \hat{x}\|^2$ (for continuous) or cross-entropy (for binary).

**Linear autoencoder = PCA.** With a linear encoder and linear decoder, and MSE loss, the bottleneck span is the same as the top principal components.

**Non-linear autoencoder:** With non-linear activations (ReLU, sigmoid), can learn non-linear manifolds — more expressive than PCA.

**Variants:**

- **Denoising Autoencoder:** Corrupts input, learns to reconstruct clean output. Forces robust features.
- **Sparse Autoencoder:** Adds L1 penalty on bottleneck activations. Encourages feature-selective neurons.
- **Variational Autoencoder (VAE):** Bottleneck is a learned distribution — enables generation.
- **Contractive Autoencoder:** Penalizes Jacobian of encoder — robust to small input perturbations.

**When to use AE over PCA:**

- Non-linear manifold structure.
- Very high-dim data (images, audio) where PCA is both expensive and inadequate.
- Want to chain dim reduction with other deep learning.

```python
import torch.nn as nn

class AE(nn.Module):
    def __init__(self, input_dim, bottleneck):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(),
            nn.Linear(128, bottleneck)
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck, 128), nn.ReLU(),
            nn.Linear(128, input_dim)
        )
    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)
```

---

## Q87. Explain anomaly detection approaches and when to use each. { #q87 }

**Unsupervised anomaly detection** — no labels available. Five main families:

| Family | Examples | Assumption |
|---|---|---|
| **Statistical** | Z-score, MAD, Grubbs test | Data is near-Gaussian |
| **Distance-based** | KNN outlier, LOF | Outliers are far from neighbors |
| **Density-based** | DBSCAN noise, LOF | Outliers are in low-density regions |
| **Clustering-based** | Distance to nearest cluster center | Outliers don't belong to any cluster |
| **Isolation-based** | Isolation Forest | Outliers are easy to isolate |
| **Reconstruction-based** | Autoencoders, PCA | Outliers have high reconstruction error |
| **Model-based** | One-class SVM, Elliptic Envelope | Outliers fall outside a fitted boundary |

**Decision guide:**

- **Low-dim (< 20), Gaussian-ish:** Elliptic Envelope (fits multivariate Gaussian).
- **Mid-dim tabular:** Isolation Forest — robust, fast, no assumption on distribution.
- **High-dim (images, time series):** Autoencoder reconstruction error.
- **Streaming / online:** Half-Space Trees, HBOS.
- **Local anomalies (outlier relative to local neighborhood):** Local Outlier Factor (LOF).

```python
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope

# Isolation Forest — general purpose
iso = IsolationForest(contamination=0.01).fit(X)

# LOF for local anomalies
lof = LocalOutlierFactor(n_neighbors=20, contamination=0.01)
labels = lof.fit_predict(X)

# Gaussian fit
ee = EllipticEnvelope(contamination=0.01).fit(X)
```

---

## Q88. What is Local Outlier Factor (LOF)? { #q88 }

**LOF** measures the local density deviation of a point relative to its neighbors.

**Computation:**

1. For each point $p$, find its $k$-nearest neighbors.
2. Compute **reachability distance**: $\text{reach-dist}_k(p, o) = \max(k\text{-dist}(o), d(p, o))$.
3. Compute **local reachability density** (LRD):
   $$
   \text{LRD}_k(p) = \frac{1}{\frac{1}{k} \sum_{o \in N_k(p)} \text{reach-dist}_k(p, o)}
   $$
4. LOF:
   $$
   \text{LOF}_k(p) = \frac{\frac{1}{k} \sum_{o \in N_k(p)} \text{LRD}_k(o)}{\text{LRD}_k(p)}
   $$

**Interpretation:**

- LOF ≈ 1: normal density match with neighbors.
- LOF > 1: density lower than neighbors → potential outlier.
- LOF >> 1 (e.g., > 2): strong outlier signal.

**Key advantage:** Detects **local** anomalies — a point can be normal relative to the whole dataset but abnormal within its neighborhood.

```python
from sklearn.neighbors import LocalOutlierFactor

lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
outliers = lof.fit_predict(X)  # -1 = outlier
scores = -lof.negative_outlier_factor_  # higher = more outlier
```

---

## Q89. Evaluating clustering without labels: internal vs external metrics. { #q89 }

**Internal metrics** (no ground truth needed):

| Metric | Measures | Range | Better |
|---|---|---|---|
| Silhouette | Tightness + separation | [-1, 1] | Higher |
| Davies-Bouldin | Avg within-/between-cluster ratio | [0, ∞) | Lower |
| Calinski-Harabasz | Variance ratio | [0, ∞) | Higher |
| Dunn Index | Min inter / max intra cluster distance | [0, ∞) | Higher |

**External metrics** (require ground truth labels):

| Metric | Range | Better | Notes |
|---|---|---|---|
| Adjusted Rand Index (ARI) | [-1, 1] | Higher | Corrected for chance |
| Normalized Mutual Info (NMI) | [0, 1] | Higher | Information-theoretic |
| Fowlkes-Mallows | [0, 1] | Higher | Geometric mean of precision/recall |
| Homogeneity / Completeness / V-measure | [0, 1] | Higher | Different facets |

**Rule of thumb:**

- No labels: use silhouette + visual inspection (scatter, silhouette plot).
- Labels exist: ARI is the gold standard (handles class count mismatch).

```python
from sklearn.metrics import silhouette_score, adjusted_rand_score, davies_bouldin_score

# Internal
sil = silhouette_score(X, labels)
db = davies_bouldin_score(X, labels)

# External (with true labels)
ari = adjusted_rand_score(y_true, labels)
```

---

## Q90. Scenario: segment customers from purchase data. Walk through. { #q90 }

**Data:** `customer_id`, `transactions` (date, amount, category), demographic data.

**Step 1 — Feature engineering (RFM + more):**

```python
features = customers.agg({
    'days_since_last_purchase': 'Recency',
    'total_transactions': 'Frequency',
    'total_amount_spent': 'Monetary',
    'avg_transaction_value': 'AOV',
    'unique_categories_bought': 'Breadth',
    'days_active': 'Tenure',
    'weekend_purchase_ratio': 'TimingPattern',
})
```

**Step 2 — Preprocess:**

- Log-transform heavy-tailed features (monetary values).
- Standardize.

**Step 3 — Decide method:**

- If unsure about K → **HDBSCAN** (finds natural clusters + outliers).
- If stakeholders need a fixed K (e.g., 4 segments for marketing) → **K-means** with K = 4.

**Step 4 — Pick K (if K-means):** Silhouette + domain knowledge.

**Step 5 — Interpret clusters:**

- Profile each cluster by feature means.
- Visualize with 2D UMAP.
- Label them: "Champions," "At-Risk," "Newcomers," "Loyal Low-Spenders."

**Step 6 — Validate:**

- Are clusters actionable? (Can marketing target them differently?)
- Are clusters stable over time? (Run monthly; check transition matrix.)

**Step 7 — Deploy:**

- Score new customers by nearest cluster center.
- Monitor cluster sizes — if distribution shifts dramatically, re-cluster.

<div class="tip-box" markdown>
**Interviewer signal:** The key is interpretation, not sophistication. A 4-cluster K-means that marketing actually uses beats a 25-cluster HDBSCAN that sits in a notebook. Ask yourself: *what action does each cluster enable?*
</div>

---

## Q91. What is collaborative filtering? { #q91 }

**Collaborative filtering (CF):** Predict user preferences by finding patterns across many users. Two flavors:

**1. Memory-based / neighborhood methods:**

- **User-user CF:** Find users similar to you; recommend what they liked.
- **Item-item CF:** Find items similar to what you've liked; recommend those.

Similarity: cosine similarity, Pearson correlation, adjusted cosine.

**2. Model-based:**

- **Matrix factorization:** Decompose the user-item matrix into user and item latent vectors.
- **Deep learning:** Neural collaborative filtering, two-tower models.

**Pros of CF:**

- No content features needed — just interactions.
- Captures latent preferences users can't articulate.

**Cons:**

- **Cold start:** New users/items have no interactions.
- **Sparsity:** Most user-item pairs are unobserved.
- **Popularity bias:** Recommends popular items.

---

## Q92. Explain Matrix Factorization for recommenders. { #q92 }

**Setup:** User-item rating matrix $R \in \mathbb{R}^{n_u \times n_i}$, mostly missing.

**Factorize:**

$$
R \approx P Q^\top
$$

where $P \in \mathbb{R}^{n_u \times k}$ (user factors) and $Q \in \mathbb{R}^{n_i \times k}$ (item factors).

**Training:** Minimize squared error on observed entries + regularization:

$$
\min_{P, Q} \sum_{(u, i) \in \text{observed}} (r_{ui} - p_u^\top q_i)^2 + \lambda (\|P\|^2 + \|Q\|^2)
$$

Solved via SGD or Alternating Least Squares (ALS).

**With biases (much better):**

$$
\hat{r}_{ui} = \mu + b_u + b_i + p_u^\top q_i
$$

where $\mu$ is the global mean, $b_u$ is user bias ("this user rates high on average"), $b_i$ is item bias ("this movie is generally well-rated").

**For implicit feedback** (clicks, views — no ratings, just presence/absence):

ALS with confidence weighting (Hu, Koren, Volinsky 2008):

$$
\min \sum_{u, i} c_{ui} (p_{ui} - p_u^\top q_i)^2 + \lambda (\|P\|^2 + \|Q\|^2)
$$

where $p_{ui} = 1$ if interaction, 0 otherwise, and $c_{ui}$ scales with strength.

```python
# Using Surprise library
from surprise import Dataset, SVD, Reader
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(df[['user_id', 'item_id', 'rating']], reader)

algo = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
algo.fit(data.build_full_trainset())

# Using implicit library for ALS
import implicit
model = implicit.als.AlternatingLeastSquares(factors=50, regularization=0.01, iterations=20)
model.fit(user_item_matrix)
```

---

## Q93. What is the Apriori algorithm? { #q93 }

**Apriori:** Classical algorithm for **frequent itemset mining** and **association rule learning** (e.g., market basket analysis).

**Goal:** Find rules like "customers who buy bread and butter also buy milk" with high support and confidence.

**Definitions:**

- **Support(X):** fraction of transactions containing itemset $X$.
- **Confidence(X → Y):** $P(Y | X)$ = Support(X ∪ Y) / Support(X).
- **Lift(X → Y):** Confidence(X → Y) / Support(Y) — lift > 1 means positive association.

**Apriori principle:** If an itemset is frequent, all its subsets are frequent. (Contrapositive: if a subset is infrequent, no superset can be frequent — prune early.)

**Algorithm:**

1. Find all size-1 frequent itemsets.
2. Generate candidate size-2 itemsets from frequent size-1.
3. Prune candidates whose subsets are infrequent.
4. Count support for remaining; keep frequent.
5. Repeat for sizes 3, 4, ...

```python
from mlxtend.frequent_patterns import apriori, association_rules

frequent = apriori(basket_df, min_support=0.02, use_colnames=True)
rules = association_rules(frequent, metric='lift', min_threshold=1.2)
```

**Modern alternative: FP-Growth.** Faster via a tree structure — no candidate generation.

---

## Q94. What's dimensionality reduction's impact on clustering? { #q94 }

**Positive effects:**

- Removes redundant/noisy dimensions → cleaner cluster boundaries.
- Combats curse of dimensionality — distances become meaningful again.
- Faster clustering (especially for distance-based methods like hierarchical).

**Negative effects:**

- Can *destroy* cluster structure if reduction is too aggressive or wrong method.
- PCA maximizes variance, not cluster separation — top PCs may not be cluster-relevant.

**Best practices:**

| Situation | Reduction approach |
|---|---|
| Tabular, 20–100 features | PCA keeping 95% variance |
| Images | Pretrained CNN features → PCA or UMAP |
| Text | TF-IDF → SVD (LSA) or sentence embeddings → UMAP |
| Very high-dim | UMAP for visualization + clustering |

**For visualization only:** Use UMAP/t-SNE on top of PCA (pre-reduce to ~50 dims for speed).

**For clustering:** PCA is usually safer than UMAP — UMAP distorts distances in ways K-means and GMM don't expect.

```python
# Pre-reduce with PCA, then UMAP for visualization
pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('pca', PCA(n_components=50)),
    ('umap', UMAP(n_components=2))
])
X_viz = pipe.fit_transform(X)
```

---

## Q95. Explain hierarchical topic modeling (LDA topic models). { #q95 }

**Latent Dirichlet Allocation (LDA, not to be confused with Linear Discriminant Analysis):**

A generative probabilistic model for documents:

1. For each document, draw a topic distribution $\theta_d \sim \text{Dir}(\alpha)$.
2. For each word position, draw a topic $z \sim \text{Cat}(\theta_d)$.
3. Given that topic, draw a word $w \sim \text{Cat}(\phi_z)$ from its word distribution.

**Inference:** Observe the words, recover $\theta_d$ (doc's topic mix), $\phi_z$ (topic's word distribution). Done via variational inference or Gibbs sampling.

**Hyperparameters:**

- $\alpha$: Dirichlet prior on doc-topic distribution. Small $\alpha$ → docs have few topics.
- $\beta$: Dirichlet prior on topic-word distribution. Small $\beta$ → topics have few key words.
- $K$: number of topics (must specify).

**Use cases:**

- **Document clustering** (docs have soft topic membership).
- **Content-based recommendations.**
- **Search expansion.**

**Modern alternative:** BERTopic — uses sentence embeddings + UMAP + HDBSCAN + c-TF-IDF. Often produces more coherent topics than LDA.

```python
# Classical LDA (sklearn)
from sklearn.decomposition import LatentDirichletAllocation
lda = LatentDirichletAllocation(n_components=20, random_state=42).fit(X_counts)

# Modern alternative
from bertopic import BERTopic
model = BERTopic().fit_transform(documents)
```

<div class="tip-box" markdown>
**Interview angle:** "Why use LDA over K-means on TF-IDF?" Answer: LDA gives **soft, probabilistic** topic membership — a document can be 60% about "politics" and 40% about "economy." K-means forces a hard assignment. Plus, LDA's topic-word distributions are interpretable; K-means cluster centroids on TF-IDF are harder to read.
</div>
