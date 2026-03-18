"""Schema/model definitions for benchmark categorization testing."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserModel:
    id: str
    name: str
    email: str


@dataclass(frozen=True)
class ProjectModel:
    id: str
    title: str
    owner_id: str
