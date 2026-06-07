---
title: Building RAG Systems That Actually Work in Production
date: 2025-06-01
category: AI Engineering
tags: [RAG, LLM, Production]
excerpt: Most RAG demos look great in notebooks. Here's what breaks in production and how we fix it.
readTime: 8 min
---

Most RAG demos look great in a Jupyter notebook. You load a few PDFs, chunk them naively, embed with OpenAI, store in Chroma, ask a question — and it works. You ship it. Three weeks later your users are getting confidently wrong answers and you don't know why.

Here's what actually goes wrong, and how we fix it.

## The Five Failure Modes

### 1. Naive Chunking Destroys Context

Fixed-size chunking (e.g. 512 tokens, no overlap) splits sentences mid-thought and severs the relationship between a header and its content. A regulation that says "this rule applies *except* in the case of..." gets split right at "except".

**What we do instead:**
- Use recursive character splitting with 20% overlap
- Respect semantic boundaries (paragraphs, headers) using structural chunking
- For tabular data, keep entire rows together — never split a table

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

### 2. Pure Vector Search Misses Exact Matches

Semantic similarity is powerful for conceptual queries ("what is the policy on X") but fails for exact lookups ("what is Article 17(3)(b)"). Users searching for specific codes, names, or numbers will get poor results from vector-only retrieval.

**Solution: Hybrid search**

Combine dense vector search with sparse BM25, then fuse rankings:

```python
# Pseudo-code — works with Weaviate, Elasticsearch, or Qdrant
results = hybrid_search(
    query=user_query,
    dense_weight=0.7,
    sparse_weight=0.3,
    top_k=20
)
```

### 3. The Top-K Results Aren't the Most Relevant

Retrieving the top 20 chunks and passing all of them to the LLM is wasteful and degrades answer quality. Not all top-20 chunks are equally relevant — position 12 might be more relevant than position 2.

**Solution: Re-ranking**

Add a cross-encoder re-ranker (Cohere or a local BAAI/bge-reranker) after initial retrieval:

```python
from cohere import Client

co = Client(api_key)
reranked = co.rerank(
    query=user_query,
    documents=[c.page_content for c in candidates],
    top_n=5,
    model="rerank-english-v3.0"
)
```

This typically improves answer quality by 15–30% with minimal latency overhead.

### 4. No Evaluation Loop

Most teams ship RAG without any systematic evaluation. You can't improve what you don't measure.

**Minimum viable eval stack:**

| Metric | Tool | What it measures |
|--------|------|-----------------|
| Context Recall | RAGAs | Are the right chunks being retrieved? |
| Faithfulness | RAGAs | Is the answer grounded in the context? |
| Answer Relevance | RAGAs | Does the answer address the question? |
| Latency | Custom | P50/P95 end-to-end response time |

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

results = evaluate(
    dataset=your_eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_recall]
)
```

Build a golden dataset of 50–100 question/answer pairs from your domain experts. Run evals on every significant change to your pipeline.

### 5. Missing Metadata and Filtering

Storing chunks without metadata means you can't filter by date, source, document type, or access level. A user asking about "the 2024 policy" shouldn't get results from 2019.

**Always store metadata alongside vectors:**

```python
documents = [
    Document(
        page_content=chunk,
        metadata={
            "source": doc_name,
            "date": doc_date,
            "section": section_title,
            "doc_type": "regulation"
        }
    )
    for chunk in chunks
]
```

## The Production Architecture We Use

```
User Query
    │
    ├─► Query Rewriting (HyDE or multi-query)
    │
    ├─► Hybrid Retrieval (dense + sparse, top-20)
    │
    ├─► Re-ranking (cross-encoder, top-5)
    │
    ├─► Context Assembly (with source attribution)
    │
    └─► LLM Generation (with citation enforcement)
```

> **Key insight:** The retrieval step matters more than the generation model. A GPT-3.5 with excellent retrieval beats GPT-4 with poor retrieval every time. Invest in your retrieval pipeline first.

## What to Do This Week

1. **Audit your chunks** — visualise 50 random chunks. Do they make sense in isolation?
2. **Add BM25** — if you're not doing hybrid search, add it. It's a one-day change with significant upside.
3. **Add one eval metric** — faithfulness from RAGAs takes 30 minutes to set up and immediately tells you if your LLM is hallucinating.

The difference between a RAG prototype and a RAG product is systematic measurement and the willingness to fix boring infrastructure problems.

---

*Questions about your RAG architecture? We'd love to hear what you're building — [hello@danalytica.com](mailto:hello@danalytica.com)*
