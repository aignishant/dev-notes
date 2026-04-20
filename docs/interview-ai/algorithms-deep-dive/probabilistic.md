# Module 4 — Probabilistic & Instance-Based

**Questions 51–65.** Naive Bayes, kNN, Bayesian networks, HMMs. These don't win Kaggle anymore, but they power production systems in search, spam filtering, and medical diagnosis — and interviewers love them because they test your probability chops.

---

## Q51. Derive Naive Bayes from Bayes' rule. Why "naive"? { #q51 }

**Bayes' rule:**

\[
P(y | x) = \frac{P(x | y) P(y)}{P(x)}
\]

Modeling `P(x | y)` directly is hard if `x` is high-dimensional — the joint has `2^d - 1` parameters for binary features.

**Naive assumption:** features are **conditionally independent** given the class.

\[
P(x_1, x_2, \ldots, x_d | y) = \prod_{j=1}^d P(x_j | y)
\]

This reduces parameters from exponential to linear in `d`.

**Classification:**

\[
\hat{y} = \arg\max_y P(y) \prod_j P(x_j | y)
\]

To avoid numerical underflow, use log-likelihood:

\[
\hat{y} = \arg\max_y \log P(y) + \sum_j \log P(x_j | y)
\]

**Why "naive":** the conditional independence assumption is almost never true. Words in an email co-occur; symptoms correlate with age.

**Why it still works:** NB is biased but low-variance. When you have little data or many features, the bias is tolerable and variance gains dominate.

```python
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB

# Continuous features
gnb = GaussianNB()

# Count features (text TF, bag-of-words)
mnb = MultinomialNB(alpha=1.0)  # alpha = Laplace smoothing

# Binary features (word present/absent)
bnb = BernoulliNB(alpha=1.0)
```

<div class="tip-box" markdown>
**Senior signal:** "NB is often surprisingly good at *ranking* even when miscalibrated. I'd use it as a fast baseline for text classification — trains in seconds, predicts in microseconds, often within 5% of the best model."
</div>

---

## Q52. When does Naive Bayes fail badly? { #q52 }

**1. Strongly correlated features.**

If two features are duplicates, NB multiplies their likelihoods twice → double-counts evidence → overconfident predictions.

*Fix:* deduplicate features before fitting.

**2. Features with zero training examples in some class.**

`P(x_j = v | y = k) = 0` zeros out the entire product. The classifier says class `k` is impossible.

*Fix:* **Laplace / add-alpha smoothing**:

\[
P(x_j = v | y) = \frac{count(x_j = v, y) + \alpha}{count(y) + \alpha \cdot V}
\]

where `V` is vocabulary size.

```python
mnb = MultinomialNB(alpha=1.0)  # alpha=1 is Laplace; alpha=0.01 is "add-epsilon"
```

**3. Continuous features with non-Gaussian distribution.**

GaussianNB assumes features are Gaussian given class. Heavy-tailed or bimodal features break this.

*Fix:* discretize features, or use KernelNB (kernel density estimation per class).

**4. Imbalanced classes cause skewed priors.**

NB uses empirical class priors. If minority is 0.1%, `log P(y=1)` is always tiny → need very strong evidence.

*Fix:* manually set `class_prior` to uniform or business-appropriate weights.

---

## Q53. How does Multinomial Naive Bayes work for text classification? { #q53 }

**Model.** For each class `y`, represent a document as a bag-of-words with counts `x = (x_1, ..., x_V)`:

\[
P(x | y) = \frac{(\sum_j x_j)!}{\prod_j x_j!} \prod_j \theta_{jy}^{x_j}
\]

where `θ_{jy}` is the probability of word `j` in class `y`.

**MLE estimate** (with Laplace smoothing):

\[
\hat{\theta}_{jy} = \frac{count(word_j, class_y) + \alpha}{\sum_{j'} count(word_{j'}, class_y) + \alpha V}
\]

**Prediction:** classify via log-posterior.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95)),
    ('clf', MultinomialNB(alpha=0.1)),
])
pipe.fit(texts_train, y_train)

# Inspect most predictive words per class
import numpy as np
feature_names = pipe['tfidf'].get_feature_names_out()
class_names = pipe['clf'].classes_

