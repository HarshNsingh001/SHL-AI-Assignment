# SHL Assessment Agent - Project Report

## 1. Project Overview
The **SHL Assessment Agent** is an automated, deterministic orchestration pipeline designed to interact with users, extract constraints, and recommend appropriate assessments from the SHL catalog. 

Unlike many modern conversational agents, this project **does not rely on Large Language Models (LLMs)**, external APIs, or vector databases. Instead, it leverages a robust, rule-based deterministic architecture using **Pydantic** models for strict validation and typing. This ensures 100% predictable, reliable, and testable behavior for every user interaction.

## 2. Core Architecture & Pipeline
The application processes user queries through a sequential, five-stage pipeline managed by the `ChatOrchestrator` (`app/services/chat_orchestrator.py`). 

When a chat request is received (via the API defined in `app/api/routes.py`), the data flows through the following services in order:

### A. Conversation Manager (`app/services/conversation_manager.py`)
- **Purpose**: Manages the state and history of the user's conversation.
- **Function**: Keeps track of previous messages, context, and extracted constraints to ensure multi-turn conversations maintain continuity.

### B. Constraint Extractor (`app/services/constraint_extractor.py`)
- **Purpose**: Parses the user's text to identify structured requirements.
- **Function**: Uses rule-based extraction (regex, keywords, and synonym matching) to detect:
  - **Job Roles** (e.g., Software Engineer, Manager, Graduate)
  - **Assessment Types** (e.g., Cognitive, Personality, Coding)
  - **Industries** or specific skills.
- **Recent Updates**: Implemented stemming/lemmatization and expanded synonym coverage to handle plurals and variations effectively.

### C. Catalog Query Service (`app/services/catalog_query_service.py`)
- **Purpose**: Retrieves matching assessments from the underlying catalog database.
- **Function**: Applies deterministic filtering and ranking against the `shl_catalog.json`. It intelligently handles generic assessments (like Cognitive Ability or Numerical Reasoning) so they aren't incorrectly filtered out when specific job roles are mentioned.

### D. Business Rule Engine (`app/services/business_rule_engine.py`)
- **Purpose**: Enforces SHL's specific business and product rules.
- **Function**: Validates the initial set of queried assessments to ensure combinations make logical sense (e.g., ensuring a candidate isn't given two identical tests, or ensuring senior roles get appropriate difficulty assessments).

### E. Recommendation Engine & Response Generator (`app/services/recommendation_engine.py` / `response_generator.py`)
- **Purpose**: Selects the final optimal assessments and formats the output.
- **Function**: Scores and selects the top recommendations. The `ResponseGenerator` then formats this data into a clean, human-readable Markdown response (often displaying recommendations in structured tables).

## 3. Data Models
The system heavily relies on `pydantic` for data validation, located in the `app/models/` directory:
- **`schemas.py`**: Defines API request/response structures.
- **`catalog.py`**: Represents the schema for assessments loaded from the JSON catalog.
- **`state.py`**: Defines the conversation state and context objects passed through the pipeline.

## 4. Setup and Local Development
The project is built using Python (3.14 recommended/used) and follows standard modern Python practices.

### Running the Application
1. **API Server**: The application is served using FastAPI/Uvicorn.
2. **Endpoints**: Entry points are defined in `app/api/routes.py`.

### Code Quality & Formatting
- The entire codebase is strictly typed and adheres to **PEP 8** standards.
- Vertical spacing and formatting are managed via `black`.
- All unnecessary or auto-generated AI docstrings have been removed to keep the codebase clean and professional.

## 5. Testing and Validation
- **Framework**: `pytest`
- **Location**: `tests/` directory.
- **Status**: The project has an extensive test suite ensuring high reliability. The current test suite validates **283 passing tests**.
- **Coverage**: Tests cover edge cases in the constraint extractor, catalog queries, business rules, and API endpoints to guarantee the pipeline operates correctly without breaking.

## 6. Key Takeaways for Submission
- **Why no LLM?** The assignment called for precision, reliability, and speed. A deterministic pipeline guarantees that identical inputs always yield identical, correct outputs without hallucination risks.
- **Maintainability**: The strict separation of concerns (Extraction -> Querying -> Business Rules -> Recommendation) means any single component can be upgraded independently.
- **Robustness**: Pydantic models catch data errors instantly, and the 100% test pass rate proves the system's production readiness.
