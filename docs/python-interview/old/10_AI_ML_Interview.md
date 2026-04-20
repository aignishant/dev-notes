# 10 — AI/ML Interview Questions
## For Python Developers & AI Enthusiasts

---

## 10.1 Machine Learning Fundamentals

### Q1: Explain bias-variance tradeoff.

**Answer:**
- **Bias:** Error from oversimplified assumptions → underfitting (model too simple)
- **Variance:** Error from sensitivity to training data fluctuations → overfitting (model too complex)
- **Goal:** Find the sweet spot — low bias AND low variance

```python
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

# High bias (underfitting) — too simple
linear = LinearRegression()
scores = cross_val_score(linear, X, y, cv=5, scoring='r2')
print(f"Linear R²: {scores.mean():.3f}")  # Low train AND test score

# High variance (overfitting) — too complex
deep_tree = DecisionTreeRegressor(max_depth=None)
scores = cross_val_score(deep_tree, X, y, cv=5, scoring='r2')
print(f"Deep Tree R²: {scores.mean():.3f}")  # High train, low test score

# Balanced — regularized model
rf = RandomForestRegressor(n_estimators=100, max_depth=10)
scores = cross_val_score(rf, X, y, cv=5, scoring='r2')
print(f"RF R²: {scores.mean():.3f}")  # Good train AND test score
```

---

### Q2: Explain common ML algorithms and when to use them.

**Answer:**

```python
"""
┌─────────────────────┬──────────────────────────────┬───────────────────────┐
│ Algorithm           │ Best For                     │ Key Parameters        │
├─────────────────────┼──────────────────────────────┼───────────────────────┤
│ Linear Regression   │ Continuous target, linear    │ regularization (α)    │
│ Logistic Regression │ Binary classification        │ C (inverse reg)       │
│ Decision Tree       │ Interpretable models         │ max_depth, min_samples│
│ Random Forest       │ General-purpose, tabular     │ n_estimators, depth   │
│ XGBoost/LightGBM    │ Competitions, tabular data   │ learning_rate, depth  │
│ SVM                 │ High-dim, clear margins      │ C, kernel, gamma      │
│ KNN                 │ Small datasets, baselines    │ k, distance metric    │
│ K-Means             │ Unsupervised clustering      │ k, init method        │
│ Neural Networks     │ Complex patterns, unstructured│ architecture, lr      │
└─────────────────────┴──────────────────────────────┴───────────────────────┘
"""

# Complete ML pipeline example
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# 1. Data splitting
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 2. Pipeline (preprocessing + model)
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', RandomForestClassifier(random_state=42))
])

# 3. Hyperparameter tuning
param_grid = {
    'clf__n_estimators': [100, 200, 500],
    'clf__max_depth': [5, 10, 20, None],
    'clf__min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(
    pipeline, param_grid, cv=5, scoring='f1_weighted', n_jobs=-1
)
grid_search.fit(X_train, y_train)

# 4. Evaluation
print(f"Best params: {grid_search.best_params_}")
y_pred = grid_search.predict(X_test)
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
```

---

### Q3: What metrics do you use for classification vs regression?

**Answer:**

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error, r2_score
)

"""
CLASSIFICATION METRICS:
  Accuracy:   Correct predictions / Total (misleading for imbalanced data)
  Precision:  TP / (TP + FP) — "Of predicted positives, how many are correct?"
  Recall:     TP / (TP + FN) — "Of actual positives, how many did we find?"
  F1-Score:   Harmonic mean of precision & recall
  AUC-ROC:    Area under ROC curve (ranking quality)

  When to use what:
    - Balanced classes → Accuracy, F1
    - Spam detection  → Precision (minimize false positives)
    - Cancer detection → Recall (minimize false negatives)
    - Imbalanced      → F1, AUC-ROC

REGRESSION METRICS:
  MAE:    Mean Absolute Error (robust to outliers)
  MSE:    Mean Squared Error (penalizes large errors)
  RMSE:   √MSE (same unit as target)
  R²:     Proportion of variance explained (0 to 1)
  MAPE:   Mean Absolute Percentage Error (relative)
"""

