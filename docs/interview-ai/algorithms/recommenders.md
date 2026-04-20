# Module 7 — Recommender Systems

Fifteen questions on the algorithms powering Netflix, Spotify, Amazon, YouTube, TikTok. Recommenders are the single largest deployed application of classical ML, and every interview touches them if you're applying to a consumer internet role.

---

## Q111. What are the main approaches to recommendation? { #q111 }

Four families:

**1. Content-based filtering:** Recommend items similar to what the user has liked, based on item *features* (genre, tags, text description).

Pros: No cold-start for new items (features are known).
Cons: Filter bubble — only recommends similar content. Needs good features.

**2. Collaborative filtering (CF):** Recommend based on patterns across users. "Users who liked X also liked Y."

Variants: user-user CF, item-item CF, matrix factorization.

Pros: Captures latent taste patterns. No feature engineering.
Cons: Cold start for new users/items. Sparse interaction matrix.

**3. Hybrid:** Combine content + CF.

**4. Knowledge-based / rule-based:** Uses domain rules ("if user searched 'red dress', show red dresses").

**Modern production systems** stack multiple approaches:

- **Retrieval stage:** Fast candidate generation from millions of items (embedding nearest neighbor, two-tower).
- **Ranking stage:** Precise scoring of candidates (GBDT, deep ranker).
- **Re-ranking:** Diversity, freshness, business rules.

---

## Q112. Content-based recommendation: walk through the implementation. { #q112 }

**Setup:** Items have feature vectors (TF-IDF of descriptions, genre one-hots, etc.). Users have interaction history.

**1. Build item features:**

```python
from sklearn.feature_extraction.text import TfidfVectorizer

tfidf = TfidfVectorizer(max_features=5000)
item_features = tfidf.fit_transform(items['description'])
```

**2. Build user profile as weighted average of liked items:**

```python
import numpy as np

def user_profile(user_likes, item_features):
    # user_likes: list of item IDs
    # item_features: sparse matrix, rows = items
    return item_features[user_likes].mean(axis=0)

profile = user_profile(user.liked_items, item_features)
```

**3. Score candidates by cosine similarity:**

```python
from sklearn.metrics.pairwise import cosine_similarity

scores = cosine_similarity(profile, item_features).ravel()
top_k_ids = np.argsort(scores)[::-1][:20]
```

**Strengths:**

- Cold start for new items (just compute features).
- Explainable: "we recommend because you liked X with similar genre."

**Weaknesses:**

- Filter bubble: never discovers surprising content.
- Requires good features — hard for items like music where mood > genre.
- Overspecialization: user gets stuck in their current taste.

**Production hack:** Mix content-based and popularity-based results to break filter bubbles.

---

## Q113. User-user vs item-item collaborative filtering. { #q113 }

**User-user CF:**

1. Find users similar to the target user (by cosine sim of rating vectors).
2. Predict target's rating for item $i$ as weighted average of similar users' ratings for $i$.

$$
\hat{r}_{ui} = \bar{r}_u + \frac{\sum_{v \in N(u)} \text{sim}(u, v) (r_{vi} - \bar{r}_v)}{\sum_{v \in N(u)} |\text{sim}(u, v)|}
$$

**Item-item CF:**

1. Find items similar to those the user has rated (by cosine sim of column vectors).
2. Predict target's rating for item $i$ as weighted average of user's ratings on similar items.

$$
\hat{r}_{ui} = \frac{\sum_{j \in N(i)} \text{sim}(i, j) \cdot r_{uj}}{\sum_{j \in N(i)} |\text{sim}(i, j)|}
$$

**Why item-item usually wins in practice:**

- Items change less often than user preferences → item-item similarities are more stable.
- Can **precompute** item-item similarity matrix; cheap to serve.
- **Explainable:** "recommended because you watched The Matrix; 78% of Matrix watchers liked this."
- **Amazon's famous system** (2003 paper) is item-item CF.