for i, cls in enumerate(class_names):
    top_idx = np.argsort(pipe['clf'].feature_log_prob_[i])[-20:]
    print(f"Class {cls}: {[feature_names[j] for j in top_idx]}")
```

**NB vs logistic regression on text:**

- NB: faster to train, small data friendly, generative (can sample), miscalibrated probabilities.
- Logistic: usually 1-3% better accuracy with good regularization, probabilities are calibrated.

<div class="scenario" markdown>
**Real production story:** a spam classifier at a major email provider ran Naive Bayes for over a decade. Logistic regression was tested and beat NB by 2% AUC, but NB's 500μs inference latency vs 2ms meant NB remained the primary filter; logistic was used only on the borderline cases.
</div>

---

## Q54. What's k-Nearest Neighbors, and what are its variants? { #q54 }

**Core algorithm (kNN):**

Given a test point `x`:

1. Find the `k` nearest training points by some distance metric.
2. Predict majority class (classification) or mean of their labels (regression).

**Distance metrics:**

| Metric | Formula | Use case |
|---|---|---|
| Euclidean | `√Σ(x_i - y_i)²` | Continuous, scaled features |
| Manhattan | `Σ|x_i - y_i|` | High-dim, sparse data |
| Cosine | `1 - x·y / (‖x‖‖y‖)` | Text, embeddings |
| Minkowski | `(Σ|x_i - y_i|^p)^(1/p)` | Generalization of above |
| Hamming | count of unequal dims | Categorical features |

**Variants:**

**1. Weighted kNN.** Weight neighbors by inverse distance:

```python
from sklearn.neighbors import KNeighborsClassifier

knn = KNeighborsClassifier(n_neighbors=15, weights='distance')
# Each neighbor contributes 1/distance to the vote
```

**2. Radius-based.** Use all neighbors within radius `r` instead of top-k.

```python
from sklearn.neighbors import RadiusNeighborsClassifier

rnn = RadiusNeighborsClassifier(radius=1.0)
# Handles variable-density data better, but can fail if a test point has 0 neighbors
```

**3. Approximate kNN (ANN).** For large datasets, exact kNN is O(n) per query. Libraries like `faiss`, `Annoy`, `hnswlib`, `scann` build indexes for sub-linear lookup with tunable accuracy.

```python
import faiss
import numpy as np

d = X_train.shape[1]
index = faiss.IndexFlatL2(d)
index.add(X_train.astype(np.float32))

# Query 1000 test points at once, get top-10 neighbors
distances, indices = index.search(X_test.astype(np.float32), k=10)
```

---

## Q55. Why does kNN suffer from the curse of dimensionality? { #q55 }

**The curse.** In high dimensions, distances between all pairs of points become similar. kNN's assumption that "nearby points have similar labels" breaks down.

**Quantitative intuition.**

Consider `n` points uniformly in `[0, 1]^d`. To capture `k` neighbors on average, you need a hypercube of side length:

\[
\ell = (k / n)^{1/d}
\]

For `k = 10, n = 10000`:

- `d = 2`: ℓ = 0.03 (tiny)
- `d = 10`: ℓ = 0.5 (half the space!)
- `d = 100`: ℓ = 0.93 (nearly whole space)

The "neighborhood" stops being local.

**Mitigations:**

1. **Dimensionality reduction** — PCA, UMAP before kNN.
2. **Learned embeddings** — train an embedding model where Euclidean distance = semantic similarity (e.g., sentence transformers for text kNN).
3. **Feature selection** — drop noise dimensions.
4. **Switch algorithms** — trees, neural nets often handle high-dim better.

<div class="scenario" markdown>
**Real case:** a recommendation team tried kNN over 768-dim BERT embeddings. Performance was decent. They switched to a fine-tuned 64-dim embedding (distilled from BERT with contrastive loss) and recall@10 jumped 30%. Dimensionality *and* representation mattered.
</div>

---

## Q56. How do you choose `k` in kNN? { #q56 }

**Cross-validation.**

```python
from sklearn.model_selection import cross_val_score
import numpy as np

