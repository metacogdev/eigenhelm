"""Package init with re-exports for benchmark categorization testing."""

from .implementation import binary_search
from .schema_models import ProjectModel, UserModel

__all__ = ["binary_search", "UserModel", "ProjectModel"]
