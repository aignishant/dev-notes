# Module 3 — Distance & Probabilistic Models

Fifteen questions on KNN, Naive Bayes, LDA/QDA, Gaussian Mixture Models, and their cousins. These are the algorithms of "geometric intuition" and "probabilistic reasoning" — interviewers use them to probe whether you understand *distance* and *likelihood* as first principles.

---

## Q41. Explain KNN from scratch. What's the training algorithm? { #q41 }

**Training:** Store the training data. That's it. KNN is a **lazy learner** — no model is fit.

**Prediction for a new point $x$:**

1. Compute distance from $x$ to every training point.
2. Find the $k$ nearest neighbors.
3. For classification: majority vote (optionally weighted by inverse distance).
4. For regression: mean (or weighted mean) of their target values.

**Distance metrics:**

| Metric | Formula | When to use |
|---|---|---|
| Euclidean | $\sqrt{\sum (x_i - y_i)^2}$ | Continuous, roughly normalized features |
| Manhattan | $\sum \|x_i - y_i\|$ | Grid-like data, robust to outliers |
| Minkowski | $(\sum \|x_i - y_i\|^p)^{1/p}$ | Generalizes the two |
| Cosine | $1 - \frac{x \cdot y}{\|x\| \|y\|}$ | Text, high-dim, magnitude-invariant |
| Mahalanobis | $\sqrt{(x-y)^\top \Sigma^{-1} (x-y)}$ | When features are correlated / different scales |

```python
from sklearn.neighbors import KNeighborsClassifier

knn = KNeighborsClassifier(
    n_neighbors=5,
    weights='distance',   # closer neighbors count more
    metric='euclidean',
    n_jobs=-1
).fit(X_train, y_train)
```

---

## Q42. How do you pick the right k in KNN? { #q42 }

**Tradeoffs:**

- **Small k (k=1):** Highly flexible, overfits, sensitive to noise.
- **Large k (k=n):** Predicts the global majority class for everything — underfits.

**Rules of thumb:**

- Start with $k = \sqrt{n}$.
- Use cross-validation over a grid (typically k = 3, 5, 7, ..., 51).
- Prefer **odd** k for binary classification to avoid ties.

**Visualize:** Plot accuracy vs k. You'll usually see a noisy increase, a plateau, then decline. Pick the lowest k in the plateau.

```python
from sklearn.model_selection import cross_val_score

scores = {k: cross_val_score(KNeighborsClassifier(n_neighbors=k), X, y, cv=5).mean()
          for k in range(1, 52, 2)}
best_k = max(scores, key=scores.get)
```

<div class="tip-box" markdown>
**Interviewer insight:** KNN's $k$ is directly a bias-variance dial. Low k = high variance. High k = high bias. The plot of error vs k is a textbook bias-variance U-curve.
</div>

---

## Q43. Why does KNN struggle in high dimensions (curse of dimensionality)? { #q43 }

In high dimensions, **all points become approximately equidistant**. The ratio between the nearest and farthest points goes to 1 as dimensionality increases:

$$
\lim_{d \to \infty} \frac{\text{max\_dist} - \text{min\_dist}}{\text{min\_dist}} \to 0
$$

**Intuition:** In 1D, "near" is meaningful (within 0.1 on a [0,1] scale). In 100D, the volume of a $\epsilon$-ball is negligibly small compared to the unit cube — all points are "far."

**Consequence:** The concept of "nearest neighbor" loses meaning. KNN's predictions become little better than random.

**Practical thresholds:**

- $d < 20$: KNN works fine with enough data.
- $20 \leq d \leq 100$: KNN degrades; need a lot more data.
- $d > 100$: Avoid KNN unless you first apply dimensionality reduction.

**Fixes:**

- **Dimensionality reduction** (PCA, UMAP, autoencoder) before KNN.
- **Feature selection** to remove irrelevant features.
- **Metric learning** (LMNN, NCA) to learn a better distance.
- **Locality-sensitive hashing** for efficient approximate KNN.

---

## Q44. Why must you scale features for KNN? { #q44 }