k_values = [1, 3, 5, 7, 9, 15, 25, 51, 101]
scores = []
for k in k_values:
    knn = KNeighborsClassifier(n_neighbors=k)
    score = cross_val_score(knn, X_train, y_train, cv=5).mean()
    scores.append(score)

best_k = k_values[np.argmax(scores)]
```

**Rules of thumb:**

- **k = 1**: no bias, high variance. Overfits.
- **k = n**: ignores input entirely, predicts mode. Underfits.
- **k ≈ √n**: classic heuristic.
- **Odd k** for binary classification to avoid ties.

**When k=1 actually wins:**

- Extremely noise-free data where each training point is trustworthy.
- Memorization baseline for research.

**When large k is needed:**

- Noisy labels — averaging reduces noise.
- Imbalanced classes — too small k amplifies minority-class noise.

---

## Q57. Why must you scale features before kNN? { #q57 }

**Problem.** Euclidean distance treats all features equally:

\[
d(x, y) = \sqrt{(x_1 - y_1)^2 + (x_2 - y_2)^2 + \ldots}
\]

If feature 1 ranges [0, 1000] and feature 2 ranges [0, 1], feature 1 dominates. kNN effectively ignores feature 2.

**Fix:** standardize.

```python
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('knn', KNeighborsClassifier(n_neighbors=7)),
])
pipe.fit(X_train, y_train)
```

**Beyond standardization — feature weighting.**

Even after scaling, features vary in *relevance*. Some features are noise. Weight them down:

```python
# Manual feature weighting by multiplying columns
weights = np.array([1.0, 1.0, 0.1, 2.0, ...])  # domain-informed
X_weighted = X * weights
```

Or use **mutual information** as automatic weights:

```python
from sklearn.feature_selection import mutual_info_classif
weights = mutual_info_classif(X_train, y_train)
X_weighted = X * weights
```

Or learned metrics (**LMNN, NCA**):

```python
from sklearn.neighbors import NeighborhoodComponentsAnalysis

nca = NeighborhoodComponentsAnalysis()
X_nca = nca.fit_transform(X_train, y_train)
knn.fit(X_nca, y_train)
```

---

## Q58. Explain Bayesian networks. Give a use case. { #q58 }

**Definition.** A Bayesian network (BN) is a directed acyclic graph (DAG) representing conditional dependencies among random variables.

- Nodes: variables.
- Edges: direct probabilistic dependencies.
- Each node has a **conditional probability table (CPT)** given its parents.

**Joint distribution factorizes:**

\[
P(X_1, \ldots, X_n) = \prod_i P(X_i | \text{Parents}(X_i))
\]

**Example — medical diagnosis.**

```
Smoker → LungDisease → XRayShadow
              ↓
          Coughing
```

Given this DAG:

\[
P(S, L, X, C) = P(S) P(L | S) P(X | L) P(C | L)
\]

**Why useful:**

1. **Causal reasoning.** Unlike a classifier, you can answer "if I intervene on X, what happens to Y?"
2. **Handles missing data** — BNs can reason about any variable from any subset.
3. **Expert knowledge integration** — experts draw the DAG; data fills the CPTs.
4. **Interpretable** — every edge has semantic meaning.

```python
# pgmpy is a Python library for Bayesian networks
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD

model = BayesianNetwork([('Smoker', 'LungDisease'), ('LungDisease', 'XRayShadow'),
                         ('LungDisease', 'Coughing')])

cpd_smoker = TabularCPD('Smoker', 2, [[0.7], [0.3]])
cpd_lung = TabularCPD('LungDisease', 2,
                      [[0.95, 0.70],    # P(LD=0 | Smoker=0, 1)
                       [0.05, 0.30]],   # P(LD=1 | Smoker=0, 1)
                      evidence=['Smoker'], evidence_card=[2])
# ... add other CPDs

model.add_cpds(cpd_smoker, cpd_lung, ...)
model.check_model()

