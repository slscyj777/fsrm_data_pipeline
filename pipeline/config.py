TEST_FILE: str = "output.xlsx"

# -------- column structures & logic  -------------
COLUMNS_TO_READ: list[int] = [1, 2, 17, 18, 13, 14]

BEER_COLUMNS_TO_READ: list[int] = [6, 7, 11, 13]

SPIRITS_COLUMNS_TO_READ: list[int] = [5, 8, 12, 14]

SKU_COLUMNS_TO_READ: list[int] = [3, 5, 21]

ASSIGN_COLUMN_MAPPING: dict[str, str] = {
    "column_1": "SKU",
    "column_2": "description",
    "column_3": "stock_case",
    "column_4": "stock_bottle",
    "column_5": "shippment_case",
    "column_6": "shippment_bottle",
}

SFC_RENAME_MAPPING: dict[str, str] = {
    "column_1": "branch_code",
    "column_2": "category",
    "column_3": "SKU",
    "column_4": "forecast"
}

SKU_RENAME_MAPPING: dict[str, str] = {
    "column_1": "SKU",
    "column_2": "brand",
    "column_3": "base_unit_bottle"
}

ASSIGN_COLUMN_ORDER: list[str] = [
    'branch_code', 'region', 'region_TBL', 'warehouse_name_TBL',
    'sermsuk_branch_name', 'SKU', 'description', "brand", 
    'base_unit_bottle', 'stock_case', 'stock_bottle', 'stock_date', 
    'ending_stock_case', "act_shippment_case"
]

STOCK_COL: list[str] = ["stock_case", "stock_bottle"]
SHIP_COL: list[str] = ["shippment_case", "shippment_bottle"]