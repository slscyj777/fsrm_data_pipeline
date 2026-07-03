import pytest
import polars as pl
from datetime import date
from pathlib import Path
from dataclasses import dataclass, field
from pipeline.extract import extract_sermsuk_data

def create_mock_excel(path: Path, sheet_name: str):
    df = pl.DataFrame({
        "column_1": ["data1", "data2", "", "", "จิง"],
        "column_2": ["val1", "val2", " ", "", ""],
        "column_3": ["val3", "val4", " ", "", ""],
        "column_4": ["val3", "val4","   ", "", ""],
        "column_5": ["val3", "val4", "", "", "zzz"],
        "column_6": ["val3", "val4"," ", "", ""],
        "column_7": ["val3", "val4", " ", "", ""],
        "column_8": ["val3", "val4","", "", "xyz"]
    })
    df.write_excel(path, worksheet=sheet_name)


@dataclass
class SermsukTestCase:
    test_id: str
    folder_name: str
    files_to_create: list[str]
    files_param_count: int
    expected_error: type[Exception] | None = None
    error_match: str | None = None
    expected_branch_names: list[str] | None = None

    id: str = field(init=False)

    def __post_init__(self):
        self.id = self.test_id

test_cases = [
    SermsukTestCase(
        test_id="success_multiple_files",
        folder_name="fsrm_stock",
        files_to_create=["3_BKK_skip_12345BranchA.xlsx", "3_CEN_skip_12345BranchB.xlsx"],
        files_param_count=2,
        expected_branch_names=["BranchA", "BranchB"]
    ),
    SermsukTestCase(
        test_id="error_missing_directory",
        folder_name="does_not_exist",
        files_to_create=[],
        files_param_count=1,
        expected_error=ValueError,
        error_match="Wrong folder name or folder not exists."
    ),
    SermsukTestCase(
        test_id="error_invalid_filename",
        folder_name="fsrm_stock",
        files_to_create=["3invalidname.xlsx"],
        files_param_count=1,
        expected_error=ValueError,
        error_match="Wrong file name format"
    ),
    SermsukTestCase(
        test_id="error_unexpected_file_count",
        folder_name="fsrm_stock",
        files_to_create=["3_BKK_skip_12345BranchA.xlsx"],
        files_param_count=5, # Expecting 5 files but only generating 1
        expected_error=ValueError,
        error_match="Expected 5 files, found 1. Check folder again." 
    )
]


class TestExtractSermsukData:
    @pytest.mark.parametrize("test_case", test_cases, ids=lambda tc: tc.id)
    def test_extract_sermsuk_data(self, tmp_path: Path, test_case: SermsukTestCase):
        day = 15
        stock_date = date(2026, 6, day)
        sub_folder = tmp_path / test_case.folder_name
 
        if test_case.folder_name != "does_not_exist":
            sub_folder.mkdir()
 
        for filename in test_case.files_to_create:
            file_path = sub_folder / filename
            create_mock_excel(file_path, sheet_name=str(day))
 
        if test_case.expected_error:
            with pytest.raises(test_case.expected_error, match=test_case.error_match):
                extract_sermsuk_data(
                    columns_to_read=[0, 1, 2, 3, 4, 5, 6, 7],
                    sub_folder=sub_folder,
                    stock_date=stock_date,
                    day=day,
                    rows_to_read=10,
                    rows_to_skip=0,
                    has_header=True,
                    files=test_case.files_param_count
                )
        else:
            result_df = extract_sermsuk_data(
                columns_to_read=[0, 1, 2, 3, 4, 5, 6, 7],
                sub_folder=sub_folder,
                stock_date=stock_date,
                day=day,
                rows_to_read=10,
                rows_to_skip=0,
                has_header=True,
                files=test_case.files_param_count
            )
 
            assert isinstance(result_df, pl.DataFrame)
            assert "branch_code" in result_df.columns
            assert "sermsuk_branch_name" in result_df.columns
 
            branch_names = result_df["sermsuk_branch_name"].unique().to_list()
 
            if test_case.expected_branch_names:
                for expected_branch in test_case.expected_branch_names:
                    assert expected_branch in branch_names
 
            assert result_df["stock_date"][0] == stock_date
 
            # 2 files * 2 valid rows per mock file = 4 expected rows
            assert result_df.shape == (4, 12)
        #note race condition mem misallocation bug to fix