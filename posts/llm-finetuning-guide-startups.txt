---
title: When to Fine-Tune an LLM (And When Not To)
date: 2025-05-05
category: AI Strategy
tags: [LLM, Fine-tuning, Strategy]
excerpt: A practical decision framework for startups — prompt engineering vs. RAG vs. fine-tuning.
readTime: 7 min
---

Every week a startup founder asks us: "Should we fine-tune our own model?" Usually the answer is no. Here's the decision framework we use to figure out when it makes sense.

## The Three Options

Before committing to fine-tuning, understand what you're choosing between:

| Approach | Cost | Time to ship | Best for |
|----------|------|-------------|---------|
| Prompt engineering | $ | Days | Style, tone, formatting |
| RAG | $$ | Weeks | Domain knowledge, up-to-date facts |
| Fine-tuning | $$$  | Months | Behaviour, latency, cost at scale |

Most teams reach for fine-tuning when they actually need RAG. Most teams reach for RAG when they actually need better prompts.

## When Prompt Engineering Is Enough

Try prompting first. You'd be surprised how far you can get.

Prompting handles:
- **Tone and format**: "Always respond as a concise technical advisor. Use bullet points."
- **Task framing**: Few-shot examples covering your most common cases
- **Constraint enforcement**: "Never mention competitor products."
- **Chain-of-thought**: "Think step by step before giving your final answer."

Before spending a month on fine-tuning, spend two days on prompt engineering with structured outputs (JSON mode, function calling) and systematic evaluation.

> **Rule of thumb**: If you can describe the behaviour you want in a paragraph, prompting will get you 80% of the way there.

## When You Need RAG Instead

Fine-tuning cannot teach a model facts it didn't see during training — and even if it could, the facts would be static. RAG is the right choice when:

- You have a **proprietary knowledge base** (documents, policies, product data)
- Your information **changes frequently** (prices, regulations, inventory)
- You need **source attribution** ("According to document X...")
- You want **verifiability** (the answer traces back to a specific chunk)

Fine-tuning a model on your documentation is almost always the wrong move. The model will hallucinate confidently because it has "learned" the domain without actually having access to the source documents at inference time.

## When Fine-Tuning Actually Makes Sense

Fine-tuning earns its cost when:

### 1. You have a very specific output format or behaviour
If your application always needs to output a particular JSON schema, SQL dialect, or domain-specific language, fine-tuning can bake this in more reliably than prompting — and with shorter prompts.

```
# Before fine-tuning: 800-token system prompt to get consistent output
# After fine-tuning: 50-token prompt, same reliability
```

### 2. Latency and cost matter at scale
A fine-tuned 7B model can match GPT-4 quality on a narrow task while running at 10x lower cost and 3x lower latency. If you're processing millions of items, this compounds fast.

Rough cost comparison for 10M tokens/day:

| Model | Cost/1M tokens | Daily cost |
|-------|---------------|-----------|
| GPT-4o | $5 | $50,000 |
| GPT-4o-mini | $0.15 | $1,500 |
| Fine-tuned Llama 3.1 8B (self-hosted) | ~$0.04 | $400 |

### 3. Data privacy requires on-premise deployment
If you cannot send data to third-party APIs (healthcare, finance, defence), you need a self-hosted model. Fine-tuning is often part of that story.

### 4. You have thousands of high-quality labelled examples
Fine-tuning needs data. Not just any data — *labelled, high-quality, diverse examples* of the exact task. If you have fewer than ~500 examples, you probably don't have enough. If your examples aren't consistently high quality, fine-tuning will bake in the noise.

## The Decision Tree

```
Do prompts + RAG already give acceptable results?
  │
  YES → Ship it. Re-evaluate in 3 months.
  │
  NO
  │
  Is the problem a lack of knowledge/facts?
    │
    YES → Build RAG. Fine-tuning won't help.
    │
    NO
    │
    Is the problem latency, cost, or output format?
      │
      YES → Fine-tuning is worth evaluating.
      │
      NO → Improve your prompts and eval dataset first.
```

## What Fine-Tuning Actually Costs

People consistently underestimate this. Budget for:

- **Data collection and cleaning**: Usually 60–70% of total effort
- **Baseline evaluation**: You need to know what you're improving on
- **Training runs**: Multiple experiments, hyperparameter sweeps
- **Serving infrastructure**: You now own a model to deploy and maintain
- **Ongoing retraining**: Models drift; you'll need to retrain as your data evolves

For a serious fine-tuning project on a 7–13B model: expect 2–3 months of engineering time and $5,000–$20,000 in compute costs for the first version.

## Our Recommendation for Most Startups

1. **Start with GPT-4o-mini + good prompts** — fast, cheap to iterate, good enough for most tasks
2. **Add RAG** when you need domain knowledge or current facts
3. **Consider fine-tuning only when** you've validated the product and have >1000 quality examples

The goal is to ship something users value, not to build the most technically impressive AI pipeline.

---

*Not sure which approach fits your use case? A 45-minute call with our team is free — [hello@danalytica.com](mailto:hello@danalytica.com)*