# Example
print(f"Accuracy:  {accuracy_score(y_true, y_pred):.3f}")
print(f"Precision: {precision_score(y_true, y_pred, average='weighted'):.3f}")
print(f"Recall:    {recall_score(y_true, y_pred, average='weighted'):.3f}")
print(f"F1:        {f1_score(y_true, y_pred, average='weighted'):.3f}")
```

---

### Q4: Explain cross-validation and why it matters.

**Answer:**

```python
from sklearn.model_selection import (
    KFold, StratifiedKFold, cross_val_score, TimeSeriesSplit
)

# K-Fold — standard
kfold = KFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=kfold, scoring='accuracy')
print(f"Accuracy: {scores.mean():.3f} ± {scores.std():.3f}")

# StratifiedKFold — preserves class distribution (for imbalanced data)
strat_kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# TimeSeriesSplit — for temporal data (no future data leakage)
tscv = TimeSeriesSplit(n_splits=5)
# Split 1: train=[0,1], test=[2]
# Split 2: train=[0,1,2], test=[3]
# Split 3: train=[0,1,2,3], test=[4]

"""
Why cross-validation matters:
  - Single train/test split is unreliable (depends on how data was split)
  - CV gives confidence interval for model performance
  - Detects overfitting: high train score + low CV score = overfitting
  - More reliable hyperparameter selection
"""
```

---

## 10.2 Deep Learning

### Q5: Explain neural network fundamentals.

**Answer:**

```python
import torch
import torch.nn as nn
import torch.optim as optim

"""
Key Concepts:
  - Forward propagation: Input → layers → output
  - Loss function: Measures prediction error
  - Backpropagation: Compute gradients of loss w.r.t. weights
  - Gradient descent: Update weights to minimize loss
  - Activation functions: ReLU, Sigmoid, Tanh, Softmax
  - Regularization: Dropout, BatchNorm, L2, early stopping
"""

# PyTorch neural network
class SimpleClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, output_dim),
        )

    def forward(self, x):
        return self.network(x)

# Training loop
model = SimpleClassifier(input_dim=784, hidden_dim=256, output_dim=10)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

for epoch in range(num_epochs):
    model.train()
    for batch_X, batch_y in train_loader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()             # Compute gradients
        optimizer.step()            # Update weights

    # Validation
    model.eval()
    with torch.no_grad():
        val_loss = sum(criterion(model(X), y) for X, y in val_loader)
```

---

## 10.3 NLP & Transformers

### Q6: Explain Transformers and modern NLP.

**Answer:**

```python
"""
Transformer Architecture:
  - Self-Attention: Each token attends to all other tokens
  - Multi-Head Attention: Multiple attention heads capture different patterns
  - Positional Encoding: Adds position information (no recurrence)
  - Feed-Forward Network: Applied to each position independently

  Attention(Q, K, V) = softmax(QK^T / √d_k) × V

Key Models:
  BERT:  Encoder-only, bidirectional, good for classification/NER
  GPT:   Decoder-only, autoregressive, good for generation
  T5:    Encoder-decoder, text-to-text, versatile

Hugging Face Usage:
"""

from transformers import pipeline, AutoTokenizer, AutoModel

# 1. Easy: Pipeline API
classifier = pipeline("sentiment-analysis")
result = classifier("I love this product!")
print(result)  # [{'label': 'POSITIVE', 'score': 0.9998}]

# Zero-shot classification
classifier = pipeline("zero-shot-classification")
result = classifier(
    "This new smartphone has amazing battery life",
    candidate_labels=["technology", "sports", "politics"]
)
print(result["labels"][0])  # "technology"

# 2. Advanced: Using models directly
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")

inputs = tokenizer("Hello world!", return_tensors="pt", padding=True)
outputs = model(**inputs)
embeddings = outputs.last_hidden_state  # [batch, seq_len, hidden_dim]

# 3. Text embeddings for semantic search
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["Hello world", "Hi there"])
similarity = embeddings[0] @ embeddings[1]  # Cosine similarity
```

---

## 10.4 LLMs, RAG & AI Engineering

### Q7: Explain RAG (Retrieval-Augmented Generation).

**Answer:**

```python
"""
RAG Architecture:
  User Query → Embedding → Vector Search → Context + Query → LLM → Response

  1. Indexing: Chunk documents → embed → store in vector DB
  2. Retrieval: Embed query → find similar chunks → return top-K
  3. Generation: Combine retrieved context + query → LLM generates answer

Why RAG?
  - Reduces hallucinations (grounded in real data)
  - No expensive fine-tuning needed
  - Data stays up-to-date (just re-index)
  - Domain-specific answers without retraining
"""

