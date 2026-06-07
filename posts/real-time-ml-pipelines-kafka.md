---
title: Real-Time ML Pipelines with Kafka and River
date: 2025-05-18
category: Data Engineering
tags: [Kafka, Streaming, MLOps]
excerpt: How we process 15k+ events per minute with sub-100ms latency for fraud detection.
readTime: 6 min
---

When a payment fraud model takes 2 seconds to respond, it's useless. Fraud either happens in milliseconds or it doesn't get caught. Here's how we built a real-time ML pipeline that classifies 15,000+ transactions per minute with P99 latency under 80ms — and adapts to new fraud patterns without retraining.

## The Problem With Batch ML

Most ML systems work in batch: collect data, retrain weekly, deploy, repeat. For fraud detection this is catastrophic. Fraudsters adapt within hours. A model trained on last week's data is already stale.

You need two things batch ML can't provide:
1. **Sub-second inference** at the moment of the transaction
2. **Online learning** — the model updates as it sees new data

## Architecture Overview

```
Payment Events
    │
    ▼
Kafka Topic: raw-transactions
    │
    ▼
Stream Processor (Faust)
  ├─ Feature extraction
  ├─ Enrichment (device fingerprint, velocity)
  └─ Normalisation
    │
    ▼
Kafka Topic: enriched-transactions
    │
    ▼
ML Inference Service
  ├─ River online model (XGBoost + LR ensemble)
  ├─ Redis feature store (30-day rolling windows)
  └─ Prediction + confidence score
    │
    ▼
Kafka Topic: fraud-scores
    │
    ├─► Decision engine (block / review / allow)
    └─► Feedback loop (labelled outcomes → model update)
```

## Why River for Online Learning

[River](https://riverml.xyz) is the Python library for online machine learning. Unlike scikit-learn models that require the full dataset to train, River models update incrementally with each new sample:

```python
from river import compose, linear_model, preprocessing, ensemble

model = compose.Pipeline(
    preprocessing.StandardScaler(),
    ensemble.AdaptiveRandomForest(n_models=10)
)

# Update with each incoming transaction
model.learn_one(features, label)

# Predict without storing any data
score = model.predict_proba_one(features)
```

The model never sees the same data twice and requires no retraining cycle. Memory footprint is constant regardless of how many transactions you've processed.

## Feature Engineering in a Stream

The hardest part of real-time ML is features that require history. You can't compute "transactions in last 30 minutes" without storing state somewhere.

We use Redis for rolling window aggregations:

```python
import redis
from datetime import datetime

r = redis.Redis()

def get_velocity_features(card_id: str, amount: float) -> dict:
    now = int(datetime.utcnow().timestamp())
    window_1h  = now - 3600
    window_24h = now - 86400

    # Sorted set: {transaction_id: timestamp}
    key = f"velocity:{card_id}"

    # Add current transaction
    r.zadd(key, {f"tx:{now}": now})
    r.expire(key, 86400 * 30)  # 30-day TTL

    # Count in windows
    count_1h  = r.zcount(key, window_1h, now)
    count_24h = r.zcount(key, window_24h, now)

    return {
        "tx_count_1h":  count_1h,
        "tx_count_24h": count_24h,
        "amount_vs_avg": amount / (get_avg_amount(card_id) or amount)
    }
```

## The Feedback Loop

Online learning is only as good as its labels. We close the feedback loop by:

1. **Immediate signals**: declined transactions, 3DS challenges triggered
2. **Delayed labels**: chargebacks (arrive 30–90 days later) piped back via Kafka
3. **Weak labels**: rule-based flags used as noisy supervision

```python
# Consumer for labelled outcomes
@app.agent(fraud_outcomes_topic)
async def process_outcome(outcomes):
    async for outcome in outcomes:
        features = await get_stored_features(outcome.transaction_id)
        if features:
            model.learn_one(features, outcome.is_fraud)
```

## Results

After 90 days in production on a mid-size payments processor:

| Metric | Before (batch) | After (streaming) |
|--------|---------------|-------------------|
| P99 Latency | 1,800ms | 78ms |
| Precision | 91.3% | 94.2% |
| False Positive Rate | 0.8% | 0.28% |
| Model staleness | 7 days | Real-time |

The false positive reduction was the biggest win commercially — fewer legitimate transactions being declined means fewer angry customers and lost revenue.

## Lessons Learned

**Don't start with the ML.** Get your Kafka pipeline working first, log everything, and validate your feature engineering with a simple threshold model before you add River. The streaming infrastructure is 80% of the work.

**Redis TTLs are load-bearing.** We had a production incident where a Redis instance ran out of memory because someone removed the TTL from the velocity keys. Every key needs a TTL.

**Monitor concept drift, not just accuracy.** Accuracy stays high right up until fraudsters discover your model's blind spots. Track the distribution of your features over time and alert when it shifts.

---

*Building a real-time ML system? We've shipped several in production — [get in touch](mailto:hello@danalytica.com).*
