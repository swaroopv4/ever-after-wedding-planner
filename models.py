from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent


class Settings(BaseModel):
    groq_api_key: str = Field(default="", repr=False, exclude=True)
    tavily_api_key: str = Field(default="", repr=False, exclude=True)
    model: str = "openai/gpt-oss-20b"

    @classmethod
    def load(cls, overrides: dict | None = None) -> Settings:
        # Read only this application's .env. Never mutate process-wide credentials.
        values = dict(dotenv_values(ROOT / ".env"))
        for key in ("GROQ_API_KEY", "TAVILY_API_KEY", "GROQ_MODEL"):
            if os.environ.get(key):
                values[key] = os.environ[key]
        values.update({k: v for k, v in (overrides or {}).items() if v})
        return cls(
            groq_api_key=(values.get("GROQ_API_KEY") or "").strip(),
            tavily_api_key=(values.get("TAVILY_API_KEY") or "").strip(),
            model=(values.get("GROQ_MODEL") or "openai/gpt-oss-20b").strip(),
        )

    @property
    def ready(self) -> bool:
        return bool(self.groq_api_key and self.tavily_api_key)


class WeddingBrief(BaseModel):
    couple: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=2, max_length=200)
    wedding_date: date
    guests: int = Field(ge=2, le=5000)
    budget: Decimal = Field(gt=0, le=100_000_000, decimal_places=2)
    currency: Literal["USD", "EUR", "GBP", "CAD", "AUD", "INR", "AED"] = "USD"
    event_scope: str = Field(default="Ceremony + reception", max_length=120)
    styles: list[str] = Field(default_factory=lambda: ["Garden", "Romantic"], max_length=10)
    priorities: list[str] = Field(
        default_factory=lambda: ["Guest experience", "Budget", "Venue shortlist"], max_length=10
    )
    must_haves: str = Field(default="", max_length=3000)
    constraints: str = Field(default="", max_length=3000)
    cultural_details: str = Field(default="", max_length=3000)
    tone: str = Field(default="Warm and practical", max_length=120)

    @field_validator("couple", "location", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("wedding_date")
    @classmethod
    def future_date(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Choose today or a future wedding date.")
        return value

    def to_prompt(self) -> str:
        return (
            f"Couple: {self.couple}\nLocation: {self.location}\n"
            f"Wedding date: {self.wedding_date.isoformat()}\nGuests: {self.guests}\n"
            f"Total budget: {self.currency} {self.budget:,.2f}\n"
            f"Event scope: {self.event_scope}\nStyles: {', '.join(self.styles) or 'Open'}\n"
            f"Priorities: {', '.join(self.priorities) or 'Balanced'}\n"
            f"Must-haves: {self.must_haves or 'Not specified'}\n"
            f"Constraints: {self.constraints or 'Not specified'}\n"
            f"Cultural and family details: {self.cultural_details or 'Not specified'}\n"
            f"Planner tone: {self.tone}\n"
        )


def sample_brief() -> WeddingBrief:
    return WeddingBrief(
        couple="Alex & Jordan",
        location="Santa Barbara, California",
        wedding_date=date.today() + timedelta(days=300),
        guests=100,
        budget=Decimal("45000.00"),
        must_haves="Outdoor ceremony, seasonal flowers, excellent food and a relaxed dance floor.",
        constraints="Step-free access; vegetarian options; keep the total within budget.",
        cultural_details="Make room for a meaningful family tradition during the ceremony.",
    )