# Inference
from pgmpy.inference import VariableElimination
infer = VariableElimination(model)
result = infer.query(variables=['LungDisease'], evidence={'Coughing': 1})
```

<div class="tip-box" markdown>
**Modern use cases:** drug trial analysis, fraud investigation, fault diagnosis, root-cause analysis. Still popular in any field where you need *causal* reasoning, not just prediction.
</div>

---

## Q59. What's a Hidden Markov Model? Walk through the three fundamental problems. { #q59 }

**HMM setup.** A sequence of hidden states `z_1, ..., z_T` each emits an observation `x_t`.

- **Transition probabilities:** `P(z_t | z_{t-1})`.
- **Emission probabilities:** `P(x_t | z_t)`.
- **Initial state:** `P(z_1)`.

**Markov assumption:** state depends only on previous state.

**Three problems and algorithms:**

| Problem | Question | Algorithm | Complexity |
|---|---|---|---|
| **Likelihood** | `P(x_1, ..., x_T | λ)` — how likely is this sequence under model λ? | Forward algorithm | O(TN²) |
| **Decoding** | What's the most likely state sequence? | Viterbi | O(TN²) |
| **Learning** | Given sequences, fit transition/emission probs | Baum-Welch (EM) | O(TN² × iters) |

**Forward algorithm** — compute `α_t(i) = P(x_{1:t}, z_t = i)` recursively:

\[
\alpha_t(i) = \left[ \sum_j \alpha_{t-1}(j) \cdot a_{ji} \right] \cdot b_i(x_t)
\]

**Viterbi** — same recurrence but with max instead of sum:

\[
v_t(i) = \max_j [v_{t-1}(j) \cdot a_{ji}] \cdot b_i(x_t)
\]

Plus backtracking pointers to recover the path.

```python
from hmmlearn import hmm

# Discrete emissions
model = hmm.CategoricalHMM(n_components=3, n_iter=100)
model.fit(X.reshape(-1, 1), lengths=[len(X)])

# Predict states (Viterbi)
states = model.predict(X_new.reshape(-1, 1))

# Sample a new sequence
generated, states = model.sample(100)
```

**Use cases (still alive):**

- **Speech recognition** (classical HMM-GMM systems pre-DL era).
- **Part-of-speech tagging** (now superseded by Transformers but HMM is the baseline).
- **Gene sequence modeling** in bioinformatics.
- **Market regime detection** (bull/bear hidden states).
- **User behavior sequences** (onboarded → engaged → churned).

---

## Q60. Compare HMM, CRF, and modern Transformers for sequence labeling. { #q60 }

All three can solve sequence labeling (POS tagging, NER, speech).

| Property | HMM | CRF | Transformer |
|---|---|---|---|
| Type | Generative | Discriminative | Discriminative |
| Models | Joint P(x, z) | Conditional P(z | x) | Conditional P(z | x) |
| Feature flexibility | Local emissions only | Arbitrary global features | Learned contextual reps |
| Label dependencies | Markov (first-order) | Adjacent (in linear chain) | Self-attention (all pairs) |
| Training | Baum-Welch (EM) or MLE | Log-likelihood (concave) | SGD on cross-entropy |
| Data requirements | Small OK | Medium | Large (or fine-tune pretrained) |
| State of the art? | No | Sometimes for low-resource | Yes for most benchmarks |

**Why CRF beats HMM** for most labeling tasks:

- HMM assumes features are conditionally independent given state.
- CRF lets you define arbitrary feature functions (current word, previous word, word shape, etc.).
- CRF optimizes the *conditional* likelihood — the metric you actually care about for classification.

**Why Transformer beats CRF** on large data:

- Learns features automatically (no hand-designed templates).
- Captures long-range dependencies through attention.
- Transfer learning from pretrained models like BERT.

**When HMM/CRF still wins:**

- Low-resource settings (few hundred labeled sequences).
- Explainability required (CRF feature weights are interpretable).
- Latency budget is tight.

```python
# sklearn-crfsuite for CRF
import sklearn_crfsuite

