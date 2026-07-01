import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from pydantic import ValidationError
from app.core.exceptions import (
    AssessmentNotFoundError,
    CatalogLoadError,
    CatalogValidationError,
)
from app.models.catalog import Assessment, Catalog


@dataclass
class CatalogLoader:

    _catalog: Catalog | None = field(default=None, init=False, repr=False)

    def load_catalog(self, path: str | Path) -> Catalog:
        catalog_path = Path(path)
        try:
            raw_catalog = self._read_json(catalog_path)
        except (OSError, json.JSONDecodeError) as exc:
            raise CatalogLoadError(
                f"Unable to load catalog from {catalog_path}."
            ) from exc

        if isinstance(raw_catalog, list):

            raw_catalog = {
                "assessments": [self._transform_raw_entry(e) for e in raw_catalog]
            }
        elif isinstance(raw_catalog, dict) and "assessments" in raw_catalog:

            raw_catalog = {
                **{k: v for k, v in raw_catalog.items() if k != "assessments"},
                "assessments": [
                    self._transform_raw_entry(e) for e in raw_catalog["assessments"]
                ],
            }

        try:
            catalog = Catalog.model_validate(raw_catalog)
        except ValidationError as exc:
            raise CatalogValidationError("Catalog data failed validation.") from exc

        self._catalog = catalog
        return catalog

    def get_all(self) -> list[Assessment]:
        return list(self._require_catalog().assessments)

    def get_by_id(self, assessment_id: str) -> Assessment:
        for assessment in self._require_catalog().assessments:
            if assessment.id == assessment_id:
                return assessment

        raise AssessmentNotFoundError(
            f"Assessment with id '{assessment_id}' was not found."
        )

    def find_by_name(self, name: str) -> Assessment:
        normalized_name = name.casefold()
        for assessment in self._require_catalog().assessments:
            if assessment.name.casefold() == normalized_name:
                return assessment

        raise AssessmentNotFoundError(f"Assessment with name '{name}' was not found.")

    def search(self, text: str) -> list[Assessment]:
        keywords = self._normalize_keywords(text)
        if not keywords:
            return []

        matches: list[Assessment] = []
        for assessment in self._require_catalog().assessments:
            searchable_text = self._build_searchable_text(assessment)
            if any(keyword in searchable_text for keyword in keywords):
                matches.append(assessment)

        return matches

    def _require_catalog(self) -> Catalog:
        if self._catalog is None:
            raise CatalogLoadError("Catalog has not been loaded.")
        return self._catalog

    @staticmethod
    def _transform_raw_entry(raw: dict[str, Any]) -> dict[str, Any]:

        key_to_code: dict[str, str] = {
            "Ability & Aptitude": "A",
            "Biodata & Situational Judgment": "B",
            "Competencies": "C",
            "Development & 360": "D",
            "Knowledge & Skills": "K",
            "Personality & Behavior": "P",
            "Simulations": "S",
        }

        keys: list[str] = raw.get("keys") or []
        codes = [key_to_code[k] for k in keys if k in key_to_code]
        test_type = ", ".join(codes) if codes else raw.get("test_type", "")

        duration_raw = raw.get("duration", "")
        if isinstance(duration_raw, int):
            duration: int | None = duration_raw
        elif isinstance(duration_raw, str) and duration_raw.strip():
            match = re.search(r"\d+", duration_raw)
            duration = int(match.group(0)) if match else None
        else:
            duration = None

        def _parse_yesno(value: Any) -> bool:  # noqa: ANN401
            if isinstance(value, bool):
                return value
            return str(value).strip().casefold() in {"yes", "true", "1"}

        status_raw = str(raw.get("status", "ok"))
        status = "active" if status_raw == "ok" else status_raw

        transformed: dict[str, Any] = {
            "id": raw.get("entity_id") or raw.get("id", ""),
            "name": raw.get("name", ""),
            "url": raw.get("link") or raw.get("url", ""),
            "description": raw.get("description", ""),
            "duration": duration,
            "job_levels": list(raw.get("job_levels") or []),
            "languages": list(raw.get("languages") or []),
            "remote_support": _parse_yesno(raw.get("remote", False)),
            "adaptive_support": _parse_yesno(raw.get("adaptive", False)),
            "test_type": test_type,
            "keys": keys,
            "status": status,
        }

        for extra_key in (
            "scraped_at",
            "job_levels_raw",
            "languages_raw",
            "duration_raw",
        ):
            if extra_key in raw:
                transformed[extra_key] = raw[extra_key]

        return transformed

    @staticmethod
    def _read_json(path: Path) -> Any:
        with path.open(encoding="utf-8") as catalog_file:
            return json.load(catalog_file, strict=False)

    @staticmethod
    def _normalize_keywords(text: str) -> list[str]:
        return [keyword.casefold() for keyword in text.split() if keyword.strip()]

    @staticmethod
    def _build_searchable_text(assessment: Assessment) -> str:
        values = [
            assessment.name,
            assessment.description,
            *assessment.keys,
            *assessment.job_levels,
            *assessment.languages,
        ]
        return " ".join(values).casefold()
