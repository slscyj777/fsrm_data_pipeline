import pytest
import polars as pl
from dataclasses import dataclass, field
from pipeline.load import check_duplicate_dates



@dataclass
class DuplicateDatesTestCase:
    test_id: str
    existing_dates: list[str]
    new_dates: list[str]
    expected: bool

    id: str = field(init=False)

    def __post_init__(self):
        self.id = self.test_id

test_cases = [
    DuplicateDatesTestCase(
    test_id ="duplicate_date",
    existing_dates=["2026-06-11", "2026-06-12", "2026-06-13"],
    new_dates=["2026-06-11"],
    expected=True
    ),
    DuplicateDatesTestCase(
    test_id ="no_duplicate_date",
    existing_dates=["2026-06-11", "2026-06-12", "2026-06-13"],
    new_dates=["2026-06-30"],
    expected=False
    ),
    DuplicateDatesTestCase(
    test_id ="mixed_dates",
    existing_dates=["2026-06-11", "2026-06-12"],
    new_dates=["2026-06-12", "2026-06-30"],
    expected=True
    ),
    DuplicateDatesTestCase(
    test_id ="empty_new_df",
    existing_dates=["2026-06-11", "2026-06-12"],
    new_dates=[],
    expected=False
    ),
    DuplicateDatesTestCase(
    test_id ="empty_existing_df",
    existing_dates=[],
    new_dates=["2026-06-30"],
    expected=False
    ),
]


@pytest.mark.parametrize(
    "test_case", test_cases, ids=lambda tc: tc.id
)

def test_check_duplicate_dates(test_case: DuplicateDatesTestCase):
    existing_df = pl.DataFrame({
        "column_1": ["data"] * len(test_case.existing_dates),
        "stock_date": test_case.existing_dates,
    })
    new_df = pl.DataFrame({
        "column_1": ["data"] * len(test_case.new_dates),
        "stock_date": test_case.new_dates,
    })

    assert check_duplicate_dates(existing_df, new_df) is test_case.expected