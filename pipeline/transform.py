import polars as pl


def rename_normalize_stock_columns(df: pl.DataFrame
                                   , column_mapping: dict[str,str]
                                   , stock_columns: list[str]
                                   , ship_columns: list[str]) -> pl.DataFrame:
    '''
    There were some columns with '-' which caused error when calculating total stock, so we remove those, then change the datatype to a decimal for faster calculation. Rename columns afterwards for readability.
    '''
    df = df.rename(column_mapping).with_columns(
                pl.col(col).str.strip_chars()
                .replace(["-", "", " "], ["0", "0", "0"])
                .fill_null("0")
                .cast(pl.Float64) 
                for col in stock_columns + ship_columns
    )
    
    return df


def map_base_unit_to_sku(df: pl.DataFrame, sku_df: pl.DataFrame) -> pl.DataFrame:
    '''
    This function maps the base unit to the main dataframe based on the SKU column.
    '''
    return df.join(sku_df, on="SKU", how="left") 


def total_stock_as_crates(df: pl.DataFrame, stock_columns: list[str]) -> pl.DataFrame:
    '''
    stock case [col R] + (stock bottle[col S] / base unit[col E])
    '''
    df = df.with_columns(
        (
            pl.col("stock_case")
            + (
                pl.col("stock_bottle") / pl.col("base_unit_bottle")
               )
        )
        .truncate(1) #1 d.p
        .alias("ending_stock_case")
    )
    df = df.with_columns(
            pl.col(col).cast(pl.Int64)
            for col in stock_columns
                )

    return df


def total_shippment_as_crates(df: pl.DataFrame, ship_columns: list[str]) -> pl.DataFrame:
    '''
    รวมเบิกจ่าย case [col N] + (รวมเบิกจ่าย bottle[col O] / base unit[col E])
    '''

    df = df.with_columns(
        (
            pl.col("shippment_case")
            + (
                pl.col("shippment_bottle") / pl.col("base_unit_bottle")
               )
        )
        .truncate(1) #1 d.p
        .alias("act_shippment_case")
    )
    df = df.with_columns(
            pl.col(col).cast(pl.Int64)
            for col in ship_columns
                )

    return df     


def map_sermsuk_to_TBL_WH_select_columns(df: pl.DataFrame
                                         , mapping_df: pl.DataFrame
                                         , column_to_map: str | list[str]
                                         ) -> pl.DataFrame:
    '''
    map tbl WH to sermsuk branch, rearrange and select final set of columns to save 
    '''

    return df.join(
        mapping_df, on = column_to_map, how= "left"
        )

def rearrange_columns(df: pl.DataFrame, column_order: list[str]) -> pl.DataFrame:

    return df.select(
            pl.col(column_order)
        )

    
def transform_consolidate_forecasts(df_beer: pl.DataFrame, df_spirits: pl.DataFrame) -> pl.DataFrame:
    """gets branch code and combines beer and spirits metrics and groups same fields."""
    return (
        pl.concat([df_beer, df_spirits])
        .with_columns(
            pl.col("branch_code").str.split(" ").list.first().cast(pl.Int64)
        )
        .group_by(["SKU", "branch_code", "category"])
        .agg(pl.col("forecast").sum())
    )

def branch_code_to_int(df: pl.DataFrame)-> pl.DataFrame:

    return (df.with_columns(pl.col("branch_code").cast(pl.Int64)))


def map_forecast_to_daily(daily_df: pl.DataFrame, forecast_df: pl.DataFrame) -> pl.DataFrame:
    """Joins the consolidated forecast dataset directly onto the current day's output dataframe."""
    return (
        daily_df.join(forecast_df, how="left", on=["branch_code", "SKU"])
        .with_columns(
            pl.col("forecast").fill_null(0),
            pl.col("category").fill_null("no_forecast")
        )
    )


#def cumulative_ASN(df: pl.DataFrame)
    
    
   



