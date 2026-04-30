"""Pydantic models for the extract-vocab API."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DictionaryConfigRequest(BaseModel):
    """Request to update dictionary configuration."""

    model_config = ConfigDict(populate_by_name=True)

    provider: Literal["bundled", "nikl"] = Field(
        ..., description="Dictionary provider to use"
    )
    api_key: Optional[str] = Field(
        default=None, description="NIKL API key (required if provider is 'nikl')"
    )


class DictionaryConfigResponse(BaseModel):
    """Response with current dictionary configuration."""

    model_config = ConfigDict(populate_by_name=True)

    provider: str = Field(..., description="Current provider: 'bundled' or 'nikl'")
    api_key_set: bool = Field(
        ..., description="Whether an API key is configured for NIKL"
    )
    bundled_available: bool = Field(
        ..., description="Whether bundled dictionary is available"
    )
    bundled_entry_count: int = Field(
        ..., description="Number of entries in bundled dictionary"
    )
    bundled_source: str = Field(
        ..., description="Source of bundled dictionary data"
    )


class ExtractVocabRequest(BaseModel):
    """Request to extract vocabulary from Korean text."""

    model_config = ConfigDict(populate_by_name=True)

    text: str = Field(..., min_length=1, description="Korean passage to extract vocabulary from")
    target_level: Literal["ANY", "TOPIK_II_3", "TOPIK_II_4", "TOPIK_II_5", "TOPIK_II_6"] = Field(
        default="ANY", alias="targetLevel", description="Target TOPIK II level for vocabulary filtering"
    )
    word_count: int = Field(
        default=20, alias="wordCount", ge=1, le=100, description="Number of vocabulary items to return"
    )
    include_sentence_translation: bool = Field(
        default=True, alias="includeSentenceTranslation",
        description="Include English translation of source sentences",
    )


class VocabCard(BaseModel):
    """A single vocabulary study card."""

    model_config = ConfigDict(populate_by_name=True)

    lemma: str = Field(..., description="Dictionary form of the word")
    display: str = Field(..., description="Display form for the card")
    pos: Literal["noun", "verb", "adjective", "adverb", "phrase", "unknown"] = Field(
        ..., description="Part of speech"
    )
    english_glosses: list[str] = Field(
        default_factory=list, alias="englishGlosses", description="English translations"
    )
    korean_definition: Optional[str] = Field(
        default=None, alias="koreanDefinition", description="Korean definition"
    )
    source_sentence: str = Field(
        ..., alias="sourceSentence", description="Korean sentence containing the word"
    )
    source_sentence_translation: Optional[str] = Field(
        default=None, alias="sourceSentenceTranslation",
        description="English translation of source sentence",
    )
    # Shortest useful Korean fragment containing the target word
    source_fragment: str = Field(
        ..., alias="sourceFragment", description="Shortest useful Korean fragment containing the word"
    )
    source_fragment_translation: Optional[str] = Field(
        default=None, alias="sourceFragmentTranslation",
        description="English translation of the Korean source fragment",
    )
    # Pre-formatted compact study line for display and copy
    study_line: str = Field(
        ..., alias="studyLine",
        description="Compact study line: '(glosses) Korean fragment. (lemma) = English translation.'",
    )
    # CSV export fields
    csv_front: str = Field(
        ..., alias="csvFront",
        description="CSV front column: '(glosses) Korean fragment. (lemma)'",
    )
    csv_back: str = Field(
        ..., alias="csvBack",
        description="CSV back column: 'English translation of the Korean source fragment.'",
    )
    level: Optional[
        Literal[
            "TOPIK_I_1", "TOPIK_I_2", "TOPIK_II_3", "TOPIK_II_4", "TOPIK_II_5", "TOPIK_II_6", "unknown"
        ]
    ] = Field(default=None, description="Estimated TOPIK level")
    difficulty_score: float = Field(
        ..., alias="difficultyScore", ge=1.0, le=6.0,
        description="Difficulty score 1-6 (1-2 beginner, 3-4 intermediate, 5-6 advanced)",
    )
    frequency_in_text: int = Field(
        ..., alias="frequencyInText", ge=1,
        description="How many times this lemma appears in the text",
    )
    reason: str = Field(..., description="Why this word was selected")


class ExtractMeta(BaseModel):
    """Metadata about the extraction result."""

    model_config = ConfigDict(populate_by_name=True)

    input_length: int = Field(
        ..., alias="inputLength", description="Length of input text in characters"
    )
    candidate_count: int = Field(
        ..., alias="candidateCount", description="Total candidates before ranking"
    )
    returned_count: int = Field(
        ..., alias="returnedCount", description="Number of cards returned"
    )
    dictionary_provider: str = Field(
        default="NIKL", alias="dictionaryProvider", description="Dictionary provider used"
    )
    # Debug metadata (not shown in normal UI)
    selected_target_level: Optional[str] = Field(
        default=None, alias="selectedTargetLevel",
        description="Target level selected by user",
    )
    candidate_count_before_filtering: Optional[int] = Field(
        default=None, alias="candidateCountBeforeFiltering",
        description="Candidates before level filtering",
    )
    level_distribution: Optional[dict[str, int]] = Field(
        default=None, alias="levelDistribution",
        description="Distribution of candidate levels",
    )


class ExtractVocabResponse(BaseModel):
    """Response from the extract-vocab endpoint."""

    cards: list[VocabCard] = Field(..., description="Extracted vocabulary cards")
    meta: ExtractMeta = Field(..., description="Extraction metadata")
