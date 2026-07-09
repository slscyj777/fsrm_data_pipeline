from pydantic import BaseModel, Field
from pathlib import Path

class ConfigSchema(BaseModel):
    TEST_FILE: str
    
    # elements inside lists must match the specified inner type
    COLUMNS_TO_READ: list[int] = Field(min_length=1)
    BEER_COLUMNS_TO_READ: list[int]
    SPIRITS_COLUMNS_TO_READ: list[int]
    SKU_COLUMNS_TO_READ: list[int]
    
    ASSIGN_COLUMN_MAPPING: dict[str, str]
    SFC_RENAME_MAPPING: dict[str, str]
    SKU_RENAME_MAPPING: dict[str, str]
    
    ASSIGN_COLUMN_ORDER: list[str]
    STOCK_COL: list[str]
    SHIP_COL: list[str]
    SUB_FOLDER_NAME: str
    FSRM_FOLDER: str
    SP_SYNC_PATH: str
    MASTER_DIM_FILE: str
    SKU_DIM_FILE: str
    FORECAST_FILE: str
    OUTPUT_FILE: str


CONFIG_PATH = Path(__file__).parent.parent / "settings.json"
# Read the raw file and validate it through the schema
settings = ConfigSchema.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))