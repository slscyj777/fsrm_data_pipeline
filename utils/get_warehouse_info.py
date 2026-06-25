import polars as pl
from pathlib import Path

folder_path = Path.home() / "Thai Beverage Public Company Limited" / "Nitita Chaiarsa - Stock FSRM SSC" 


rows = []
count = 0

sub_folder = Path(folder_path) / "1.Stock FSRM SSC"


if sub_folder.exists() and sub_folder.is_dir():
    for file in sub_folder.iterdir():
            if (not file.is_file() 
                    or not file.name.endswith(".xlsx") 
                    or not file.name.startswith("3")
                    ):
                    continue
            
            

            name_only = file.stem
            parts = name_only.split("_", 3)
            if len(parts) == 4:
                code, region, _, name = parts
                name = name[5:]
                rows.append({"code": code, "region": region, "name": name})
                count += 1
            else:
                 raise SyntaxError(f"Wrong file name format, rename {name_only}.")

else:
     raise NameError(f"Wrong folder name or folder not exists.")
                 

if rows:
    df = pl.DataFrame(rows)
    #df.to_excel("master_dim.xlsx", index=False)
    print(df)
else:
    print("No matching files found.")
