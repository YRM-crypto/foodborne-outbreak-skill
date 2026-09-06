"""请求体模型。字段与 core/store.py 的表结构一一对应。"""
from pydantic import BaseModel, Field


class CreateEvent(BaseModel):
    event_id: str
    title: str
    scenario: str = "closed-cohort"
    lead: str = ""


class EventUpdate(BaseModel):
    title: str | None = None
    lead: str | None = None
    received_at: str | None = None
    location: str | None = None
    data_cutoff: str | None = None
    timezone: str | None = None
    population_size: int | None = None
    population_complete: int | None = None
    population_basis: str | None = None
    urgent_flags: list[str] | None = None


class DefinitionIn(BaseModel):
    label: str = ""
    text: str = ""
    start: str = ""
    end: str = ""
    locations: list[str] = Field(default_factory=list)
    populations: list[str] = Field(default_factory=list)
    symptoms_any: list[str] = Field(default_factory=list)
    minimum_symptoms: int = 1
    require_lab: int = 0
    evidence_ids: list[str] = Field(default_factory=list)


class PersonIn(BaseModel):
    id: str
    age: float | None = None
    sex: str | None = None
    location: str | None = None
    population: str | None = None
    onset: str | None = None
    recovery: str | None = None
    observed_until: str | None = None
    illness_status: str | None = None
    symptoms: dict[str, bool | None] = Field(default_factory=dict)
    hospitalized: int = 0
    died: int = 0
    lab_eligible: int | None = None
    adjudication: dict | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class ExposureIn(BaseModel):
    id: str
    person_id: str
    meal_id: str | None = None
    food_id: str | None = None
    consumed: int | None = None
    ate_at: str | None = None
    incubation_anchor: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class SampleIn(BaseModel):
    id: str
    kind: str | None = None
    person_id: str | None = None
    source: str | None = None
    collected_at: str | None = None
    laboratory: str | None = None
    tests: list = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class EvidenceIn(BaseModel):
    id: str
    title: str = ""
    status: str = ""
    uri: str | None = None
    text: str = ""
    locator: str | None = None
    collected_at: str | None = None
    sha256: str | None = None
    notes: str = ""


class ConclusionIn(BaseModel):
    topic: str
    status: str = "hypothesis"
    statement: str = ""
    reason: str = ""
    limitations: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class ConfirmIn(BaseModel):
    node: str
    role: str = ""
    note: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    disposition: str = "confirmed"
