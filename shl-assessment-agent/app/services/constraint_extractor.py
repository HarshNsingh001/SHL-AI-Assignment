import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar
from app.models.constraints import (
    AssessmentPurpose,
    ConstraintExtractionResult,
    EmploymentType,
    HiringConstraints,
    JobLevel,
    MissingInformation,
    Seniority,
    WorkLocation,
)
from app.models.conversation import ConversationState


@dataclass(frozen=True)
class ConstraintExtractor:

    ROLE_SYNONYMS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("backend developer", "Backend Engineer"),
        ("backend engineer", "Backend Engineer"),
        ("software developer", "Software Engineer"),
        ("software engineer", "Software Engineer"),
        ("java engineer", "Software Engineer"),
        ("java developer", "Software Engineer"),
        ("rust engineer", "Software Engineer"),
        ("rust developer", "Software Engineer"),
        ("python engineer", "Software Engineer"),
        ("python developer", "Software Engineer"),
        ("financial analyst", "Financial Analyst"),
        ("finance analyst", "Financial Analyst"),
        ("contact center agent", "Contact Center Agent"),
        ("contact center advisor", "Contact Center Agent"),
        ("customer support agent", "Customer Support Agent"),
        ("customer service agent", "Customer Support Agent"),
        ("sales manager", "Sales Manager"),
        ("sales representative", "Sales Representative"),
        ("account executive", "Account Executive"),
        ("executive leadership", "Executive Leadership"),
        ("plant operator", "Plant Operator"),
        ("production operator", "Plant Operator"),
        ("operations supervisor", "Operations Supervisor"),
        ("engineer", "Engineer"),
        ("analyst", "Analyst"),
        ("manager", "Manager"),
        ("management trainee", "Graduate Trainee"),
        ("graduate trainee", "Graduate Trainee"),
        ("graduate program", "Graduate Trainee"),
        ("trainee", "Graduate Trainee"),
        ("admin assistant", "Admin Assistant"),
        ("administrative assistant", "Admin Assistant"),
        ("sales organization", "Sales Representative"),
        ("sales team", "Sales Representative"),
        ("sales force", "Sales Representative"),
        ("leadership hiring", "Executive Leadership"),
    )
    JOB_LEVEL_SYNONYMS: ClassVar[tuple[tuple[str, JobLevel], ...]] = (
        ("graduate trainee", JobLevel.GRADUATE),
        ("management trainee", JobLevel.GRADUATE),
        ("campus hire", JobLevel.GRADUATE),
        ("campus hiring", JobLevel.GRADUATE),
        ("graduate program", JobLevel.GRADUATE),
        ("graduate", JobLevel.GRADUATE),
        ("entry level", JobLevel.ENTRY_LEVEL),
        ("entry-level", JobLevel.ENTRY_LEVEL),
        ("junior", JobLevel.ENTRY_LEVEL),
        ("mid level", JobLevel.MID_LEVEL),
        ("mid-level", JobLevel.MID_LEVEL),
        ("experienced", JobLevel.MID_LEVEL),
        ("senior", JobLevel.SENIOR),
        ("manager", JobLevel.MANAGER),
        ("executive", JobLevel.EXECUTIVE),
    )
    INDUSTRY_SYNONYMS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("financial services", "Finance"),
        ("financial", "Finance"),
        ("finance", "Finance"),
        ("banking", "Finance"),
        ("accounting", "Finance"),
        ("contact center", "Customer Support"),
        ("customer support", "Customer Support"),
        ("customer service", "Customer Support"),
        ("sales", "Sales"),
        ("manufacturing", "Manufacturing"),
        ("production", "Manufacturing"),
        ("factory", "Manufacturing"),
        ("plant", "Manufacturing"),
        ("software", "Technology"),
        ("technology", "Technology"),
        ("backend", "Technology"),
        ("developer", "Technology"),
        ("engineer", "Technology"),
    )
    SKILL_SYNONYMS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("javascript", "JavaScript"),
        ("typescript", "TypeScript"),
        ("kubernetes", "Kubernetes"),
        ("customer service", "Customer Service"),
        ("financial analysis", "Financial Analysis"),
        ("problem solving", "Problem Solving"),
        ("communication", "Communication"),
        ("leadership", "Leadership"),
        ("accounting", "Accounting"),
        ("operations", "Operations"),
        ("python", "Python"),
        ("java", "Java"),
        ("rust", "Rust"),
        ("sql", "SQL"),
        ("aws", "AWS"),
        ("react", "React"),
        ("node", "Node.js"),
        ("docker", "Docker"),
        ("c++", "C++"),
        ("c#", "C#"),
        (".net", ".NET"),
        ("sales", "Sales"),
        ("safety", "Safety"),
    )
    LANGUAGE_SYNONYMS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("mandarin", "Mandarin"),
        ("portuguese", "Portuguese"),
        ("english", "English"),
        ("spanish", "Spanish"),
        ("french", "French"),
        ("german", "German"),
        ("hindi", "Hindi"),
        ("japanese", "Japanese"),
        ("arabic", "Arabic"),
    )
    ASSESSMENT_TYPE_SYNONYMS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("customer service", "Customer Service"),
        ("situational judgement", "Situational Judgement"),
        ("situational judgment", "Situational Judgement"),
        ("personality", "Personality"),
        ("behavioral", "Behavioral"),
        ("behavioural", "Behavioral"),
        ("cognitive", "Cognitive"),
        ("technical", "Technical"),
        ("coding", "Coding"),
        ("language", "Language"),
        ("leadership", "Leadership"),
        ("sales", "Sales"),
    )
    EMPLOYMENT_TYPE_SYNONYMS: ClassVar[tuple[tuple[str, EmploymentType], ...]] = (
        ("full time", EmploymentType.FULL_TIME),
        ("full-time", EmploymentType.FULL_TIME),
        ("part time", EmploymentType.PART_TIME),
        ("part-time", EmploymentType.PART_TIME),
        ("contract", EmploymentType.CONTRACT),
        ("internship", EmploymentType.INTERNSHIP),
        ("intern", EmploymentType.INTERNSHIP),
    )
    WORK_LOCATION_SYNONYMS: ClassVar[tuple[tuple[str, WorkLocation], ...]] = (
        ("remote", WorkLocation.REMOTE),
        ("hybrid", WorkLocation.HYBRID),
        ("on site", WorkLocation.ONSITE),
        ("onsite", WorkLocation.ONSITE),
        ("in office", WorkLocation.ONSITE),
    )
    PURPOSE_SYNONYMS: ClassVar[tuple[tuple[str, AssessmentPurpose], ...]] = (
        ("campus hire", AssessmentPurpose.HIRING),
        ("campus hiring", AssessmentPurpose.HIRING),
        ("hiring", AssessmentPurpose.HIRING),
        ("hire", AssessmentPurpose.HIRING),
        ("recruiting", AssessmentPurpose.HIRING),
        ("recruitment", AssessmentPurpose.HIRING),
        ("screening", AssessmentPurpose.SCREENING),
        ("screen", AssessmentPurpose.SCREENING),
        ("development", AssessmentPurpose.DEVELOPMENT),
        ("promotion", AssessmentPurpose.PROMOTION),
    )
    PREFERRED_INDICATORS: ClassVar[tuple[str, ...]] = (
        "preferred",
        "nice to have",
        "ideally",
    )
    LEADERSHIP_INDICATORS: ClassVar[tuple[str, ...]] = (
        "leadership",
        "leader",
        "manager",
        "supervisor",
        "executive",
        "head of",
    )
    CUSTOMER_FACING_INDICATORS: ClassVar[tuple[str, ...]] = (
        "contact center",
        "customer support",
        "customer service",
        "sales",
        "account executive",
        "customer facing",
    )
    TECHNICAL_ROLE_INDICATORS: ClassVar[tuple[str, ...]] = (
        "engineer",
        "developer",
        "backend",
        "software",
        "technical",
        "coding",
        "java",
        "python",
        "rust",
        "sql",
        "aws",
    )

    @staticmethod
    def _stem_text(text: str) -> str:
        excluded_words = {
            "sales",
            "statistics",
            "process",
            "business",
            "analysis",
            "class",
            "glass",
            "as",
            "us",
            "is",
        }
        words = text.split()
        stemmed = []
        for word in words:
            word_clean = word.rstrip(".,;:!?()")
            suffix = word[len(word_clean) :]
            stemmed_word = word_clean
            if word_clean.endswith("s") and word_clean not in excluded_words:
                if word_clean.endswith("ies"):
                    stemmed_word = word_clean[:-3] + "y"
                elif word_clean.endswith("es") and word_clean[:-2].endswith(
                    ("ch", "sh", "x", "s", "z")
                ):
                    stemmed_word = word_clean[:-2]
                else:
                    stemmed_word = word_clean[:-1]
            stemmed.append(stemmed_word + suffix)
        return " ".join(stemmed)

    def extract(
        self,
        conversation_state: ConversationState,
        latest_user_message: str | None = None,
    ) -> ConstraintExtractionResult:
        text = self._build_source_text(conversation_state, latest_user_message)
        normalized_text = self._normalize_text(text)
        stemmed_text = self._stem_text(normalized_text)

        context = conversation_state.context
        existing_languages = self._empty_to_none(context.languages)
        existing_assessment_types = self._empty_to_none(
            context.assessment_types_requested
        )
        extracted_required, extracted_preferred = self._extract_skills(stemmed_text)

        constraints = HiringConstraints(
            role=self._extract_role(stemmed_text) or context.current_role,
            job_level=(
                self._extract_job_level(stemmed_text)
                or self._normalize_job_level(context.job_level)
            ),
            experience_level=(
                self._extract_experience_level(stemmed_text) or context.experience_level
            ),
            industry=self._extract_industry(stemmed_text) or context.industry,
            employment_type=self._extract_employment_type(stemmed_text),
            required_skills=self._merge_optional_strings(
                context.required_skills,
                extracted_required,
            ),
            preferred_skills=extracted_preferred,
            languages=self._merge_optional_strings(
                existing_languages,
                self._extract_languages(stemmed_text),
            ),
            assessment_types=self._merge_optional_strings(
                existing_assessment_types,
                self._extract_assessment_types(stemmed_text),
            ),
            purpose=self._extract_purpose(stemmed_text),
            candidate_volume=self._extract_candidate_volume(stemmed_text),
            work_location=self._extract_work_location(stemmed_text),
            seniority=self._extract_seniority(stemmed_text),
            leadership_required=self._extract_boolean_presence(
                stemmed_text,
                self.LEADERSHIP_INDICATORS,
            ),
            technical_role=self._extract_boolean_presence(
                stemmed_text,
                self.TECHNICAL_ROLE_INDICATORS,
            ),
            customer_facing=self._extract_boolean_presence(
                stemmed_text,
                self.CUSTOMER_FACING_INDICATORS,
            ),
            additional_requirements=self._extract_additional_requirements(text),
        )

        missing_information = self._build_missing_information(constraints)
        warnings = self._build_warnings(stemmed_text, missing_information)
        confidence = self._calculate_confidence(
            constraints, missing_information, stemmed_text
        )

        return ConstraintExtractionResult(
            constraints=constraints,
            confidence=confidence,
            missing_information=missing_information,
            warnings=warnings,
            metadata={"source": "deterministic"},
        )

    def _build_source_text(
        self,
        conversation_state: ConversationState,
        latest_user_message: str | None,
    ) -> str:
        segments = [message.content for message in conversation_state.messages]
        if conversation_state.conversation_summary:
            segments.append(conversation_state.conversation_summary)
        if latest_user_message:
            segments.append(latest_user_message)
        return " ".join(segment for segment in segments if segment.strip())

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = text.casefold()
        normalized = normalized.replace("centre", "center")
        normalized = normalized.replace("/", " ")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def _extract_role(self, normalized_text: str) -> str | None:
        for phrase, role in self.ROLE_SYNONYMS:
            if self._contains_phrase(normalized_text, phrase):
                return role
        return None

    def _extract_job_level(self, normalized_text: str) -> JobLevel | None:
        for phrase, job_level in self.JOB_LEVEL_SYNONYMS:
            if self._contains_phrase(normalized_text, phrase):
                return job_level
        return None

    @staticmethod
    def _normalize_job_level(job_level: str | None) -> JobLevel | None:
        if job_level is None:
            return None
        normalized = job_level.casefold().replace("-", " ")
        for enum_value in JobLevel:
            if enum_value.value.casefold() == normalized:
                return enum_value
        return None

    def _extract_seniority(self, normalized_text: str) -> Seniority | None:
        job_level = self._extract_job_level(normalized_text)
        if job_level is None:
            return None
        return Seniority(job_level.value)

    @staticmethod
    def _extract_experience_level(normalized_text: str) -> str | None:
        match = re.search(r"\b(\d{1,2})\+?\s+years?\b", normalized_text)
        if match:
            return f"{match.group(1)} years"
        if "no experience" in normalized_text:
            return "No experience"
        return None

    def _extract_industry(self, normalized_text: str) -> str | None:
        for phrase, industry in self.INDUSTRY_SYNONYMS:
            if self._contains_phrase(normalized_text, phrase):
                return industry
        return None

    def _extract_employment_type(
        self,
        normalized_text: str,
    ) -> EmploymentType | None:
        for phrase, employment_type in self.EMPLOYMENT_TYPE_SYNONYMS:
            if self._contains_phrase(normalized_text, phrase):
                return employment_type
        return None

    def _extract_work_location(self, normalized_text: str) -> WorkLocation | None:
        for phrase, work_location in self.WORK_LOCATION_SYNONYMS:
            if self._contains_phrase(normalized_text, phrase):
                return work_location
        return None

    def _extract_purpose(self, normalized_text: str) -> AssessmentPurpose | None:
        for phrase, purpose in self.PURPOSE_SYNONYMS:
            if self._contains_phrase(normalized_text, phrase):
                return purpose
        return None

    def _extract_skills(
        self,
        normalized_text: str,
    ) -> tuple[list[str] | None, list[str] | None]:
        required: list[str] = []
        preferred: list[str] = []

        for phrase, skill in self.SKILL_SYNONYMS:
            if not self._contains_phrase(normalized_text, phrase):
                continue
            if self._appears_as_preferred(normalized_text, phrase):
                preferred.append(skill)
            else:
                required.append(skill)

        return self._empty_to_none(required), self._empty_to_none(preferred)

    def _appears_as_preferred(self, stemmed_text: str, phrase: str) -> bool:
        stemmed_phrase = self._stem_text(phrase.casefold())
        for indicator in self.PREFERRED_INDICATORS:
            stemmed_indicator = self._stem_text(indicator.casefold())
            pattern = rf"{re.escape(stemmed_indicator)}[^.]*{re.escape(stemmed_phrase)}"
            if re.search(pattern, stemmed_text):
                return True
        return False

    def _extract_languages(self, normalized_text: str) -> list[str] | None:
        languages = [
            language
            for phrase, language in self.LANGUAGE_SYNONYMS
            if self._contains_phrase(normalized_text, phrase)
        ]
        return self._empty_to_none(languages)

    def _extract_assessment_types(self, normalized_text: str) -> list[str] | None:
        assessment_types = [
            assessment_type
            for phrase, assessment_type in self.ASSESSMENT_TYPE_SYNONYMS
            if self._contains_phrase(normalized_text, phrase)
        ]
        return self._empty_to_none(assessment_types)

    @staticmethod
    def _extract_candidate_volume(normalized_text: str) -> int | None:
        patterns = (
            r"\b(?:hire|hiring|screen|screening)\s+(\d{1,6})\b",
            r"\b(\d{1,6})\s+(?:candidates?|applicants?|hires?|people)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized_text)
            if match:
                return int(match.group(1))
        return None

    def _extract_boolean_presence(
        self,
        normalized_text: str,
        indicators: Iterable[str],
    ) -> bool | None:
        for indicator in indicators:
            if self._contains_phrase(normalized_text, indicator):
                return True
        return None

    @staticmethod
    def _extract_additional_requirements(text: str) -> list[str] | None:
        matches = re.findall(
            r"\b(?:must have|requires|required)\s+([^.;]+)",
            text,
            flags=re.IGNORECASE,
        )
        requirements = [match.strip() for match in matches if match.strip()]
        return ConstraintExtractor._empty_to_none(requirements)

    def _contains_phrase(self, stemmed_text: str, phrase: str) -> bool:
        stemmed_phrase = self._stem_text(phrase.casefold().replace("centre", "center"))
        pattern = rf"(?<![a-z0-9]){re.escape(stemmed_phrase)}(?![a-z0-9])"
        return re.search(pattern, stemmed_text) is not None

    @staticmethod
    def _merge_optional_strings(
        first: Iterable[str] | None,
        second: Iterable[str] | None,
    ) -> list[str] | None:
        values: list[str] = []
        for item in list(first or []) + list(second or []):
            if item not in values:
                values.append(item)
        return ConstraintExtractor._empty_to_none(values)

    @staticmethod
    def _empty_to_none(values: Iterable[str] | None) -> list[str] | None:
        if values is None:
            return None
        normalized_values = [value for value in values if value]
        if not normalized_values:
            return None
        return normalized_values

    @staticmethod
    def _build_missing_information(
        constraints: HiringConstraints,
    ) -> MissingInformation:
        missing_fields: list[str] = []
        questions: list[str] = []

        if constraints.role is None:
            missing_fields.append("role")
            questions.append("Which role are you hiring for?")
        if constraints.seniority is None:
            missing_fields.append("seniority")
            questions.append("What seniority or job level should be targeted?")
        if constraints.purpose is None:
            missing_fields.append("purpose")
            questions.append("What is the assessment purpose?")

        return MissingInformation(
            missing_fields=missing_fields,
            questions=questions,
            is_complete=not missing_fields,
        )

    @staticmethod
    def _build_warnings(
        normalized_text: str,
        missing_information: MissingInformation,
    ) -> list[str]:
        warnings: list[str] = []
        if not normalized_text:
            warnings.append("No source text was available for extraction.")
        for missing_field in missing_information.missing_fields:
            warnings.append(f"Missing {missing_field}.")
        return warnings

    @staticmethod
    def _count_role_signals(normalized_text: str, role: str) -> int:
        role_keywords = {
            "Software Engineer": [
                "engineer",
                "developer",
                "coder",
                "programmer",
                "software",
                "coding",
                "programming",
                "java",
                "python",
                "rust",
            ],
            "Backend Engineer": [
                "engineer",
                "developer",
                "coder",
                "programmer",
                "software",
                "backend",
                "java",
                "python",
                "rust",
                "spring",
                "sql",
                "api",
            ],
            "Financial Analyst": [
                "analyst",
                "financial",
                "finance",
                "accounting",
                "statistics",
            ],
            "Contact Center Agent": [
                "agent",
                "advisor",
                "contact",
                "center",
                "centre",
                "customer",
                "support",
                "service",
                "phone",
            ],
            "Customer Support Agent": [
                "agent",
                "customer",
                "support",
                "service",
                "help",
                "phone",
            ],
            "Sales Representative": [
                "representative",
                "sales",
                "rep",
                "selling",
                "force",
                "team",
                "organization",
            ],
            "Sales Manager": ["manager", "sales", "leader", "team", "force"],
            "Executive Leadership": [
                "executive",
                "leadership",
                "cxo",
                "director",
                "vp",
                "president",
                "chief",
            ],
            "Plant Operator": [
                "operator",
                "plant",
                "manufacturing",
                "industrial",
                "safety",
                "dependability",
            ],
            "Graduate Trainee": [
                "trainee",
                "graduate",
                "program",
                "scheme",
                "intern",
                "management",
            ],
        }
        keywords = role_keywords.get(role, [])
        return sum(kw in normalized_text for kw in keywords)

    @classmethod
    def _calculate_confidence(
        cls,
        constraints: HiringConstraints,
        missing_information: MissingInformation,
        stemmed_text: str = "",
    ) -> float:
        field_values = [
            constraints.role,
            constraints.job_level,
            constraints.experience_level,
            constraints.industry,
            constraints.employment_type,
            constraints.required_skills,
            constraints.preferred_skills,
            constraints.languages,
            constraints.assessment_types,
            constraints.purpose,
            constraints.candidate_volume,
            constraints.work_location,
            constraints.seniority,
            constraints.leadership_required,
            constraints.technical_role,
            constraints.customer_facing,
            constraints.additional_requirements,
        ]
        populated_fields = sum(value is not None for value in field_values)
        confidence = min(0.95, 0.2 + (populated_fields * 0.05))

        if constraints.role and stemmed_text:
            role_signals = cls._count_role_signals(stemmed_text, constraints.role)
            if role_signals >= 2:
                confidence = min(0.95, confidence + (role_signals - 1) * 0.05)

        if "role" in missing_information.missing_fields:
            confidence = min(confidence, 0.65)
        if "seniority" in missing_information.missing_fields:
            confidence = min(confidence, 0.8)
        return round(confidence, 2)