**Cold start failure mode:** Both struggle with new users (no history) and new items (no ratings). Solutions: hybridize with content, use popularity prior, bootstrap from signup survey.

---

## Q114. Explain matrix factorization with SGD step by step. { #q114 }

**Objective:** For observed ratings $(u, i, r_{ui})$:

$$
\min_{P, Q} \sum_{(u, i) \in R} (r_{ui} - p_u^\top q_i)^2 + \lambda (\|p_u\|^2 + \|q_i\|^2)
$$

**SGD update for a single observed rating:**

1. Prediction: $\hat{r}_{ui} = p_u^\top q_i$.
2. Error: $e_{ui} = r_{ui} - \hat{r}_{ui}$.
3. Update:
   $$
   p_u \leftarrow p_u + \eta (e_{ui} q_i - \lambda p_u)
   $$
   $$
   q_i \leftarrow q_i + \eta (e_{ui} p_u - \lambda q_i)
   $$

Loop through all observed ratings per epoch.

```python
import numpy as np

def mf_sgd(ratings, n_users, n_items, k=10, lr=0.01, reg=0.02, epochs=20):
    P = np.random.normal(0, 0.1, (n_users, k))
    Q = np.random.normal(0, 0.1, (n_items, k))
    for _ in range(epochs):
        for u, i, r in ratings:
            pred = P[u] @ Q[i]
            err = r - pred
            P[u] += lr * (err * Q[i] - reg * P[u])
            Q[i] += lr * (err * P[u] - reg * Q[i])
    return P, Q
```

**With biases:**

$$
\hat{r}_{ui} = \mu + b_u + b_i + p_u^\top q_i
$$

Add update rules for $b_u, b_i$. In practice, biases explain a surprisingly large fraction of variance — some users rate everything high; some items are generally well-liked.

---

## Q115. ALS vs SGD for matrix factorization. When to use each? { #q115 }

**Alternating Least Squares (ALS):**

Fix $Q$, solve for $P$ (closed-form, treating it as a ridge regression per user). Fix $P$, solve for $Q$ similarly. Alternate.

For user $u$:

$$
p_u = (Q_I^\top Q_I + \lambda I)^{-1} Q_I^\top r_u
$$

where $Q_I$ are rows of $Q$ for items $u$ has rated.

**SGD:** Update one example at a time with gradient.

**Comparison:**

| Property | SGD | ALS |
|---|---|---|
| **Convergence** | Needs LR tuning | Guaranteed each step |
| **Parallelization** | Hard (updates are sequential per row) | Easy (each user/item is independent) |
| **Large sparse data** | Good | Better — closed form per user/item |
| **Implicit feedback** | Needs tricks | Native via weighted ALS |
| **Memory** | Low | Needs $Q^\top Q$ and per-user solve |
| **Library support** | Surprise, PyTorch | Spark MLlib, `implicit` library |

**Rule of thumb:**

- **Spark / distributed** → ALS.
- **Small/medium data with streaming updates** → SGD.
- **Implicit feedback (clicks, views)** → ALS with confidence weighting.

```python
# Spark ALS
from pyspark.ml.recommendation import ALS
als = ALS(
    rank=20, maxIter=10, regParam=0.1,
    userCol="user", itemCol="item", ratingCol="rating",
    coldStartStrategy="drop"
).fit(train)

# implicit library
import implicit
model = implicit.als.AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)
model.fit(user_item_sparse)
```

---

## Q116. Explicit vs implicit feedback. How do recommender approaches differ? { #q116 }

**Explicit feedback:** User rates or says explicitly (5-star reviews, thumbs up/down).

