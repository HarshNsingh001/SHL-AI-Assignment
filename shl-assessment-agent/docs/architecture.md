# Architecture

This project starts with a clean FastAPI application shell and empty extension
points for future agent capabilities.

The current implementation intentionally includes no retrieval, ranking,
prompting, model calls, embeddings, or SHL-specific recommendation logic.

## Layers

- `app/api`: HTTP routing, middleware, and exception handling.
- `app/core`: runtime configuration and infrastructure.
- `app/models`: Pydantic request and response contracts.
- `app/services`: future orchestration layer.
- `app/retrieval`: future retrieval layer.
- `app/ranking`: future ranking layer.
- `app/prompts`: future prompt assets.
- `app/memory`: future conversation memory layer.
- `app/utils`: future shared utilities.
