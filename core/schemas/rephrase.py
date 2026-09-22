from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Change(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    type: NonEmpty = Field(max_length=80)
    description: NonEmpty = Field(max_length=2000)


class RephraseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    rewritten_text: NonEmpty = Field(max_length=24000)
    changes: list[Change] = Field(max_length=40)