**Implicit feedback:** Inferred from behavior (clicks, views, watch time, purchases). No negative signal — absence of interaction is ambiguous (didn't see it? or saw and disliked?).

**Implicit feedback is vastly more common in production.** YouTube doesn't have star ratings — it has watch time.

**Key differences for modeling:**

| Aspect | Explicit | Implicit |
|---|---|---|
| Signal | Clean rating | Clicks/dwell, no negatives |
| Missing data | Missing at random | Missing because not shown |
| Objective | Predict rating (RMSE) | Predict interaction prob (ranking) |
| Confidence | All ratings equally valuable | Confidence weighted by interaction strength |

**Weighted ALS for implicit (Hu, Koren, Volinsky 2008):**

$$
\min \sum_{u, i} c_{ui} (p_{ui} - p_u^\top q_i)^2 + \lambda (\|P\|^2 + \|Q\|^2)
$$

where $p_{ui} = 1$ if interacted else 0, and $c_{ui} = 1 + \alpha \cdot r_{ui}$ weights confidence by how strongly user $u$ interacted with $i$ (e.g., watch duration).

**Bayesian Personalized Ranking (BPR):** Optimizes a pairwise ranking loss. For each observed $(u, i)$, sample a negative $j$ not interacted with. Maximize:

$$
\log \sigma(\hat{r}_{ui} - \hat{r}_{uj})
$$

BPR directly optimizes **ranking** rather than predicting ratings, better aligned with recommendation as a retrieval problem.

---

## Q117. What's the cold start problem, and how do you handle it? { #q117 }

**Cold start:** A new user or item enters the system with no interaction history.

**Three scenarios:**

**1. New user (user cold start):**

- **Onboarding questionnaire:** Ask users to rate a few seed items.
- **Popularity baseline:** Show widely-liked items.
- **Demographics / signup data:** Recommend based on age/location proxies.
- **Implicit signals:** Click patterns in the first session quickly personalize.

**2. New item (item cold start):**

- **Content-based features:** Text, images, metadata → embed and find similar items.
- **Upload time boost:** Amplify new items temporarily to collect interactions.
- **Taxonomy-based:** Place in a category; benefit from category-level behaviors.

**3. New system (no users or items):**

- Start with heuristics (popularity, recency).
- Collect feedback aggressively, initialize CF when data accumulates.

**Two-tower models** handle cold start naturally:

- User tower: embeds user ID + features (demographics, recent activity).
- Item tower: embeds item ID + features (content embeddings, category).
- Similarity is dot product.
- New user/item gets embeddings via features even without interactions.

```python
# Schematic two-tower
class TwoTower(nn.Module):
    def __init__(self):
        super().__init__()
        self.user_tower = nn.Sequential(
            nn.Linear(user_feat_dim, 128), nn.ReLU(),
            nn.Linear(128, 32)
        )
        self.item_tower = nn.Sequential(
            nn.Linear(item_feat_dim, 128), nn.ReLU(),
            nn.Linear(128, 32)
        )
    def forward(self, user, item):
        u = self.user_tower(user)
        i = self.item_tower(item)
        return (u * i).sum(-1)
```

---

## Q118. What are two-tower models? Why are they dominant in production? { #q118 }

**Two-tower architecture:**

- **User tower:** User features → user embedding $u \in \mathbb{R}^d$.
- **Item tower:** Item features → item embedding $v \in \mathbb{R}^d$.
- **Score:** $s(u, v) = u^\top v$ or cosine similarity.

Trained with contrastive loss: positive pairs (actual interactions) should have high similarity; negative pairs (random items) low.

**Why they dominate:**

1. **Scalable retrieval.** Item tower is computed offline for every item. At serving time, you compute user embedding and find nearest item embeddings via ANN (FAISS, HNSW). Billions of items → milliseconds.

2. **Fresh content handling.** New items just need features passed through the item tower.

3. **Features + CF fused.** The embedding spaces encode both content and collaborative signal.

4. **Transfer learning.** Pretrain towers on auxiliary tasks, then fine-tune.

**Architecture typically used:**

- User tower: demographics, history sequence (via Transformer or GRU), current context.
- Item tower: text/image embeddings, categorical features, price, age.

**Training tricks:**

- **In-batch negative sampling:** Other items in the batch serve as negatives (free).
- **Hard negative mining:** Sample semi-popular items user didn't interact with.
- **Sampled softmax / NCE** for the contrastive loss.

**Production examples:** Google search two-tower (paper: "Sampling-Bias-Corrected Neural Modeling"), Facebook EBR, YouTube recommendation retrieval stage.

---

## Q119. How is a recommender deployed? Walk through the architecture. { #q119 }

Modern production recommender:

```
[User request]
      ↓
[Retrieval stage]  ← candidates from multiple sources
      ↓  (fetch ~1000 items from millions)
[Filtering]        ← business rules, eligibility, already-seen
      ↓  (~500 items)
[Ranking stage]    ← deep ranker scores each user-item
      ↓  (scored list)
[Re-ranking]       ← diversity, freshness, MMR
      ↓  (~20 items)
[Serve]
      ↓
[Logging]          ← impressions, clicks, dwell
      ↓
[Offline training] ← hourly/daily retrains
```

**Retrieval:** Multiple retrievers in parallel:

- **Popular/recent** — simple baselines.
- **Content-based** — nearest neighbor in item feature space.
- **Collaborative** — two-tower or MF nearest neighbor.
- **Sequence-based** — items similar to recent user session (SASRec, BERT4Rec).
- **Friend-based** — items liked by social graph.

Union top-k from each → candidate pool.

**Ranking:** LightGBM, XGBoost, or DNN (DLRM, DeepFM, DIN, MMoE for multi-task). Features per candidate:

- User × item interaction features (cosine sim from tower, num past interactions in category).
- Historical CTR, conversion rate of the item.
- Recency, position bias.
- Contextual features (time of day, device).

**Re-ranking:** Diversity (MMR, DPP), fairness, freshness. Sometimes bandit logic.

**Serving latency budget:** Typically <100ms end-to-end.

**Infrastructure:** Redis/Aerospike for feature store, FAISS for vector search, TF Serving or Triton for model inference, Kafka for logging.

---

## Q120. Evaluating recommenders: offline and online metrics. { #q120 }

**Offline metrics** (from historical logs):

| Metric | Measures |
|---|---|
| **Precision@k** | Fraction of top-k that user interacted with |
| **Recall@k** | Fraction of relevant items that are in top-k |
| **MAP (Mean Average Precision)** | Ranks sensitive — rewarding relevant items near top |
| **NDCG@k** | Like MAP but with graded relevance |
| **MRR (Mean Reciprocal Rank)** | 1 / rank of first relevant item |
| **Hit rate@k** | Fraction of users for whom at least one relevant item is in top-k |
| **Diversity / Novelty / Coverage** | Business metrics beyond accuracy |

**NDCG formula:**

$$
\text{DCG}_k = \sum_{i=1}^{k} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}
$$

