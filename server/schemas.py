"""请求体模型。字段与 core/store.py 的表结构一一对应（附表 1-8 / S2012）。"""
from typing import Any

from pydantic import BaseModel, Field


class CreateEvent(BaseModel):
    event_id: str
    title: str
    lead: str = ""


class EventUpdate(BaseModel):
    title: str | None = None
    lead: str | None = None
    place_type: str | None = None
    region: str | None = None
    address: str | None = None
    occurred_at: str | None = None
    received_at: str | None = None
    exposure_at: str | None = None
    investigation_end: str | None = None
    cross_region: int | None = None
    is_foodborne: str | None = None
    source_region: str | None = None
    source_place_type: str | None = None
    source_address: str | None = None
    population_size: int | None = None
    population_basis: str | None = None
    population_known: int | None = None
    study_design: str | None = None
    timezone: str | None = None
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
    probable: dict[str, Any] = Field(default_factory=dict)
    confirmed: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)


class PersonIn(BaseModel):
    id: str
    name: str | None = None
    age: float | None = None
    sex: str | None = None
    occupation: str | None = None
    population: str | None = None
    location: str | None = None
    onset: str | None = None
    recovery: str | None = None
    illness_status: str | None = None
    symptoms: dict[str, bool | None] = Field(default_factory=dict)
    hospitalized: int = 0
    died: int = 0
    hospital: str | None = None
    diagnosis: str | None = None
    adjudication: dict | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class ExposureIn(BaseModel):
    id: str
    person_id: str
    meal_id: str | None = None
    meal_at: str | None = None
    food_id: str | None = None
    consumed: int | None = None
    ate_at: str | None = None
    incubation_anchor: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class FoodIn(BaseModel):
    id: str
    category: str | None = None
    meal_id: str | None = None
    source: str | None = None
    process_method: str | None = None
    package: str | None = None
    notes: str = ""


class SampleIn(BaseModel):
    id: str
    category: str | None = None
    source: str | None = None
    person_id: str | None = None
    laboratory: str | None = None
    collected_at: str | None = None
    tests: list = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class HygieneIn(BaseModel):
    id: str
    aspect: str | None = None
    item: str | None = None
    finding: str | None = None
    problem: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class ControlIn(BaseModel):
    id: str
    measure: str | None = None
    target: str | None = None
    implemented: str | None = None
    date: str | None = None
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
    status: str = "unknown"
    statement: str = ""
    reason: str = ""
    limitations: str = ""
    link: str | None = None
    factor: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class StageIn(BaseModel):
    stage: str
    status: str = "pending"
    note: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
