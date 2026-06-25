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


df_beer = process_beverage_data(
    "excel/input/FSRM_Beer Sales Forecasting_July 2026.xlsx", 
    columns_to_read=[6, 7, 11, 13] 
)

df_spirits = process_beverage_data(
    "excel/input/FSRM_Spirits Sales Forecasting_July 2026.xlsx", 
    columns_to_read=[5, 8, 12, 14]
)


df_combined = pl.concat([df_beer, df_spirits])

backup_df = pl.read_csv("data/FSRM_consolidated_June_2026.csv")


df_combined = (
    df_combined
    .group_by(["SKU", "branch_code", "category"]).agg(
    pl.col("forecast").sum())
)

updated_backup_df = (backup_df.join(df_combined, how="left", on=["branch_code", "SKU"])
                     .with_columns((pl.col("forecast").fill_null(0)),
                                   (pl.col("category").fill_null("no_forecast"))
                                   )
                                   )

print(updated_backup_df)

updated_backup_df.write_csv("data/output.csv")







