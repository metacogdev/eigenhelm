import numpy as np
from pathlib import Path
from typing import Dict, Any

from eigenhelm.models import NPZ_KEYS

def load_npz_model_arrays(path: str | Path, allow_pickle: bool = True) -> Dict[str, Any]:
    """Load an .npz model and extract the required keys."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Eigenspace model not found: {path}")

    data = np.load(path, allow_pickle=allow_pickle)

    required = (NPZ_KEYS.PROJECTION_MATRIX, NPZ_KEYS.MEAN, NPZ_KEYS.STD)
    for key in required:
        if key not in data:
            raise KeyError(f"Missing key {key!r} in eigenspace model {path}")

    return data
