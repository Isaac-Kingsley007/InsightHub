"""Single-customer churn prediction API contract."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    Account_Age_Days: int = Field(ge=0)
    Login_Frequency: Literal["Daily", "Weekly", "Rarely"]
    Daily_Usage_Mins: float = Field(ge=0, allow_inf_nan=False)


class ChurnResult(BaseModel):
    predicted_churn: Literal[0, 1]
    churn_probability: float = Field(ge=0, le=1)
