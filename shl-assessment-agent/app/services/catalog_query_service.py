import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar
from app.models.catalog import Assessment, Catalog
from app.models.constraints import HiringConstraints, WorkLocation, JobLevel

@dataclass(frozen=True)
class CatalogQuery:

    constraints: HiringConstraints | None = None
    job_levels: Sequence[str] = field(default_factory=tuple)
    languages: Sequence[str] = field(default_factory=tuple)
    assessment_keys: Sequence[str] = field(default_factory=tuple)
    max_duration: int | None = None
    adaptive: bool | None = None
    remote: bool | None = None
    assessment_types: Sequence[str] = field(default_factory=tuple)
    keywords: Sequence[str] = field(default_factory=tuple)
    skills: Sequence[str] = field(default_factory=tuple)
    limit: int = 10


@dataclass(frozen=True)
class CatalogCandidate:

    assessment: Assessment
    score: float


@dataclass(frozen=True)
class CatalogQueryService:

    catalog: Catalog

    TEST_TYPE_KEYS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("A", "Ability & Aptitude"),
        ("B", "Biodata & Situational Judgment"),
        ("C", "Competencies"),
        ("D", "Development & 360"),
        ("K", "Knowledge & Skills"),
        ("P", "Personality & Behavior"),
        ("S", "Simulations"),
    )
    JOB_LEVEL_ALIASES: ClassVar[tuple[tuple[str, tuple[str, ...]], ...]] = (
        ("graduate", ("graduate",)),
        ("entry level", ("entry level", "entry-level")),
        ("mid level", ("mid-professional", "mid level", "mid-level")),
        (
            "senior",
            (
                "senior",
                "mid-professional",
                "professional individual contributor",
            ),
        ),
        ("manager", ("manager", "front line manager", "supervisor")),
        ("executive", ("executive", "director")),
    )

    @staticmethod
    def _is_generic_assessment(assessment: Assessment) -> bool:
        name = assessment.name.casefold()
        desc = assessment.description.casefold()
        generic_keywords = [
            "cognitive",
            "numerical",
            "verbal",
            "inductive",
            "logical",
            "personality",
            "opq",
            "sjt",
            "situational judgement",
            "situational judgment",
            "graduate scenarios",
            "aptitude",
            "behavioural",
            "behavioral",
            "occupational personality",
            "verify g+",
            "verify interactive",
            "global skills",
        ]
        return any(kw in name or kw in desc for kw in generic_keywords)

    def _category_match_score(
        self,
        assessment: Assessment,
        constraints: HiringConstraints | None,
    ) -> float:
        if not constraints:
            return 0.0

        score = 0.0
        name = assessment.name.casefold()
        desc = assessment.description.casefold()
        keys = [k.casefold() for k in assessment.keys]

        is_graduate = constraints.job_level == JobLevel.GRADUATE or (
            constraints.role and "graduate" in constraints.role.casefold()
        )
        if is_graduate:
            supports_graduate = any(
                "graduate" in level.casefold() for level in assessment.job_levels
            )
            if (
                supports_graduate
                or "graduate" in name
                or "graduate" in desc
                or any("graduate" in k for k in keys)
            ):
                score += 5.0
            if self._is_generic_assessment(assessment) and any(
                x in name for x in ["numerical", "verbal", "g+", "scenarios"]
            ):
                score += 0.2

        is_leadership = constraints.leadership_required is True or (
            constraints.role
            and any(
                x in constraints.role.casefold()
                for x in ["manager", "executive", "leader", "director", "trainee"]
            )
        )
        if is_leadership:
            if any(
                x in name or x in desc or x in keys
                for x in ["leadership", "manager", "executive", "trainee"]
            ):
                score += 5.0

        is_sales = (constraints.role and "sales" in constraints.role.casefold()) or (
            constraints.industry and "sales" in constraints.industry.casefold()
        )
        if is_sales:
            if any(x in name or x in desc or x in keys for x in ["sales", "selling"]):
                score += 5.0

        is_cust_service = constraints.customer_facing is True or (
            constraints.role
            and any(
                x in constraints.role.casefold()
                for x in ["customer", "support", "contact", "agent", "call"]
            )
        )
        if is_cust_service:
            if any(
                x in name or x in desc or x in keys
                for x in [
                    "customer",
                    "service",
                    "support",
                    "contact",
                    "phone",
                    "call",
                    "svar",
                ]
            ):
                score += 5.0

        is_technical = constraints.technical_role is True or (
            constraints.role
            and any(
                x in constraints.role.casefold()
                for x in ["engineer", "developer", "programmer", "architect", "tech"]
            )
        )
        if is_technical:
            if any(
                x in name or x in desc or x in keys
                for x in [
                    "coding",
                    "programming",
                    "software",
                    "java",
                    "python",
                    "rust",
                    "aws",
                    "docker",
                    "spring",
                    "sql",
                    "linux",
                    "networking",
                    "technology",
                ]
            ):
                score += 5.0

        is_manufacturing = (
            constraints.industry and "manufacturing" in constraints.industry.casefold()
        ) or (
            constraints.role
            and any(
                x in constraints.role.casefold()
                for x in ["operator", "plant", "manufacturing", "safety", "indust"]
            )
        )
        if is_manufacturing:
            if any(
                x in name or x in desc or x in keys
                for x in ["manufactur", "industrial", "safety", "dsi", "dependability"]
            ):
                score += 5.0

        return score

    def search(self, query: CatalogQuery | HiringConstraints) -> list[CatalogCandidate]:
        catalog_query = self._coerce_query(query)
        candidates: list[CatalogCandidate] = []

        for assessment in self.catalog.assessments:
            if not self._passes_hard_filters(assessment, catalog_query):
                continue

            score = self._score_assessment(assessment, catalog_query)

            has_category_match = (
                self._category_match_score(assessment, catalog_query.constraints) > 0
            )
            if not (self._is_generic_assessment(assessment) or has_category_match):
                if not self._passes_text_evidence_filter(assessment, catalog_query):
                    continue
                if self._has_text_criteria(catalog_query) and score <= 0:
                    continue

            candidates.append(CatalogCandidate(assessment=assessment, score=score))

        return sorted(
            candidates,
            key=lambda candidate: -candidate.score,
        )[: catalog_query.limit]

    def _coerce_query(self, query: CatalogQuery | HiringConstraints) -> CatalogQuery:
        if isinstance(query, CatalogQuery):
            if query.constraints is None:
                return query
            return self._merge_constraints(query, query.constraints)
        return self._merge_constraints(CatalogQuery(), query)

    def _merge_constraints(
        self,
        query: CatalogQuery,
        constraints: HiringConstraints,
    ) -> CatalogQuery:
        job_levels = list(query.job_levels)
        if constraints.job_level is not None:
            job_levels.append(constraints.job_level.value)
        if constraints.seniority is not None:
            job_levels.append(constraints.seniority.value)

        keywords = list(query.keywords)
        for value in (
            constraints.role,
            constraints.industry,
            constraints.purpose.value if constraints.purpose else None,
        ):
            if value:
                keywords.append(value)
        keywords.extend(constraints.additional_requirements or [])

        skills = list(query.skills)
        skills.extend(constraints.required_skills or [])
        skills.extend(constraints.preferred_skills or [])

        remote = query.remote
        if constraints.work_location is WorkLocation.REMOTE:
            remote = True

        return CatalogQuery(
            constraints=constraints,
            job_levels=self._deduplicate(job_levels),
            languages=self._deduplicate(
                list(query.languages) + list(constraints.languages or [])
            ),
            assessment_keys=query.assessment_keys,
            max_duration=query.max_duration,
            adaptive=query.adaptive,
            remote=remote,
            assessment_types=self._deduplicate(
                list(query.assessment_types) + list(constraints.assessment_types or [])
            ),
            keywords=self._deduplicate(keywords),
            skills=self._deduplicate(skills),
            limit=query.limit,
        )

    def _passes_hard_filters(
        self,
        assessment: Assessment,
        query: CatalogQuery,
    ) -> bool:
        if query.max_duration is not None:
            duration = self._extract_duration(assessment)
            if duration is None or duration > query.max_duration:
                return False
        if (
            query.remote is not None
            and self._extract_boolean(
                assessment,
                "remote",
                assessment.remote_support,
            )
            is not query.remote
        ):
            return False
        if (
            query.adaptive is not None
            and self._extract_boolean(
                assessment,
                "adaptive",
                assessment.adaptive_support,
            )
            is not query.adaptive
        ):
            return False

        if query.job_levels and not self._is_generic_assessment(assessment):
            if not self._matches_any_job_level(assessment, query.job_levels):
                return False
        if query.languages and not self._matches_any(
            self._assessment_languages(assessment),
            query.languages,
        ):
            return False
        if query.assessment_keys and not self._matches_any(
            assessment.keys,
            query.assessment_keys,
        ):
            return False
        if query.assessment_types and not self._matches_any_assessment_type(
            assessment,
            query.assessment_types,
        ):
            return False
        return True

    def _score_assessment(
        self,
        assessment: Assessment,
        query: CatalogQuery,
    ) -> float:
        score = 0.0
        searchable_text = self._build_searchable_text(assessment)

        score += 1.0 * self._count_matches(query.job_levels, assessment.job_levels)
        score += 0.8 * self._count_matches(
            query.languages,
            self._assessment_languages(assessment),
        )
        score += 1.2 * self._count_matches(query.assessment_keys, assessment.keys)
        score += 1.0 * self._score_assessment_type(assessment, query.assessment_types)
        score += 1.1 * self._count_text_matches(query.skills, searchable_text)
        score += 0.7 * self._count_text_matches(query.keywords, searchable_text)

        if (
            query.max_duration is not None
            and self._extract_duration(assessment) is not None
        ):
            score += 0.3
        if query.remote is not None:
            score += 0.2
        if query.adaptive is not None:
            score += 0.2

        if query.constraints is not None and self._is_generic_assessment(assessment):
            score += 0.01

        if "Knowledge & Skills" in assessment.keys and query.skills:
            if self._count_text_matches(query.skills, searchable_text) > 0:
                score += 1.5

        score += self._category_match_score(assessment, query.constraints)

        return round(score, 4)

    @staticmethod
    def _has_text_criteria(query: CatalogQuery) -> bool:
        return bool(
            query.job_levels
            or query.languages
            or query.assessment_keys
            or query.assessment_types
            or query.keywords
            or query.skills
        )

    def _matches_any_job_level(
        self,
        assessment: Assessment,
        job_levels: Sequence[str],
    ) -> bool:
        assessment_levels = [self._normalize(level) for level in assessment.job_levels]
        for job_level in job_levels:
            normalized_level = self._normalize(job_level)
            aliases = self._job_level_aliases(normalized_level)
            if any(
                self._terms_match(self._normalize(alias), level)
                for alias in aliases
                for level in assessment_levels
            ):
                return True
        return False

    def _matches_any_assessment_type(
        self,
        assessment: Assessment,
        assessment_types: Sequence[str],
    ) -> bool:
        return self._score_assessment_type(assessment, assessment_types) > 0

    def _score_assessment_type(
        self,
        assessment: Assessment,
        assessment_types: Sequence[str],
    ) -> int:
        if not assessment_types:
            return 0

        candidate_values = [assessment.test_type, *assessment.keys]
        expanded_values = [self._normalize(value) for value in candidate_values]
        expanded_values.extend(self._expanded_test_type_values(assessment.test_type))

        count = 0
        for assessment_type in assessment_types:
            normalized_type = self._normalize(assessment_type)
            if self._matches_assessment_type(normalized_type, expanded_values):
                count += 1
        return count

    @staticmethod
    def _matches_assessment_type(
        normalized_type: str,
        expanded_values: Sequence[str],
    ) -> bool:
        if len(normalized_type) <= 2:
            return normalized_type in expanded_values
        expanded_labels = [value for value in expanded_values if len(value) > 2]
        return any(
            CatalogQueryService._terms_match(normalized_type, value)
            for value in expanded_labels
        )

    def _passes_text_evidence_filter(
        self,
        assessment: Assessment,
        query: CatalogQuery,
    ) -> bool:
        if not query.skills and not query.keywords:
            return True

        searchable_text = self._build_searchable_text(assessment)
        return (
            self._count_text_matches(query.skills, searchable_text)
            + self._count_text_matches(query.keywords, searchable_text)
            > 0
        )

    @staticmethod
    def _matches_any(
        values: Sequence[str],
        requested_values: Sequence[str],
    ) -> bool:
        normalized_values = [CatalogQueryService._normalize(value) for value in values]
        for requested_value in requested_values:
            normalized_request = CatalogQueryService._normalize(requested_value)
            if any(
                CatalogQueryService._terms_match(normalized_request, value)
                for value in normalized_values
            ):
                return True
        return False

    @staticmethod
    def _count_matches(
        requested_values: Sequence[str],
        candidate_values: Sequence[str],
    ) -> int:
        count = 0
        normalized_candidates = [
            CatalogQueryService._normalize(value) for value in candidate_values
        ]
        for requested_value in requested_values:
            normalized_request = CatalogQueryService._normalize(requested_value)
            if any(
                CatalogQueryService._terms_match(normalized_request, candidate)
                for candidate in normalized_candidates
            ):
                count += 1
        return count

    @staticmethod
    def _count_text_matches(
        requested_values: Sequence[str],
        searchable_text: str,
    ) -> int:
        return sum(
            CatalogQueryService._normalize(value) in searchable_text
            for value in requested_values
        )

    def _expanded_test_type_values(self, test_type: str) -> list[str]:
        values: list[str] = []
        parts = [part.strip() for part in test_type.split(",") if part.strip()]
        for part in parts:
            for code, label in self.TEST_TYPE_KEYS:
                if self._normalize(part) == self._normalize(code):
                    values.append(self._normalize(label))
        return values

    @staticmethod
    def _build_searchable_text(assessment: Assessment) -> str:
        values = [
            assessment.name,
            assessment.description,
            assessment.test_type,
            *assessment.keys,
            *assessment.job_levels,
            *assessment.languages,
        ]
        extras = assessment.model_extra or {}
        for value in extras.values():
            if isinstance(value, str):
                values.append(value)
            elif isinstance(value, list):
                values.extend(str(item) for item in value)
        return CatalogQueryService._normalize(" ".join(values))

    @staticmethod
    def _assessment_languages(assessment: Assessment) -> list[str]:
        languages = list(assessment.languages)
        extras = assessment.model_extra or {}
        extra_languages = extras.get("languages")
        if isinstance(extra_languages, list):
            languages.extend(str(language) for language in extra_languages)
        return list(CatalogQueryService._deduplicate(languages))

    @staticmethod
    def _extract_duration(assessment: Assessment) -> int | None:
        if isinstance(assessment.duration, int):
            return assessment.duration

        extras = assessment.model_extra or {}
        for key in ("duration", "duration_raw"):
            value = extras.get(key)
            if value is None:
                continue
            match = re.search(r"\d+", str(value))
            if match:
                return int(match.group(0))
        return None

    @staticmethod
    def _extract_boolean(
        assessment: Assessment,
        extra_key: str,
        fallback: bool,
    ) -> bool:
        extras = assessment.model_extra or {}
        value = extras.get(extra_key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.casefold() in {"yes", "true", "1"}
        return fallback

    def _job_level_aliases(self, normalized_job_level: str) -> tuple[str, ...]:
        for label, aliases in self.JOB_LEVEL_ALIASES:
            if self._terms_match(normalized_job_level, label):
                return aliases
        return (normalized_job_level,)

    @staticmethod
    def _terms_match(requested_value: str, candidate_value: str) -> bool:
        return requested_value in candidate_value or candidate_value in requested_value

    @staticmethod
    def _normalize(value: Any) -> str:
        normalized = str(value).casefold()
        normalized = normalized.replace("&", " and ")
        normalized = normalized.replace("/", " ")
        normalized = re.sub(r"[^a-z0-9+#.]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    @staticmethod
    def _deduplicate(values: Iterable[str]) -> tuple[str, ...]:
        deduplicated: list[str] = []
        for value in values:
            if value and value not in deduplicated:
                deduplicated.append(value)
        return tuple(deduplicated)
