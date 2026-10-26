"""Seed datasets registered in this build, in dependency order (parents first).

`/ready` checks every dataset listed here; `app.db.seed` loads them.
"""

from typing import Final

from app.data import finscope_2024, reference, seasonal, synthetic_households, vulnerability
from app.data.registry import Dataset

DATASETS: Final[tuple[Dataset, ...]] = (
    *reference.DATASETS,
    *seasonal.DATASETS,
    *vulnerability.DATASETS,
    *synthetic_households.DATASETS,
    *finscope_2024.DATASETS,  # official published statistics (after `districts`)
)