crf = sklearn_crfsuite.CRF(
    algorithm='lbfgs',
    c1=0.1,  # L1 regularization
    c2=0.1,  # L2 regularization
    max_iterations=100,
)
crf.fit(X_train, y_train)  # X is list of list of feature dicts
```

---

## Q61. What's kernel density estimation (KDE), and how does it relate to kNN? { #q61 }

**KDE** estimates a probability density from samples:

\[
\hat{f}(x) = \frac{1}{nh} \sum_{i=1}^n K\left(\frac{x - x_i}{h}\right)
\]

- `K` is a kernel function (Gaussian, Epanechnikov, etc.).
- `h` is bandwidth — smoothing parameter.

**Connection to kNN.** kNN density estimate uses an *adaptive* bandwidth — large `h` in sparse regions, small in dense regions.

\[
\hat{f}_{kNN}(x) = \frac{k}{n \cdot V_k(x)}
\]

where `V_k(x)` is the volume of the hypersphere containing the `k` nearest neighbors.

**Bandwidth selection for KDE:**

- **Silverman's rule** — closed-form estimate assuming Gaussian data.
- **Cross-validation** — grid search with log-likelihood.

```python
from sklearn.neighbors import KernelDensity
import numpy as np

# Grid search for bandwidth
from sklearn.model_selection import GridSearchCV

params = {'bandwidth': np.logspace(-1, 1, 20)}
grid = GridSearchCV(KernelDensity(kernel='gaussian'), params, cv=5)
grid.fit(X_train)

kde = grid.best_estimator_
density = np.exp(kde.score_samples(X_test))
```

**Use cases:**

- Visualization of 1D/2D distributions (prefer over histograms).
- Anomaly detection — low density = anomaly.
- Generative models (sample from KDE).

---

## Q62. How do mixture models work? Explain EM for Gaussian Mixture Model. { #q62 }

**Gaussian Mixture Model (GMM):**

\[
p(x) = \sum_{k=1}^K \pi_k \mathcal{N}(x | \mu_k, \Sigma_k)
\]

where `π_k` are mixing weights (sum to 1), `μ_k, Σ_k` are mean and covariance of component `k`.

**Why "mixture":** each point is assumed to be drawn from one of K Gaussians, but we don't know which.

**EM algorithm:**

**E-step — compute responsibilities:**

\[
\gamma_{ik} = \frac{\pi_k \mathcal{N}(x_i | \mu_k, \Sigma_k)}{\sum_{j=1}^K \pi_j \mathcal{N}(x_i | \mu_j, \Sigma_j)}
\]

(Probability that point `i` came from component `k`.)

**M-step — update parameters:**

\[
\pi_k = \frac{1}{n} \sum_i \gamma_{ik}
\]

\[
\mu_k = \frac{\sum_i \gamma_{ik} x_i}{\sum_i \gamma_{ik}}
\]

\[
\Sigma_k = \frac{\sum_i \gamma_{ik} (x_i - \mu_k)(x_i - \mu_k)^T}{\sum_i \gamma_{ik}}
\]

**Why EM?** The log-likelihood is non-concave (has multiple local maxima). EM is a hill-climbing procedure that monotonically increases log-likelihood.

**Initialization matters** — EM is local. Use K-means results as starting point (`init_params='kmeans'`).

```python
from sklearn.mixture import GaussianMixture
import numpy as np

gmm = GaussianMixture(
    n_components=3,
    covariance_type='full',   # 'full', 'tied', 'diag', 'spherical'
    init_params='kmeans',
    n_init=10,                # multiple restarts
    max_iter=200,
    random_state=42,
)
gmm.fit(X)

