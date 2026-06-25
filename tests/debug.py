from pipeline.extract import extract_sermsuk_data, extract_sermsuk_TBL_mapping, validate_extracted_data
from pipeline.transform import rename_normalize_stock_columns, total_stock_as_crates,total_shippment_as_crates, map_sermsuk_to_TBL_WH_select_columns
from pipeline.load import check_and_load_to_backup, load_to_excel
from pipeline.config import DAY, MASTER_DIM_FILE, TEST_FILE,SUB_FOLDER_NAME ,COLUMNS_TO_READ, STOCK_COL,SHIP_COL ,ASSIGN_COLUMN_MAPPING, ASSIGN_COLUMN_ORDER
import time
from pathlib import Path

start_time = time.perf_counter()
print("Starting...")

DAY = [12]

for day in DAY: 


    df_mapping = extract_sermsuk_TBL_mapping(MASTER_DIM_FILE)


    df = (extract_sermsuk_data(
                            columns_to_read = COLUMNS_TO_READ
                            ,day = day
                            ,sub_folder= Path(SUB_FOLDER_NAME)
                            ))


    #print(df.head)
    df.write_excel("test.xlsx")
