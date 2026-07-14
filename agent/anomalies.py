import polars as pl


def flag_anomalies(df: pl.DataFrame, threshold_pct: float) -> pl.DataFrame:
    '''
    Flags SKU/branch rows where ending stock is below forecast by more than threshold_pct.
    Rows with no forecast (forecast == 0, filled by map_forecast_to_daily) are excluded
    since there's nothing to compare against.
    '''
    return (
        df.filter(pl.col("forecast") > 0)
          .with_columns(
              (1 - pl.col("ending_stock_case") / pl.col("forecast")).alias("shortage_pct")
          )
          .filter(pl.col("shortage_pct") > threshold_pct)
          .select(
              "sermsuk_branch_name", "region_TBL", "SKU", "description", "brand", "category",
              "ending_stock_case", "forecast", "shortage_pct"
          )
          .sort("shortage_pct", descending=True)
    )