# RAG implementation sketch
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 1. Load and chunk documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " "]
)
chunks = text_splitter.split_documents(documents)

# 2. Create embeddings and vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 3. Create RAG chain
llm = ChatOpenAI(model="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

# 4. Query
result = qa_chain({"query": "What is the refund policy?"})
print(result["result"])
"""
```

---

### Q8: Explain fine-tuning vs prompt engineering vs RAG.

**Answer:**

```
┌─────────────────────┬───────────────────┬──────────────────┬──────────────────┐
│                     │ Prompt Engineering│ RAG              │ Fine-tuning      │
├─────────────────────┼───────────────────┼──────────────────┼──────────────────┤
│ Cost                │ Very Low          │ Low-Medium       │ High             │
│ Implementation time │ Hours             │ Days             │ Weeks            │
│ Data needed         │ None              │ Documents        │ Labeled examples │
│ Customization       │ Behavior/format   │ Knowledge        │ Deep behavior    │
│ Latency             │ Low               │ Medium           │ Low              │
│ Best for            │ Quick adaptations │ Domain knowledge │ Specialized tasks│
│ Hallucination risk  │ Medium            │ Low (grounded)   │ Medium           │
│ Data freshness      │ N/A               │ Real-time        │ Training-time    │
└─────────────────────┴───────────────────┴──────────────────┴──────────────────┘

Decision Framework:
  1. Start with prompt engineering (few-shot, chain-of-thought)
  2. If model lacks domain knowledge → add RAG
  3. If model needs to learn new behavior/style → fine-tune
  4. Combine all three for best results
```

---

### Q9: Explain AI Agents and tool use.

**Answer:**

```python
"""
AI Agent Architecture:
  User Request → LLM (reasoning) → Tool Selection → Tool Execution → Response

Components:
  - LLM Core: Reasoning engine (GPT-4, Claude)
  - Tools: Functions the agent can call (search, code execution, APIs)
  - Memory: Conversation history, retrieved context
  - Planning: Break complex tasks into steps

Agent Frameworks:
  - LangChain: Popular, comprehensive
  - LlamaIndex: Data-focused, great for RAG
  - CrewAI: Multi-agent collaboration
  - AutoGen: Microsoft's multi-agent framework
"""

# Tool use example with function calling
"""
import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}]
)

# Agent will respond with tool_use block if it wants to call a tool
for block in response.content:
    if block.type == "tool_use":
        tool_name = block.name      # "get_weather"
        tool_input = block.input    # {"location": "Tokyo"}
        # Execute the tool and send result back
"""
```

---

### Q10: Explain vector databases and embeddings.

**Answer:**

```python
"""
Embeddings: Dense vector representations of text/images
  - Similar items have similar vectors (close in vector space)
  - Dimension: 256 to 4096 (model-dependent)
  - Distance metrics: Cosine similarity, Euclidean, Dot product

Vector Databases:
  - Pinecone: Managed, easy to use
  - Chroma: Lightweight, good for prototyping
  - Weaviate: Feature-rich, hybrid search
  - Milvus: High performance, open source
  - pgvector: PostgreSQL extension (familiar for SQL users)

Indexing Algorithms:
  - HNSW: Hierarchical Navigable Small World (most popular)
  - IVF: Inverted File Index (good for large datasets)
  - PQ: Product Quantization (memory-efficient)
"""

# Example with ChromaDB
"""
import chromadb
from chromadb.utils import embedding_functions

# Setup
client = chromadb.Client()
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.create_collection("docs", embedding_function=ef)

# Add documents
collection.add(
    documents=["Python is great", "Java is popular", "ML uses Python"],
    ids=["doc1", "doc2", "doc3"],
    metadatas=[{"topic": "python"}, {"topic": "java"}, {"topic": "ml"}]
)

# Query — finds semantically similar documents
results = collection.query(
    query_texts=["programming languages for data science"],
    n_results=2,
    where={"topic": {"$in": ["python", "ml"]}}
)
print(results["documents"])
"""
```

---