$$
\text{NDCG}_k = \frac{\text{DCG}_k}{\text{IDCG}_k}
$$

where IDCG is DCG of the ideal ordering.

**Online metrics** (A/B test):

- **CTR** (click-through rate)
- **Conversion rate**
- **Session length / time spent**
- **User retention** (long-term)
- **Revenue per session**

**The offline-online gap:** Offline metrics measure prediction of *past* behavior. They don't measure whether users *discover* items they'd like but haven't seen. Offline improvements frequently don't translate online — always A/B test.

```python
def ndcg_at_k(relevance, k=10):
    relevance = relevance[:k]
    dcg = ((2**relevance - 1) / np.log2(np.arange(2, len(relevance)+2))).sum()
    ideal = sorted(relevance, reverse=True)
    idcg = ((2**np.array(ideal) - 1) / np.log2(np.arange(2, len(ideal)+2))).sum()
    return dcg / idcg if idcg > 0 else 0
```

---

## Q121. Explain the exploration-exploitation tradeoff in recsys. { #q121 }

**Exploitation:** Recommend items you're confident the user will like.

**Exploration:** Recommend items to *learn* more about user preferences.

**Why exploration matters:**

- **Popularity bias:** Pure exploitation only recommends already-popular items → rich-get-richer.
- **Discovery:** Users never see items outside their current cluster.
- **Cold items starve:** New items never get shown, never get feedback, never get recommended.

