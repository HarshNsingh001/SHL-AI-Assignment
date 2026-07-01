import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from app.core.exceptions import (
    AssessmentNotFoundError,
    CatalogLoadError,
    CatalogValidationError,
)
from app.models.catalog import AssessmentStatus
from app.services.catalog_loader import CatalogLoader


def write_catalog(path: Path, catalog_data: Mapping[str, object]) -> None:
    path.write_text(json.dumps(catalog_data), encoding="utf-8")


def sample_catalog_data() -> dict[str, object]:
    return {
        "source": "test-fixture",
        "assessments": [
            {
                "id": "verify-g-plus",
                "name": "Verify G+",
                "url": "https://example.com/verify-g-plus",
                "description": "General cognitive ability assessment.",
                "duration": 36,
                "job_levels": ["graduate", "professional"],
                "languages": ["English"],
                "remote_support": True,
                "adaptive_support": False,
                "test_type": "cognitive",
                "keys": ["reasoning", "ability"],
                "status": "active",
                "family": "verify",
            },
            {
                "id": "coding-simulation",
                "name": "Coding Simulation",
                "url": "https://example.com/coding-simulation",
                "description": "Hands-on programming simulation.",
                "duration": 45,
                "job_levels": ["entry-level"],
                "languages": ["English", "Spanish"],
                "remote_support": True,
                "adaptive_support": False,
                "test_type": "simulation",
                "keys": ["python", "programming"],
                "status": "active",
            },
        ],
    }


def test_load_catalog_validates_and_caches_assessments(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path, sample_catalog_data())
    loader = CatalogLoader()

    catalog = loader.load_catalog(catalog_path)

    assert len(catalog.assessments) == 2
    assert catalog.additional_metadata() == {"source": "test-fixture"}
    assert loader.get_all()[0].id == "verify-g-plus"
    assert loader.get_all()[0].status is AssessmentStatus.ACTIVE


def test_get_by_id_returns_matching_assessment(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path, sample_catalog_data())
    loader = CatalogLoader()
    loader.load_catalog(catalog_path)

    assessment = loader.get_by_id("coding-simulation")

    assert assessment.name == "Coding Simulation"


def test_find_by_name_returns_case_insensitive_match(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path, sample_catalog_data())
    loader = CatalogLoader()
    loader.load_catalog(catalog_path)

    assessment = loader.find_by_name("verify g+")

    assert assessment.id == "verify-g-plus"


def test_search_matches_keywords_across_catalog_fields(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path, sample_catalog_data())
    loader = CatalogLoader()
    loader.load_catalog(catalog_path)

    name_matches = loader.search("coding")
    key_matches = loader.search("reasoning")
    job_level_matches = loader.search("graduate")
    language_matches = loader.search("spanish")

    assert [assessment.id for assessment in name_matches] == ["coding-simulation"]
    assert [assessment.id for assessment in key_matches] == ["verify-g-plus"]
    assert [assessment.id for assessment in job_level_matches] == ["verify-g-plus"]
    assert [assessment.id for assessment in language_matches] == ["coding-simulation"]


def test_search_returns_empty_list_for_blank_text(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path, sample_catalog_data())
    loader = CatalogLoader()
    loader.load_catalog(catalog_path)

    assert loader.search("   ") == []


def test_load_catalog_raises_validation_error_for_invalid_data(
    tmp_path: Path,
) -> None:
    catalog_path = tmp_path / "catalog.json"
    invalid_catalog = {"assessments": [{"id": "missing-required-fields"}]}
    write_catalog(catalog_path, invalid_catalog)
    loader = CatalogLoader()

    with pytest.raises(CatalogValidationError):
        loader.load_catalog(catalog_path)


def test_load_catalog_raises_load_error_for_missing_file(tmp_path: Path) -> None:
    loader = CatalogLoader()

    with pytest.raises(CatalogLoadError):
        loader.load_catalog(tmp_path / "missing.json")


def test_load_catalog_raises_load_error_for_invalid_json(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("{invalid-json", encoding="utf-8")
    loader = CatalogLoader()

    with pytest.raises(CatalogLoadError):
        loader.load_catalog(catalog_path)


def test_get_by_id_raises_not_found_for_unknown_assessment(
    tmp_path: Path,
) -> None:
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path, sample_catalog_data())
    loader = CatalogLoader()
    loader.load_catalog(catalog_path)

    with pytest.raises(AssessmentNotFoundError):
        loader.get_by_id("unknown")


def test_queries_require_loaded_catalog() -> None:
    loader = CatalogLoader()

    with pytest.raises(CatalogLoadError):
        loader.get_all()
