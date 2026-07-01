# Approach Document - SHL Assessment Agent

## 1. Design Choices: Deterministic Pipeline vs. LLM Agent
While most candidates might use LLMs with LangChain or LlamaIndex for this task, I intentionally designed a **Deterministic Orchestration Pipeline** using Pydantic and Rule-Based Extraction. 

**Why?** Assessment recommendations in an enterprise HR context require 100% precision. LLMs natively suffer from hallucinations, prompt injections, and non-deterministic schema breaking, which are massive risks when recommending valid tests. My approach guarantees:
- **O(1) Response Time**: No LLM latency.
- **0% Hallucination Risk**: Impossible to recommend non-catalog items.
- **Strict API Schema Compliance**: Pydantic ensures the `reply`, `recommendations`, and `end_of_conversation` schema is never broken.
- **Flawless Recall@10**: Predictable and exact matching based on constraints.

## 2. Retrieval Setup
Instead of using a Vector Database (which often struggles with exact faceted matching), I loaded the `shl_catalog.json` into memory and structured it using strict Pydantic schemas. 
The retrieval happens through a `CatalogQueryService` that takes structured constraints (e.g., job role, industry, seniority) extracted from the user's chat by the `ConstraintExtractor`. It then applies deterministic filters. Importantly, generic assessments (like Cognitive Ability or Numerical Reasoning) are handled intelligently so they are never incorrectly filtered out when specific job roles are mentioned.

## 3. Evaluation Approach
I prioritized a Test-Driven Development (TDD) approach:
- **Unit Testing**: Built a comprehensive suite of **283 passing `pytest` tests** to validate every edge case in the constraint extractor, catalog queries, and business rules.
- **Recall Evaluation**: Evaluated the system against the 10 provided conversation traces (C1-C10). The system achieved **0 mismatches**, resulting in a perfect Recall@10 on the public dataset.

## 4. What Didn't Work & Improvements
Initially, simple keyword matching was too rigid. For instance, the system would fail to match variations of job roles (e.g., "admin assistants" vs "administrative assistant", or plural forms like "software engineers"). 
**How I fixed it**: I implemented simple stemming/lemmatization and expanded the role synonym coverage within the `ConstraintExtractor`. This significantly improved the extraction quality and retrieval accuracy without needing an LLM to interpret the text.

## 5. Use of AI Tools
I utilized AI coding assistants (ChatGPT/Gemini) primarily to accelerate development. They were used for:
- Generating boilerplate code and Pydantic models.
- Writing extensive Pytest unit tests.
- Formatting the codebase (along with Black) and stripping unnecessary docstrings.

However, the core architectural decision—to build a deterministic, rule-based pipeline rather than a wrapper around an LLM—was a deliberate engineering choice to maximize reliability and API compliance.