**Algorithms:**

**1. ε-greedy:** Recommend the top-scoring item with probability $1-\epsilon$; random item with probability $\epsilon$.

Simple but wasteful — random items are often terrible.

**2. UCB (Upper Confidence Bound):**

$$
\text{score}(i) = \hat{\mu}_i + c \sqrt{\frac{\ln t}{n_i}}
$$

Prefer items with high predicted reward OR high uncertainty. Items shown fewer times get an exploration bonus.

**3. Thompson sampling:** Maintain a posterior distribution over each item's reward. Sample from the posterior, act as if the sample were truth. Naturally balances exploration and exploitation.

**4. Contextual bandits (LinUCB, Thompson with linear model):** Extend to personalized recommendations.

**Production pattern:** Most of traffic goes to exploitation (main ranker). A small slice (1–5%) goes to exploration to keep the system learning.

---

## Q122. What's the Netflix Prize "Funk SVD" approach? { #q122 }

Simon Funk's 2006 blog post revolutionized recommender systems and framed the modern matrix factorization approach.

**Setup:** User-movie rating matrix $R$, mostly missing.

**Factorize:** $R \approx P Q^\top$ where $P$ has user factors, $Q$ has movie factors.

**Funk's twist:** Instead of computing SVD of the incomplete matrix (mathematically ill-defined), just *iteratively* learn $P$ and $Q$ via SGD on observed entries only.

Each epoch, for each observed rating:

1. Predict $\hat{r} = \mu + b_u + b_i + p_u^\top q_i$.
2. Compute error.
3. Gradient update $p_u, q_i, b_u, b_i$.

Critical additions in the final Netflix Prize winner:

- **Biases** — global, per-user, per-item.
- **Time dynamics** — user preferences drift; movie popularity shifts.
- **Implicit feedback** (SVD++) — account for which items a user rated, even if rating unknown.
- **Ensembling** — blend hundreds of models (the winning team combined ~100 models).

**Why it matters:** Established that:

1. Simple models with good engineering beat fancy math.
2. Biases often explain more variance than interactions.
3. Ensembles dominate single models.
4. Time-awareness is crucial.

Modern deep recommenders still build on this foundation.

---

## Q123. What is sequence-aware / session-based recommendation? { #q123 }

**Classic CF ignores order:** Watching *The Godfather I* then *II* vs *II* then *I* produces the same user profile.

**Sequence-aware recommenders** treat user history as an ordered sequence, capturing:

- **Recency:** recent interactions matter more.
- **Patterns:** A → B → C sequences.
- **Session intent:** What the user is doing *right now*.

**Approaches:**

**1. GRU4Rec (2016):** GRU over sequence of item IDs. Predict next item.

**2. Self-Attentive Sequential Recommendation (SASRec, 2018):** Transformer decoder over item sequence. Current SOTA for session recsys.

**3. BERT4Rec (2019):** Bidirectional Transformer (MLM-style) — mask random items, predict them.

**4. Caser (2018):** Treat sequence as an "image," use CNN.

**5. Session-based MF:** Simpler baseline — use only the current session's items to predict next.

