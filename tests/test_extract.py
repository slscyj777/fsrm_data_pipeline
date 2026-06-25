import pytest
import polars as pl
from datetime import date
from pathlib import Path
from pipeline.extract import extract_sermsuk_data

def create_mock_excel(path: Path, sheet_name: str):
    df = pl.DataFrame({
        "column_0": ["data1", "data2", "", "", "จิง"],
        "column_1": ["val1", "val2", " ", "", ""],
        "column_2": ["val3", "val4", " ", "", ""],
        "column_8": ["val3", "val4","   ", "", ""],
        "column_4": ["val3", "val4", "", "", "zzz"],
        "column_5": ["val3", "val4"," ", "", ""],
        "column_6": ["val3", "val4", " ", "", ""],
        "column_7": ["val3", "val4","", "", "xyz"]
    })
    df.write_excel(path, worksheet=sheet_name)


class TestExtractSermsukData:
    
    def test_extract_sermsuk_data_success(self, tmp_path: Path):
        sub_folder = tmp_path / "fsrm_stock"
        sub_folder.mkdir()
        
        valid_file_1 = sub_folder / "3_BKK_skip_12345BranchA.xlsx"
        valid_file_2 = sub_folder / "3_CEN_skip_12345BranchB.xlsx"
        
        day = 15
        create_mock_excel(valid_file_1, sheet_name=str(day))
        create_mock_excel(valid_file_2, sheet_name=str(day))
        
        result_df = extract_sermsuk_data(
            columns_to_read=[0, 1, 2, 3, 4, 5, 6, 7],
            sub_folder=sub_folder,
            day=day,
            rows_to_read=10,
            rows_to_skip=0,
            has_header=True,
            files=2 
        )
        
        assert isinstance(result_df, pl.DataFrame)
        assert "branch_code" in result_df.columns
        assert "sermsuk_branch_name" in result_df.columns 
        
        branch_names = result_df["sermsuk_branch_name"].unique().to_list()
        assert "BranchA" in branch_names
        assert "BranchB" in branch_names
        
        expected_date = date.today().replace(day=day)
        assert result_df["stock_date"][0] == expected_date
        assert result_df.shape == (4, 12)

    def test_missing_directory_raises_error(self, tmp_path: Path):
        bad_folder = tmp_path / "does_not_exist"
        
        with pytest.raises(NameError, match="Wrong folder name or folder not exists."):
            extract_sermsuk_data([0], bad_folder, files=1)

    def test_invalid_filename_format_raises_error(self, tmp_path: Path):
        sub_folder = tmp_path / "fsrm_stock"
        sub_folder.mkdir()
        
        bad_file = sub_folder / "3invalidname.xlsx"
        create_mock_excel(bad_file, sheet_name="15")
        
        with pytest.raises(SyntaxError, match="Wrong file name format"):
            extract_sermsuk_data([0], sub_folder, day=15, files=1)

    def test_unexpected_file_count_raises_error(self, tmp_path: Path):
        sub_folder = tmp_path / "fsrm_stock"
        sub_folder.mkdir()
        
        valid_file = sub_folder / "3_BKK_skip_12345BranchA.xlsx"
        create_mock_excel(valid_file, sheet_name="15")
        
        with pytest.raises(SystemError, match="Too many files. Check folder again."):
            extract_sermsuk_data(
                columns_to_read=[0, 1, 2, 3, 4, 5, 6, 7], 
                sub_folder=sub_folder, 
                day=15, 
                files=5, 
                rows_to_skip=0
            )