KNN is distance-based. If feature A ranges [0, 1] and feature B ranges [0, 1M], then feature B dominates the distance calculation. The model effectively ignores A.

**Example:** Predicting house prices from `(bedrooms, square_feet)`. Bedrooms ∈ [1, 10], sqft ∈ [500, 5000]. Without scaling, bedrooms contribute negligibly; all neighbors are chosen by sqft alone.

**Solutions:**

| Scaler | Formula | When |
|---|---|---|
| StandardScaler | $(x - \mu) / \sigma$ | Default; assumes ~normal data |
| MinMaxScaler | $(x - \min) / (\max - \min)$ | Bounded range [0,1] |
| RobustScaler | $(x - \text{median}) / \text{IQR}$ | Outliers present |
| Normalizer | $x / \|x\|$ | Cosine-like distances |

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

knn_pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('knn', KNeighborsClassifier(n_neighbors=5))
]).fit(X, y)
```

**KNN is one of the few models where forgetting to scale is catastrophic.** Tree models don't care; linear models are sensitive to scale for convergence but not for final predictions.

---

## Q45. What data structures make KNN fast? { #q45 }

Naive KNN is $O(n \cdot d)$ per query — check distance to every training point. For large training sets, this is prohibitive.

**Spatial data structures:**

**1. KD-Tree:** Binary tree that recursively partitions space by splitting on one dimension at a time. Query time: $O(\log n)$ in low dimensions, degrades to $O(n)$ when $d \gtrsim 20$.

**2. Ball Tree:** Partitions space into nested hyperspheres. Handles higher dimensions better than KD-Tree.

**3. Locality-Sensitive Hashing (LSH):** Hashes similar points to the same buckets with high probability. Approximate, but scales to millions of points and hundreds of dimensions.

**4. HNSW (Hierarchical Navigable Small World):** Graph-based approximate nearest neighbor. Dominates modern vector search (FAISS, Weaviate, Pinecone use HNSW variants).

```python
# sklearn auto-selects algorithm
KNeighborsClassifier(algorithm='auto')

# Explicit
KNeighborsClassifier(algorithm='ball_tree')
KNeighborsClassifier(algorithm='kd_tree')
KNeighborsClassifier(algorithm='brute')

# For millions of points, use FAISS
import faiss
index = faiss.IndexHNSWFlat(d, 32)
index.add(X_train.astype('float32'))
D, I = index.search(X_query.astype('float32'), k=5)
```

---

## Q46. Derive Naive Bayes for a classification problem. { #q46 }

**Bayes theorem:**

$$
P(y \mid x_1, \dots, x_p) = \frac{P(y) \cdot P(x_1, \dots, x_p \mid y)}{P(x_1, \dots, x_p)}
$$

The denominator doesn't depend on $y$, so we just need to maximize the numerator:

$$
\hat{y} = \arg\max_y P(y) \cdot P(x_1, \dots, x_p \mid y)
$$

**The "naive" assumption:** features are conditionally independent given the class.

$$
P(x_1, \dots, x_p \mid y) = \prod_{j=1}^{p} P(x_j \mid y)
$$

So:

$$
\hat{y} = \arg\max_y P(y) \cdot \prod_{j=1}^{p} P(x_j \mid y)
$$

In practice, we use log-probabilities to avoid underflow:

$$
\hat{y} = \arg\max_y \log P(y) + \sum_{j=1}^{p} \log P(x_j \mid y)
$$

**Why "naive"?** Because conditional independence of features given the class is almost never true in reality. Yet Naive Bayes often works well anyway — the decision is based on *ranking* classes, not absolute probability, and rank is often preserved even when probabilities are miscalibrated.

---

## Q47. What's the difference between Gaussian, Multinomial, and Bernoulli Naive Bayes? { #q47 }

Different assumptions about $P(x_j \mid y)$:

| Variant | $P(x_j \mid y)$ | Use case |
|---|---|---|
| **Gaussian NB** | $\mathcal{N}(\mu_{jy}, \sigma_{jy}^2)$ | Continuous features |
| **Multinomial NB** | Multinomial over word counts | Text with term frequencies |
| **Bernoulli NB** | Bernoulli (0 or 1) | Text with binary presence |
| **Complement NB** | Modified multinomial | Imbalanced text classification |
| **Categorical NB** | Categorical distribution | Discrete features with few values |

**For text:** If documents are short or features are already binarized, Bernoulli NB often wins. If you're using TF or TF-IDF, Multinomial NB is standard.

```python
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB

