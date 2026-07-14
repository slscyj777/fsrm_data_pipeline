import pytest
import polars as pl
from dataclasses import dataclass, field
from math import ceil
from pipeline.transform import (
    branch_code_to_int,
    map_base_unit_to_sku,
    map_forecast_to_daily,
    map_sermsuk_to_TBL_WH_select_columns,
    rearrange_columns,
    rename_normalize_stock_columns,
    total_shippment_as_crates,
    total_stock_as_crates,
    transform_consolidate_forecasts,
)

@dataclass
class NormalizeStockTestCase:
    test_id: str
    raw: str | None
    expected: float
    id: str = field(init=False)

    def __post_init__(self):
        self.id = self.test_id

normalize_stock_cases = [
    NormalizeStockTestCase("dash_becomes_zero", "-", 0.0),
    NormalizeStockTestCase("empty_string_becomes_zero", "", 0.0),
    NormalizeStockTestCase("whitespace_becomes_zero", " ", 0.0),
    NormalizeStockTestCase("null_becomes_zero", None, 0.0),
    NormalizeStockTestCase("integer_string_parses", "5", 5.0),
    NormalizeStockTestCase("decimal_string_parses", "10.5", 10.5),
    NormalizeStockTestCase("surrounding_whitespace_stripped", "  20  ", 20.0),
]


@pytest.mark.parametrize("test_case", normalize_stock_cases, ids=lambda tc: tc.id)

def test_rename_normalize(test_case: NormalizeStockTestCase):

    df = pl.DataFrame({
        "raw_stock": [test_case.raw],
        "raw_ship": [test_case.raw]
    })

    result = rename_normalize_stock_columns(
        df,
        column_mapping={"raw_stock": "stock_case", "raw_ship": "shippment_case"},
        stock_columns=["stock_case"],
        ship_columns=["shippment_case"],
    )

    assert result["stock_case"][0] == pytest.approx(test_case.expected)
    assert result["shippment_case"][0] == pytest.approx(test_case.expected)
    assert result["stock_case"].dtype == pl.Float64

@dataclass
class BranchCodeExtractTestCase:
    test_id: str
    raw_branch_code: str
    expected_branch_code: int
    id: str = field(init=False)
 
    def __post_init__(self):
        self.id = self.test_id

branch_code_extract_cases = [
    BranchCodeExtractTestCase("sfc_data_format", "3202 - ชนบุรี", 3202),
    BranchCodeExtractTestCase("number_in_branch_name", "3202 - ชนบุรี 2", 3202),
    BranchCodeExtractTestCase("concacted_name", "3202ชนบุรี", 3202),
    BranchCodeExtractTestCase("leading_zeros", "045 Warehouse", 45)

]

class TestTransformConsolidateForecasts:
    @pytest.mark.parametrize("test_case", branch_code_extract_cases, ids=lambda tc: tc.id)
    def test_extracts_branch_code(self, test_case: BranchCodeExtractTestCase):
        df_beer = pl.DataFrame({
            "branch_code": [test_case.raw_branch_code],
            "category": ["beer"],
            "SKU": ["SKU1"],
            "forecast": [10.0],
        })
        df_spirits = pl.DataFrame(schema=df_beer.schema)

        result = transform_consolidate_forecasts(df_beer, df_spirits)
    
        assert result["branch_code"][0] == test_case.expected_branch_code
        assert result["branch_code"].dtype == pl.Int64
            
    def test_transform_consolidate_forecasts_sums_matching_groups(self, normalize: float = 1.2):
        df_beer = pl.DataFrame({
            "branch_code": ["3202 Bangkok"],
            "category": ["soda"],
            "SKU": ["SKU1"],
            "forecast": [10.0],
        })
        df_spirits = pl.DataFrame({
            "branch_code": ["3202 Bangkok"],
            "category": ["soda"],
            "SKU": ["SKU1"],
            "forecast": [5.0],
        })
    
        result = transform_consolidate_forecasts(df_beer, df_spirits, normalize)

        assert result["forecast"][0] == ceil(round(15.0 / normalize, 10))
        assert result.height == 1
        assert result["forecast"].dtype == pl.Int64