# Soft assignments (responsibilities)
proba = gmm.predict_proba(X)
# Hard assignments
labels = gmm.predict(X)
# Density estimates
log_density = gmm.score_samples(X)
```

**Choosing K:**

- BIC / AIC — penalize complexity.
- Variational Bayesian GMM (`BayesianGaussianMixture`) — automatically prunes unused components.

---

## Q63. What's the difference between K-means and GMM? { #q63 }

Both cluster data into K groups. Key differences:

| Property | K-means | GMM |
|---|---|---|
| Assignments | Hard (each point → one cluster) | Soft (probabilities over clusters) |
| Shape of clusters | Spherical (Euclidean distance) | Ellipsoidal (covariance-aware) |
| Handles cluster size variation | Poorly (biased toward equal-sized) | Yes (via `π_k`) |
| Output | Centroids only | Full probability distribution |
| Computational cost | O(nk) per iter | O(nk d²) per iter |
| Initialization sensitivity | High (use K-means++) | High (use K-means init) |

**GMM is K-means when:**

- Covariances are identity and equal.
- Responsibilities are hardened (argmax instead of soft).

**When to prefer K-means:**

- Clusters are genuinely spherical and equal-sized.
- You just need labels, not probabilities.
- Speed matters — K-means is faster.

**When to prefer GMM:**

- Clusters are elongated or differently shaped.
- You need probabilistic cluster membership (borderline points).
- Density estimation alongside clustering.

<div class="scenario" markdown>
**Visual check:** if you can cluster your data by drawing ellipses that are *not* circles, GMM with `covariance_type='full'` will dramatically outperform K-means.
</div>

---

## Q64. What's Bayesian inference, and how does it differ from MLE? { #q64 }

**MLE (Maximum Likelihood Estimation):**

\[
\hat{\theta}_{MLE} = \arg\max_\theta P(D | \theta)
\]

Finds single best point estimate of parameters.

**MAP (Maximum A Posteriori):**

\[
\hat{\theta}_{MAP} = \arg\max_\theta P(\theta | D) = \arg\max_\theta P(D | \theta) P(\theta)
\]

Adds a prior. Still a point estimate.

**Full Bayesian inference:**

\[
P(\theta | D) = \frac{P(D | \theta) P(\theta)}{\int P(D | \theta') P(\theta') d\theta'}
\]

Produces a *distribution* over `θ`, not a point. Predictions marginalize over this distribution:

\[
P(y | x, D) = \int P(y | x, \theta) P(\theta | D) d\theta
\]

**Advantages:**

1. **Uncertainty quantification** — get credible intervals, not just point estimates.
2. **Priors incorporate domain knowledge.**
3. **Natural regularization** — priors pull toward reasonable values, especially with small data.
4. **Combining information** — easily update as new data arrives (sequential).

**Disadvantages:**

1. **Computationally expensive** — exact inference is intractable; MCMC / VI needed.
2. **Prior specification** — subjective and impactful for small data.
3. **Harder to debug** than point estimates.

```python
# PyMC for Bayesian modeling
import pymc as pm
import numpy as np

with pm.Model() as model:
    # Priors
    beta = pm.Normal('beta', mu=0, sigma=1, shape=X.shape[1])
    sigma = pm.HalfNormal('sigma', sigma=1)
    
    # Likelihood
    mu = pm.math.dot(X, beta)
    y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=y)
    
    # Sample posterior
    trace = pm.sample(2000, tune=1000, return_inferencedata=True)

# Posterior summary
import arviz as az
print(az.summary(trace, var_names=['beta']))
```

---

## Q65. Explain conjugate priors. Why do they matter practically? { #q65 }

**Definition.** A prior is **conjugate** to a likelihood if the posterior belongs to the same family as the prior.

**Most useful pairs:**

| Likelihood | Conjugate Prior | Posterior |
|---|---|---|
| Bernoulli / Binomial | Beta | Beta |
| Poisson | Gamma | Gamma |
| Normal (known σ²) | Normal | Normal |
| Normal (unknown σ²) | Normal-Inverse-Gamma | Normal-Inverse-Gamma |
| Multinomial | Dirichlet | Dirichlet |
| Exponential | Gamma | Gamma |

**Why conjugacy matters:**

1. **Closed-form posterior** — no MCMC needed.
2. **Online / sequential updates** — update as data arrives, just increment sufficient statistics.
3. **Interpretable prior strength** — prior hyperparameters have meanings like "pseudo-counts."

**Example: Beta-Binomial.**

Prior: `θ ~ Beta(α, β)`. Likelihood: `X ~ Binomial(n, θ)` with `s` successes.

Posterior: `θ | X ~ Beta(α + s, β + n - s)`.

**Thompson sampling in A/B testing** uses exactly this:

```python
import numpy as np

# Track successes and failures per arm
successes = [10, 8]
failures = [20, 22]

# Sample from each arm's posterior Beta
samples = [np.random.beta(1 + s, 1 + f) for s, f in zip(successes, failures)]

# Pull the arm with highest sampled value
chosen_arm = np.argmax(samples)
```

<div class="tip-box" markdown>
**Senior signal:** "Conjugacy isn't a mathematical curiosity — it's how real A/B testing, bandit algorithms, and many streaming recommender systems operate in production. You get Bayesian inference at zero extra compute."
</div>
