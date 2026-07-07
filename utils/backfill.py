import polars as pl

def process_beverage_data(file_path: str, columns_to_read: list[int]) -> pl.DataFrame:

    rename_map = {
        "column_1": "branch_code",
        "column_2": "category",
        "column_3": "SKU",
        "column_4": "forecast"
    }
    df = (
        pl.read_excel(
            file_path,
            engine="calamine",
            columns=columns_to_read,
            has_header=False,
            read_options={"skip_rows": 1} 
        )
        .rename(rename_map)
        .with_columns(
            pl.col("branch_code").str.split(" ").list.first().cast(pl.Int64)
        )
    )

    return df