# Continuous
model = GaussianNB().fit(X, y)

# Text with CountVectorizer
model = MultinomialNB(alpha=1.0).fit(X_counts, y)

# Text with binarized features
model = BernoulliNB().fit(X_binary, y)
```

**Laplace (additive) smoothing** (`alpha` parameter) prevents zero probabilities when a class-feature combination has zero count in training.

---

## Q48. Why does Naive Bayes work well for text despite the naive assumption? { #q48 }

Three reasons:

**1. High-dimensional word features.** Many words contribute weak evidence, so the product of many slightly-wrong probabilities averages out. The final ranking is robust.

**2. Fast and scalable.** Training is one pass over the data (count frequencies + Laplace smoothing). It's essentially free compared to other models, which matters when you have millions of documents.

**3. Works with tiny data.** Because of the strong independence assumption, NB has very few parameters — excellent when training data is limited.

**Where NB fails:**

- When feature *interactions* matter (e.g., "not good" vs "good"). NB treats "not" and "good" independently.
- When features are heavily correlated — NB double-counts evidence.
- When calibrated probabilities are needed — NB probabilities are often poorly calibrated.

**Historical note:** Naive Bayes was the dominant email spam classifier until ~2010, when L2-regularized logistic regression and tree ensembles surpassed it.

---

## Q49. Explain Linear Discriminant Analysis (LDA). How is it different from PCA? { #q49 }

**LDA** is a **supervised** dimensionality reduction and classification method.

**Assumptions:** Each class is drawn from a Gaussian with class-specific mean $\mu_k$ and **shared covariance matrix** $\Sigma$.

**Goal:** Project to a $(K-1)$-dim subspace that maximizes class separability.

**Fisher's criterion:** Maximize the ratio of between-class variance to within-class variance:

$$
J(w) = \frac{w^\top S_B w}{w^\top S_W w}
$$

where:

$$
S_W = \sum_k \sum_{i \in \text{class } k} (x_i - \mu_k)(x_i - \mu_k)^\top
$$

$$
S_B = \sum_k n_k (\mu_k - \mu)(\mu_k - \mu)^\top
$$

Solution: eigenvectors of $S_W^{-1} S_B$ corresponding to largest eigenvalues.

**LDA as classifier:** Once projected, use the Gaussian assumption to derive a linear decision boundary (Bayes-optimal under shared-covariance assumption):

$$
\delta_k(x) = x^\top \Sigma^{-1} \mu_k - \frac{1}{2} \mu_k^\top \Sigma^{-1} \mu_k + \log \pi_k
$$

**LDA vs PCA:**

| Aspect | PCA | LDA |
|---|---|---|
| Supervised | No | Yes |
| Goal | Maximize variance | Maximize class separability |
| Output dimension | Up to $p$ | At most $K - 1$ |
| Assumption | None (just linear) | Gaussian classes, shared Σ |

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

lda = LinearDiscriminantAnalysis(n_components=2)
X_proj = lda.fit_transform(X, y)  # supervised, uses y
```

---

## Q50. What's Quadratic Discriminant Analysis (QDA)? When would you use it over LDA? { #q50 }

**QDA** allows each class to have its **own covariance matrix** $\Sigma_k$. This leads to **quadratic** decision boundaries.

$$
\delta_k(x) = -\frac{1}{2} \log |\Sigma_k| - \frac{1}{2} (x - \mu_k)^\top \Sigma_k^{-1} (x - \mu_k) + \log \pi_k
$$

**When QDA beats LDA:**

- Class covariances are genuinely different.
- Enough data to estimate $K$ covariance matrices reliably (each has $p(p+1)/2$ parameters).

**When LDA beats QDA:**