```python
# SASRec (schematic)
class SASRec(nn.Module):
    def __init__(self, n_items, d=64, heads=4, layers=2):
        super().__init__()
        self.item_emb = nn.Embedding(n_items, d)
        self.pos_emb = nn.Embedding(max_len, d)
        self.layers = nn.ModuleList([
            nn.TransformerDecoderLayer(d, heads) for _ in range(layers)
        ])
    def forward(self, items):
        seq = self.item_emb(items) + self.pos_emb(...)
        for layer in self.layers:
            seq = layer(seq, seq, causal_mask=True)
        return seq @ self.item_emb.weight.T
```

**Use cases:**

- E-commerce sessions ("you just added shoes → show socks").
- News feeds (recent reads signal current interest).
- Music playlists (sequence flow matters).

---

## Q124. Recommender biases: feedback loops and how to break them. { #q124 }

**Core problem:** Recommenders learn from data that *they produced*. Item A got shown → user clicked → A gets recommended more → shown more → clicked more. The system converges to showing what it already shows.

**Specific biases:**

**1. Exposure / selection bias:** You only observe clicks on items you showed. Items you didn't show have no signal. Models think unexplored items are "bad."

Fix: **Inverse propensity scoring (IPS):** Weight each observation by $1/P(\text{shown})$ — upweights rare-exposure items.

**2. Popularity bias:** Popular items get more exposure → more clicks → recommended more.

Fix: Re-rank with diversity constraints; penalize popular items explicitly; boost long-tail.

**3. Position bias:** Top of the list gets more clicks regardless of relevance.

Fix: Include position as a feature during training; randomize positions occasionally to measure true relevance.

**4. Conformity bias:** Users click what others clicked (herding).

Fix: Harder — needs causal inference or RCTs.

**5. Confirmation bias / filter bubble:** Users see what they already like; taste narrows.

Fix: Deliberate diversity injection; exploration bandits.

**6. Survivorship bias:** Only long-surviving users remain. Recent cohorts underrepresented.

Fix: Time-weighted sampling; fresh-user evaluation.

```python
# IPS-weighted training
weights = 1 / (propensity + 1e-6)
loss = (weights * per_sample_loss).mean()
```

---

## Q125. Scenario: design a recommendation system for a new e-commerce site. { #q125 }

**Step 1 — Clarify:**

- What's the catalog size? (1K, 1M, 100M?)
- User base size and growth?
- Types of items (few categories vs millions of SKUs)?
- Business goal (CTR? GMV? session length?)
- Latency budget (real-time browsing vs email digest)?

**Step 2 — Phased rollout:**

**Phase 1 (MVP, weeks 1–4):**

- Popularity-based recommendations (trending, bestsellers).
- Category-based filtering.
- "Customers also bought" via item-item co-occurrence.
- Track impressions, clicks, purchases — build the training log.

**Phase 2 (months 2–3):**

- Add item-item CF using ALS on implicit feedback.
- Add content-based similarity using item descriptions + images.
- Hybrid: weighted blend of popularity + CF + content.
- A/B test: hybrid vs popularity-only.

**Phase 3 (months 4+):**

- Two-tower neural retrieval for scale.
- LightGBM ranker on top (user × item features).
- Session-aware models (SASRec) for browsing.
- Multi-objective (CTR + CVR + revenue).

**Phase 4 (ongoing):**

- Bandits for exploration.
- Cold-start handling with content tower.
- Fairness / diversity re-ranking.

**Key metrics throughout:**

- Offline: NDCG@10, MAP, coverage.
- Online: CTR, CVR, GMV per session, diversity, new-item exposure.

**Pitfalls to avoid:**

- Starting with a neural model (too complex for Phase 1).
- Evaluating only on CTR (ignoring long-tail discovery).
- Ignoring position bias in logs.
- Not setting up A/B testing infrastructure early.

<div class="tip-box" markdown>
**Interviewer signal:** The best candidates talk about **phased rollout**, **logging infrastructure**, and **metrics beyond CTR**. The average candidate jumps straight to deep learning. Show you understand that simple baselines, proper evaluation, and fast iteration matter more than fancy architectures for a 0-to-1 system.
</div>
