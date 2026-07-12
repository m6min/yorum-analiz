from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SentimentLabel(Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

@dataclass
class SentimentScore:
    """Sentiment analysis result with scores."""
    label: SentimentLabel
    confidence: float
    positive_score: float
    negative_score: float
    neutral_score: float

@dataclass
class SentimentAnalysis:
    """Complete sentiment analysis schema."""
    text: str
    sentiment: SentimentScore
    tokens: Optional[list[str]] = None
    metadata: Optional[dict] = None