- Small sample sizes — QDA needs more data because it estimates more parameters.
- Classes have similar shapes/scales — QDA's extra flexibility just overfits.

**Rule of thumb:** If $n_k < 20p$, prefer LDA. Otherwise, try both.

**Regularized DA (RDA)** interpolates between LDA and QDA:

$$
\tilde{\Sigma}_k = \alpha \Sigma_k + (1 - \alpha) \Sigma
$$

for $\alpha \in [0, 1]$. sklearn exposes this as `shrinkage` in LDA and RDA.

---

## Q51. Explain Gaussian Mixture Models (GMM). { #q51 }

**GMM** models data as a weighted sum of $K$ Gaussians:

$$
p(x) = \sum_{k=1}^{K} \pi_k \mathcal{N}(x \mid \mu_k, \Sigma_k)
$$

Parameters: mixture weights $\pi_k$, means $\mu_k$, covariances $\Sigma_k$. Constraint: $\sum \pi_k = 1$.

**Fitted via Expectation-Maximization (EM):**

- **E-step:** Given current parameters, compute "responsibility" of each cluster for each point:
  $$
  \gamma_{ik} = \frac{\pi_k \mathcal{N}(x_i \mid \mu_k, \Sigma_k)}{\sum_j \pi_j \mathcal{N}(x_i \mid \mu_j, \Sigma_j)}
  $$
- **M-step:** Update parameters as weighted averages using responsibilities:
  $$
  \mu_k = \frac{\sum_i \gamma_{ik} x_i}{\sum_i \gamma_{ik}}
  $$

Repeat until log-likelihood converges.

**Uses:**

