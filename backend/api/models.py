"""Pydantic models for the extract-vocab API."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    level: Optional[
        Literal[
            "TOPIK_I_1", "TOPIK_I_2", "TOPIK_II_3", "TOPIK_II_4", "TOPIK_II_5", "TOPIK_II_6", "unknown"
        ]
    ] = Field(default=None, description="Estimated TOPIK level")
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


class ExtractVocabResponse(BaseModel):
    """Response from the extract-vocab endpoint."""

    cards: list[VocabCard] = Field(..., description="Extracted vocabulary cards")
    meta: ExtractMeta = Field(..., description="Extraction metadata")
