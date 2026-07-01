import os
from functools import lru_cache
from typing import Any

from fastapi import Depends

from app.models.catalog import Assessment, Catalog
from app.services.catalog_query_service import CatalogQueryService
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.response_generator import ResponseGenerator, build_response_generator

_CATALOG_PATH_ENV = "SHL_CATALOG_PATH"

_DEMO_CATALOG_DATA: dict[str, Any] = {
    "assessments": [
        {
            "id": "opq32r",
            "name": "Occupational Personality Questionnaire OPQ32r",
            "url": "https://www.shl.com/products/product-catalog/view/occupational-personality-questionnaire-opq32r/",
            "description": "Measures 32 workplace behaviour dimensions including leadership, influencing style, and strategic thinking.",
            "duration": 25,
            "job_levels": ["Graduate", "Manager", "Executive", "Director"],
            "languages": [
                "English International",
                "French (Canada)",
                "Portuguese",
                "Chinese Simplified",
                "Spanish",
                "German",
                "Dutch",
                "Italian",
            ],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "P",
            "keys": ["Personality & Behavior"],
        },
        {
            "id": "opq-leadership-report",
            "name": "OPQ Leadership Report",
            "url": "https://www.shl.com/products/product-catalog/view/opq-leadership-report/",
            "description": "Leadership report generated from OPQ32r results.",
            "duration": None,
            "job_levels": ["Manager", "Executive", "Director"],
            "languages": [
                "Dutch",
                "English International",
                "English (USA)",
                "Romanian",
            ],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "P",
            "keys": ["Personality & Behavior"],
        },
        {
            "id": "verify-g-plus",
            "name": "SHL Verify Interactive G+",
            "url": "https://www.shl.com/products/product-catalog/view/shl-verify-interactive-g/",
            "description": "Adaptive general cognitive ability test covering inductive, numerical, and deductive reasoning.",
            "duration": 36,
            "job_levels": ["Graduate", "Entry Level", "Mid-Professional"],
            "languages": [
                "English (USA)",
                "Chinese Traditional",
                "Korean",
                "Serbian",
                "French",
                "German",
            ],
            "remote_support": True,
            "adaptive_support": True,
            "test_type": "A",
            "keys": ["Ability & Aptitude"],
        },
        {
            "id": "smart-interview-live-coding",
            "name": "Smart Interview Live Coding",
            "url": "https://www.shl.com/products/product-catalog/view/smart-interview-live-coding/",
            "description": "Adaptive live-coding interview for software engineering roles.",
            "duration": None,
            "job_levels": ["Graduate", "Mid-Professional", "Senior"],
            "languages": ["English (USA)"],
            "remote_support": True,
            "adaptive_support": True,
            "test_type": "K",
            "keys": ["Knowledge & Skills"],
        },
        {
            "id": "core-java-advanced-new",
            "name": "Core Java (Advanced Level) (New)",
            "url": "https://www.shl.com/products/product-catalog/view/core-java-advanced-level-new/",
            "description": "Covers Java concurrency, JVM internals, performance tuning, and design patterns.",
            "duration": 13,
            "job_levels": ["Mid-Professional", "Senior"],
            "languages": ["English (USA)"],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "K",
            "keys": ["Knowledge & Skills"],
        },
        {
            "id": "graduate-scenarios",
            "name": "Graduate Scenarios",
            "url": "https://www.shl.com/products/product-catalog/view/graduate-scenarios/",
            "description": "Situational judgement test designed for graduate-level candidates.",
            "duration": None,
            "job_levels": ["Graduate", "Entry Level"],
            "languages": ["English International"],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "B",
            "keys": ["Biodata & Situational Judgment"],
        },
        {
            "id": "dependability-safety-instrument",
            "name": "Dependability and Safety Instrument (DSI)",
            "url": "https://www.shl.com/products/product-catalog/view/dependability-and-safety-instrument-dsi/",
            "description": "Measures integrity, reliability, and safety attitudes across sectors.",
            "duration": 10,
            "job_levels": ["Entry Level", "Mid-Professional"],
            "languages": [
                "Portuguese (Brazil)",
                "Chinese Traditional",
                "Danish",
                "Dutch",
                "Latin American Spanish",
                "English (USA)",
            ],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "P",
            "keys": ["Personality & Behavior"],
        },
        {
            "id": "customer-service-phone-simulation",
            "name": "Customer Service Phone Simulation",
            "url": "https://www.shl.com/products/product-catalog/view/customer-service-phone-simulation/",
            "description": "Phone-based customer service simulation for contact centre roles.",
            "duration": 20,
            "job_levels": ["Entry Level", "Mid-Professional"],
            "languages": [
                "English (USA)",
                "French (Canada)",
                "Portuguese (Brazil)",
                "Dutch",
                "Italian",
            ],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "S",
            "keys": ["Simulations", "Biodata & Situational Judgment"],
        },
        {
            "id": "contact-center-call-simulation-new",
            "name": "Contact Center Call Simulation (New)",
            "url": "https://www.shl.com/products/product-catalog/view/contact-center-call-simulation-new/",
            "description": "Standalone simulation focused on the in-call interaction for contact centre screening.",
            "duration": 15,
            "job_levels": ["Entry Level", "Mid-Professional"],
            "languages": ["English (USA)"],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "S",
            "keys": ["Simulations"],
        },
        {
            "id": "entry-level-customer-service-retail-contact-center",
            "name": "Entry Level Customer Serv - Retail & Contact Center",
            "url": "https://www.shl.com/products/product-catalog/view/entry-level-customer-serv-retail-and-contact-center/",
            "description": "Personality and competency measure for entry-level customer service roles.",
            "duration": 19,
            "job_levels": ["Entry Level"],
            "languages": [
                "Latin American Spanish",
                "German",
                "French",
                "Chinese Simplified",
                "English (USA)",
            ],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "P",
            "keys": ["Personality & Behavior", "Competencies"],
        },
        {
            "id": "verify-numerical-reasoning",
            "name": "SHL Verify Interactive – Numerical Reasoning",
            "url": "https://www.shl.com/products/product-catalog/view/shl-verify-interactive-numerical-reasoning/",
            "description": "Adaptive numerical reasoning assessment for graduate and professional roles.",
            "duration": 20,
            "job_levels": ["Graduate", "Mid-Professional"],
            "languages": [
                "French",
                "German",
                "Italian",
                "Dutch",
                "English International",
            ],
            "remote_support": True,
            "adaptive_support": True,
            "test_type": "A",
            "keys": ["Ability & Aptitude"],
        },
        {
            "id": "safety-dependability-8",
            "name": "Manufac. & Indust. - Safety & Dependability 8.0",
            "url": "https://www.shl.com/products/product-catalog/view/safety-and-dependability-focus-8-0/",
            "description": "Sector-specific safety personality measure with manufacturing and industrial norms.",
            "duration": 16,
            "job_levels": ["Entry Level", "Mid-Professional"],
            "languages": [
                "English (USA)",
                "German",
                "Latin American Spanish",
                "French",
            ],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "P",
            "keys": ["Personality & Behavior"],
        },
        {
            "id": "global-skills-assessment",
            "name": "Global Skills Assessment",
            "url": "https://www.shl.com/products/product-catalog/view/global-skills-assessment/",
            "description": "Self-reported skills and competency assessment across 19+ languages.",
            "duration": 16,
            "job_levels": ["Mid-Professional", "Manager"],
            "languages": [
                "Indonesian",
                "Italian",
                "Swedish",
                "Thai",
                "Portuguese (Brazil)",
                "English (USA)",
            ],
            "remote_support": True,
            "adaptive_support": False,
            "test_type": "C",
            "keys": ["Competencies", "Knowledge & Skills"],
        },
    ]
}


@lru_cache(maxsize=1)
def get_catalog() -> Catalog:
    catalog_path = os.getenv(_CATALOG_PATH_ENV, "")
    if catalog_path:
        import json
        from pathlib import Path

        from app.services.catalog_loader import CatalogLoader

        loader = CatalogLoader()
        return loader.load_catalog(Path(catalog_path))

    return Catalog.model_validate(_DEMO_CATALOG_DATA)


@lru_cache(maxsize=1)
def get_catalog_query_service() -> CatalogQueryService:
    return CatalogQueryService(catalog=get_catalog())


@lru_cache(maxsize=1)
def get_response_generator() -> ResponseGenerator:
    return build_response_generator()


def get_orchestrator(
    catalog_query_service: CatalogQueryService = Depends(get_catalog_query_service),
) -> ChatOrchestrator:
    return ChatOrchestrator.build(
        catalog_query_service=catalog_query_service,
    )