- **Soft clustering** — each point has a probability of belonging to each cluster (unlike K-means' hard assignment).
- **Density estimation** — $p(x)$ can be evaluated for any new point.
- **Anomaly detection** — low $p(x)$ signals anomaly.

**Covariance types:**

| Type | Shape | Parameters |
|---|---|---|
| `full` | Arbitrary ellipses | $K p^2$ |
| `tied` | Same ellipse, different centers | $p^2$ |
| `diag` | Axis-aligned ellipses | $K p$ |
| `spherical` | Circles | $K$ |

```python
from sklearn.mixture import GaussianMixture

gmm = GaussianMixture(
    n_components=5,
    covariance_type='full',
    random_state=42
).fit(X)

labels = gmm.predict(X)             # hard assignments
probs = gmm.predict_proba(X)        # soft assignments
log_density = gmm.score_samples(X)  # anomaly score
```

---

## Q52. How do you pick the number of components in a GMM? { #q52 }

Three common approaches:

**1. BIC (Bayesian Information Criterion):**

$$
\text{BIC} = -2 \log \mathcal{L} + k \log n
$$

Penalizes model complexity. Lower is better. Fit GMM for K = 1, 2, ..., 20 and pick the K with minimum BIC.

**2. AIC (Akaike Information Criterion):**

$$
\text{AIC} = -2 \log \mathcal{L} + 2k
$$

Less aggressive penalty than BIC. Tends to favor slightly more complex models.

**3. Held-out log-likelihood:** Compute log-likelihood on a held-out set for different K.

```python
bics = []
for k in range(1, 21):
    gmm = GaussianMixture(n_components=k, covariance_type='full').fit(X)
    bics.append(gmm.bic(X))

best_k = np.argmin(bics) + 1
```

**BIC vs AIC:** BIC is more conservative (prefers fewer components). Use BIC when you want the "most parsimonious" model, AIC when you want predictive accuracy.

**Variational Bayesian GMM (`BayesianGaussianMixture`)** automatically pushes unnecessary component weights to zero — no need to tune K manually.

---

## Q53. What's the EM algorithm? Why does it converge? { #q53 }

**EM (Expectation-Maximization):** General algorithm for maximum likelihood estimation when there are latent (unobserved) variables.

**Setup:** Data $X$, latent $Z$, parameters $\theta$. We want $\arg\max_\theta p(X \mid \theta)$, but $p(X \mid \theta) = \int p(X, Z \mid \theta) dZ$ — hard.

**E-step:** Given current $\theta^{(t)}$, compute expected log-likelihood w.r.t. posterior over $Z$:

$$
Q(\theta \mid \theta^{(t)}) = \mathbb{E}_{Z \mid X, \theta^{(t)}}[\log p(X, Z \mid \theta)]
$$

**M-step:** Find $\theta$ that maximizes $Q$:

$$
\theta^{(t+1)} = \arg\max_\theta Q(\theta \mid \theta^{(t)})
$$

**Why it converges:** Each EM iteration is guaranteed to increase (or keep equal) the observed-data log-likelihood $\log p(X \mid \theta)$. This comes from Jensen's inequality — $Q$ is a *lower bound* on the true log-likelihood, and maximizing the bound pushes the true log-likelihood up too.

**Caveat:** EM converges to a **local** maximum. Multiple restarts with random initializations are standard practice.

**EM applications beyond GMM:**

- K-means (hard-assignment version of GMM with shared spherical covariance).
- Hidden Markov Models (HMM) via Baum-Welch.
- Topic models (LDA) via variational EM.
- Collaborative filtering with missing values.

---

## Q54. Compare KNN, Logistic Regression, and Naive Bayes. { #q54 }

| Dimension | KNN | Logistic Regression | Naive Bayes |
|---|---|---|---|
| **Learning style** | Instance-based (lazy) | Model-based | Model-based |
| **Assumption** | Local smoothness | Linear decision boundary | Feature independence given class |
| **Training time** | $O(1)$ (just store) | $O(npk)$ | $O(np)$ |
| **Prediction time** | $O(nd)$ per query (or $\log n$ with trees) | $O(p)$ | $O(Kp)$ |
| **Memory** | $O(np)$ | $O(p)$ | $O(Kp)$ |
| **Handles non-linearity** | Yes (via local neighbors) | Only with feature engineering | Weak (through joint distribution) |
| **Handles high-dim data** | Poor (curse of dim) | Good | Excellent (esp. for text) |
| **Handles missing values** | Poor | Needs imputation | Naturally (just skip that feature's probability) |
| **Probabilistic output** | Fraction of neighbors | Calibrated-ish | Often miscalibrated |
| **Interpretability** | None | High (coefficients) | Medium |

**When each wins:**

- **KNN:** Small, low-dim, non-linear problems; recommender systems (user/item nearest neighbors).
- **Logistic Regression:** Linearly separable problems; huge sparse data (billions of rows, millions of features); interpretability.
- **Naive Bayes:** Text classification; small datasets; need fast baseline.

---

## Q55. Scenario: A candidate says "KNN is a great first model." How do you push back? { #q55 }

**Your pushback (with production reality):**

> "KNN sounds elegant, but in production it has several serious issues:
>
> 1. **Inference cost scales with dataset size.** If we have 10M rows, every prediction requires computing 10M distances. Even with KD-trees, this is prohibitive in real-time systems. LightGBM predicts in microseconds regardless of training set size.
>
> 2. **Memory footprint is the whole training set.** Redis-based serving of 10M rows × 50 features is ~2 GB. Most tree models fit in 20 MB.
>
> 3. **Curse of dimensionality.** Above ~20 features, distances become meaningless. We'd need aggressive dimensionality reduction first.
>
> 4. **No handling of mixed types.** Categorical + continuous + missing values? You'd need custom preprocessing for each.
>
> 5. **Feature scaling is brittle.** If a data pipeline changes the scale of one feature, KNN's behavior changes drastically. LightGBM is scale-invariant.
>
> 6. **No interpretability.** 'Your prediction is 0.8 because your 5 nearest neighbors had labels [1, 1, 1, 0, 1]' is not a satisfying business explanation.
>
> For a first model on tabular data, I'd reach for LightGBM — better accuracy, faster inference, easier to maintain, better SHAP explanations. KNN has a place for semantic search or simple exploratory work, but not as a production baseline."

<div class="tip-box" markdown>
**Interview meta-signal:** Pushing back on a "standard answer" with specific production reasoning demonstrates seniority. Junior candidates accept textbook algorithms; senior candidates challenge them.
</div>
