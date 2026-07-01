import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from app.models.business_rules import CatalogQueryResult, ConversationDecision
from app.models.catalog import Assessment
from app.models.constraints import ConstraintExtractionResult, HiringConstraints
from app.models.conversation import ConversationMessageRole, ConversationState
from app.models.recommendation_engine import (
    AssessmentRecommendation,
    RecommendationMetadata,
    RecommendationReason,
    RecommendationResult,
    RecommendationScore,
)
from app.services.catalog_query_service import CatalogCandidate


@dataclass(frozen=True)
class RecommendationEngine:

    default_limit: int = 10

    def generate(
        self,
        conversation_state: ConversationState,
        constraint_result: ConstraintExtractionResult,
        conversation_decision: ConversationDecision,
        catalog_query_result: CatalogQueryResult,
        limit: int | None = None,
    ) -> RecommendationResult:
        requested_limit = self._normalize_limit(limit)
        candidates = self._extract_candidates(catalog_query_result)
        prior_ids = self._prior_recommendation_ids(conversation_state)
        latest_message = self._latest_user_message(conversation_state)
        excluded_ids = self._excluded_assessment_ids(latest_message, candidates)
        should_return = conversation_decision.decision_type.value in {
            "recommend",
            "update_recommendations",
        }

        if not should_return:
            return self._empty_result(
                conversation_decision,
                requested_limit,
                len(candidates),
                prior_ids,
                excluded_ids,
                "Business-rule decision does not allow recommendations.",
            )

        scored_recommendations = [
            self._build_recommendation(
                candidate,
                constraint_result.constraints,
                conversation_decision,
                prior_ids,
            )
            for candidate in candidates
            if candidate.assessment.id not in excluded_ids
        ]

        scored_recommendations = self._merge_prior_recommendations(
            scored_recommendations,
            candidates,
            prior_ids,
            excluded_ids,
            constraint_result.constraints,
            conversation_decision,
        )

        ranked = sorted(
            scored_recommendations,
            key=lambda recommendation: (
                -recommendation.score.total,
                recommendation.assessment.name,
            ),
        )[:requested_limit]
        warnings = []
        if not ranked:
            warnings.append("No catalog candidates were available to recommend.")

        return RecommendationResult(
            recommendations=ranked,
            metadata=RecommendationMetadata(
                decision_type=conversation_decision.decision_type.value,
                requested_limit=requested_limit,
                candidate_count=len(candidates),
                returned_count=len(ranked),
                updated_from_previous=bool(prior_ids),
                prior_recommendation_ids=prior_ids,
                excluded_assessment_ids=excluded_ids,
            ),
            warnings=warnings,
        )

    def _build_recommendation(
        self,
        candidate: CatalogCandidate,
        constraints: HiringConstraints,
        conversation_decision: ConversationDecision,
        prior_ids: Sequence[str],
    ) -> AssessmentRecommendation:
        matched_constraints = self._matched_constraints(
            candidate.assessment, constraints
        )
        catalog_score = self._normalize_catalog_score(candidate.score)
        constraint_score = len(matched_constraints) * 0.25
        context_score = self._context_score(
            candidate.assessment, constraints, prior_ids
        )
        decision_score = self._decision_score(conversation_decision)
        total = round(
            catalog_score + constraint_score + context_score + decision_score, 4
        )
        confidence = self._confidence(total, matched_constraints)

        return AssessmentRecommendation(
            assessment=candidate.assessment,
            score=RecommendationScore(
                catalog_score=catalog_score,
                constraint_score=round(constraint_score, 4),
                context_score=round(context_score, 4),
                decision_score=decision_score,
                total=total,
            ),
            matched_constraints=matched_constraints,
            reason=RecommendationReason(
                summary="Matched deterministic catalog and constraint signals.",
                evidence=self._reason_evidence(
                    candidate.assessment, matched_constraints
                ),
            ),
            confidence=confidence,
        )

    def _matched_constraints(
        self,
        assessment: Assessment,
        constraints: HiringConstraints,
    ) -> list[str]:
        searchable_text = self._searchable_text(assessment)
        matches: list[str] = []

        if constraints.role and self._contains_any_token(
            searchable_text,
            self._tokens(constraints.role),
        ):
            matches.append("role")
        if constraints.job_level and self._matches_any(
            assessment.job_levels,
            [constraints.job_level.value],
        ):
            matches.append("job_level")
        if constraints.seniority and self._matches_any(
            assessment.job_levels,
            [constraints.seniority.value],
        ):
            matches.append("seniority")
        if constraints.industry and self._contains_text(
            searchable_text,
            constraints.industry,
        ):
            matches.append("industry")
        if constraints.languages and self._matches_any(
            assessment.languages,
            constraints.languages,
        ):
            matches.append("languages")
        if constraints.assessment_types and self._matches_any(
            [assessment.test_type, *assessment.keys],
            constraints.assessment_types,
        ):
            matches.append("assessment_types")
        if constraints.required_skills and self._contains_any_phrase(
            searchable_text,
            constraints.required_skills,
        ):
            matches.append("required_skills")
        if constraints.preferred_skills and self._contains_any_phrase(
            searchable_text,
            constraints.preferred_skills,
        ):
            matches.append("preferred_skills")
        if constraints.additional_requirements and self._contains_any_phrase(
            searchable_text,
            constraints.additional_requirements,
        ):
            matches.append("additional_requirements")
        if constraints.purpose and self._contains_text(
            searchable_text,
            constraints.purpose.value,
        ):
            matches.append("purpose")
        if constraints.leadership_required is True and self._contains_any_phrase(
            searchable_text,
            ("leadership", "leader", "manager", "supervisor"),
        ):
            matches.append("leadership_required")
        if constraints.technical_role is True and self._contains_any_phrase(
            searchable_text,
            ("technical", "coding", "programming", "developer", "engineer"),
        ):
            matches.append("technical_role")
        if constraints.customer_facing is True and self._contains_any_phrase(
            searchable_text,
            ("customer", "contact center", "sales", "call"),
        ):
            matches.append("customer_facing")

        return matches

    def _merge_prior_recommendations(
        self,
        recommendations: list[AssessmentRecommendation],
        candidates: Sequence[CatalogCandidate],
        prior_ids: Sequence[str],
        excluded_ids: Sequence[str],
        constraints: HiringConstraints,
        conversation_decision: ConversationDecision,
    ) -> list[AssessmentRecommendation]:
        if conversation_decision.decision_type.value != "update_recommendations":
            return recommendations

        existing_ids = {
            recommendation.assessment.id for recommendation in recommendations
        }
        candidate_by_id = {
            candidate.assessment.id: candidate for candidate in candidates
        }
        merged = list(recommendations)
        for prior_id in prior_ids:
            if prior_id in excluded_ids or prior_id in existing_ids:
                continue
            candidate = candidate_by_id.get(prior_id)
            if candidate is None:
                continue
            merged.append(
                self._build_recommendation(
                    candidate,
                    constraints,
                    conversation_decision,
                    prior_ids,
                )
            )
        return merged

    @staticmethod
    def _extract_candidates(
        catalog_query_result: CatalogQueryResult,
    ) -> list[CatalogCandidate]:
        raw_candidates = catalog_query_result.metadata.get("candidates", [])
        candidates: list[CatalogCandidate] = []
        for raw_candidate in raw_candidates:
            if isinstance(raw_candidate, CatalogCandidate):
                candidates.append(raw_candidate)
            elif isinstance(raw_candidate, dict):
                assessment = raw_candidate.get("assessment")
                score = raw_candidate.get("score", 0.0)
                if isinstance(assessment, Assessment) and isinstance(
                    score,
                    int | float,
                ):
                    candidates.append(
                        CatalogCandidate(
                            assessment=assessment,
                            score=float(score),
                        )
                    )
        return candidates

    @staticmethod
    def _prior_recommendation_ids(
        conversation_state: ConversationState,
    ) -> list[str]:
        ids = list(conversation_state.recommended_assessment_ids)
        for record in conversation_state.recommendation_history.records:
            for assessment_id in record.assessment_ids:
                if assessment_id not in ids:
                    ids.append(assessment_id)
        return ids

    def _excluded_assessment_ids(
        self,
        latest_message: str | None,
        candidates: Sequence[CatalogCandidate],
    ) -> list[str]:
        if latest_message is None:
            return []
        normalized_message = self._normalize(self._exclusion_text(latest_message))
        if not any(
            term in normalized_message
            for term in ("drop", "remove", "without", "skip", "exclude")
        ):
            return []

        excluded: list[str] = []
        for candidate in candidates:
            assessment_tokens = [
                *self._tokens(candidate.assessment.id),
                *self._tokens(candidate.assessment.name),
            ]
            if self._contains_any_token(normalized_message, assessment_tokens):
                excluded.append(candidate.assessment.id)
        return excluded

    @staticmethod
    def _context_score(
        assessment: Assessment,
        constraints: HiringConstraints,
        prior_ids: Sequence[str],
    ) -> float:
        score = 0.0
        if assessment.id in prior_ids:
            score += 0.75
        if constraints.leadership_required and any(
            "Personality" in key for key in assessment.keys
        ):
            score += 0.25
        if constraints.technical_role and any(
            "Knowledge" in key for key in assessment.keys
        ):
            score += 0.25
        if constraints.customer_facing and any(
            phrase in assessment.name.casefold()
            for phrase in ("customer", "contact", "sales")
        ):
            score += 0.25
        return score

    @staticmethod
    def _decision_score(conversation_decision: ConversationDecision) -> float:
        if conversation_decision.decision_type.value == "update_recommendations":
            return 0.5
        if conversation_decision.decision_type.value == "recommend":
            return 0.35
        return 0.0

    @staticmethod
    def _normalize_catalog_score(score: float) -> float:
        return round(min(max(score, 0.0), 10.0) * 3.0, 4)

    @staticmethod
    def _confidence(total: float, matched_constraints: Sequence[str]) -> float:
        confidence = min(
            0.95, 0.35 + (total * 0.04) + (len(matched_constraints) * 0.03)
        )
        return round(confidence, 4)

    @staticmethod
    def _reason_evidence(
        assessment: Assessment,
        matched_constraints: Sequence[str],
    ) -> list[str]:
        evidence = [f"matched:{constraint}" for constraint in matched_constraints]
        evidence.extend(f"key:{key}" for key in assessment.keys[:3])
        if assessment.job_levels:
            evidence.append(f"job_level:{assessment.job_levels[0]}")
        return evidence

    def _empty_result(
        self,
        conversation_decision: ConversationDecision,
        requested_limit: int,
        candidate_count: int,
        prior_ids: list[str],
        excluded_ids: list[str],
        warning: str,
    ) -> RecommendationResult:
        return RecommendationResult(
            recommendations=[],
            metadata=RecommendationMetadata(
                decision_type=conversation_decision.decision_type.value,
                requested_limit=requested_limit,
                candidate_count=candidate_count,
                returned_count=0,
                updated_from_previous=bool(prior_ids),
                prior_recommendation_ids=prior_ids,
                excluded_assessment_ids=excluded_ids,
            ),
            warnings=[warning],
        )

    def _normalize_limit(self, limit: int | None) -> int:
        requested_limit = self.default_limit if limit is None else limit
        return min(max(requested_limit, 0), 10)

    @staticmethod
    def _latest_user_message(conversation_state: ConversationState) -> str | None:
        for message in reversed(conversation_state.messages):
            if message.role is ConversationMessageRole.USER:
                return message.content
        return None

    @staticmethod
    def _searchable_text(assessment: Assessment) -> str:
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
        return RecommendationEngine._normalize(" ".join(values))

    @staticmethod
    def _matches_any(values: Sequence[str], requested_values: Sequence[str]) -> bool:
        normalized_values = [RecommendationEngine._normalize(value) for value in values]
        for requested_value in requested_values:
            normalized_request = RecommendationEngine._normalize(requested_value)
            if any(
                normalized_request in value or value in normalized_request
                for value in normalized_values
            ):
                return True
        return False

    @staticmethod
    def _contains_text(searchable_text: str, value: str) -> bool:
        return RecommendationEngine._normalize(value) in searchable_text

    @staticmethod
    def _contains_any_phrase(searchable_text: str, values: Iterable[str]) -> bool:
        return any(
            RecommendationEngine._normalize(value) in searchable_text
            for value in values
        )

    @staticmethod
    def _contains_any_token(searchable_text: str, tokens: Iterable[str]) -> bool:
        searchable_tokens = searchable_text.split()
        for token in tokens:
            if len(token) < 3:
                continue
            if token in searchable_text:
                return True
            if any(
                token.startswith(searchable_token) or searchable_token.startswith(token)
                for searchable_token in searchable_tokens
                if len(searchable_token) >= 3
            ):
                return True
        return False

    @staticmethod
    def _exclusion_text(latest_message: str) -> str:
        normalized = RecommendationEngine._normalize(latest_message)
        segments = re.findall(
            r"(?:drop|remove|without|skip|exclude)\s+(.+?)(?:\badd\b|\bfinal\b|[.;]|$)",
            normalized,
        )
        if not segments:
            return normalized
        return " ".join(f"drop {segment}" for segment in segments)

    @staticmethod
    def _tokens(value: str) -> list[str]:
        ignored_tokens = {
            "and",
            "the",
            "new",
            "level",
            "assessment",
            "engineer",
            "assistant",
        }
        return [
            token
            for token in RecommendationEngine._normalize(value).split()
            if token and token not in ignored_tokens
        ]

    @staticmethod
    def _normalize(value: Any) -> str:
        normalized = str(value).casefold().replace("centre", "center")
        normalized = normalized.replace("&", " and ")
        normalized = normalized.replace("/", " ")
        normalized = re.sub(r"[^a-z0-9+#.]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
