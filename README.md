# FSRM Daily Pipeline — User Guide

This document explains how to install and run the FSRM stock pipeline on Windows. It covers the Streamlit app (use this for daily work) and the Agent Summary feature.

---

## What's new

- **1.1.1** — Fixed `scripts/setup.bat`. It no longer runs `uv sync`. `scripts/launch_ui.bat` already runs `uv sync` before it opens the app, so the second run was not needed.
- **1.1.0** — `clear_csv_data.py` now locks the backup file while it runs, keeps timestamped backup copies, writes an audit log, and can restore a previous backup. See **Delete or restore backup rows** below.

---

## What the pipeline does

Each day, the pipeline does these tasks in order:

1. It reads branch stock files, shipment files, and forecast files from SharePoint.
2. It cleans the data and combines it into one table.
3. It saves a backup CSV file for the month, so no data is lost.
4. It writes the final table into the shared file `FSRM_consolidated.xlsx`.
5. If you enable it, an AI step writes a short summary of which branches and SKUs are low on stock, and suggests where to focus replenishment.

You can run these steps from the browser app or from the command line.

---

## Before you start

Install `uv`. If `uv` is not on your computer, open PowerShell and run this command:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Setup (do this once)

**Warning:** Put the project folder on local disk only. Do not put it inside a folder synced by OneDrive or SharePoint. Setup creates a `.venv` folder with thousands of files. OneDrive tries to sync every one of them. This slows your computer and can break the sync.

### Step 1: Choose a project folder
Pick a folder outside OneDrive, for example `C:\FSRM`. Copy the project into it.

### Step 2: Open the project folder
```bash
cd path/to/your/folder
```

### Step 3: Install `uv`
Double-click `scripts/setup.bat`. This installs `uv` if it is missing. If setup fails, the script prints the error and stays open so you can read it.

You do not need to run `uv sync` by hand. The app runs it for you the first time you start it — see **Run the app** below.

### Step 4: Sync the SharePoint folder
Get access to the SharePoint folder named **"Stock FSRM SSC"**. Sync it, so it appears as a normal folder on your computer. The pipeline reads branch files and forecast files from this folder, and writes the output Excel file back to it.

### Step 5: Add the input files
Copy the master dimension file, the SKU dimension file, and the forecast file into `excel/input/`. You set these file names in the app Settings panel — see below.

### Step 6: Set the environment variable
1. Rename `.env.example` to `.env`.
2. Open `.env` and add `GEMINI_API_KEY`.

You need `GEMINI_API_KEY` only for the AI Summary feature. Without it, the pipeline still runs. Instead of a summary, you see a message that says no summary was generated.

---

## Run the app (use this for daily work)

Open a terminal and run this command:

```bash
uv run streamlit run st_app.py
```

**Shortcut:** Instead of this command, double-click `scripts/launch_ui.bat` in the project folder. This script runs `uv sync` first, then opens the app. The first run takes longer while it installs dependencies. Later runs start faster.

This command opens the FSRM Daily Pipeline dashboard in your browser.

### Settings (left sidebar)
Open **Settings** in the sidebar to view or change file paths and folder names: the SharePoint sync path, input file names, and the output file name. Change a field, then click **Save settings**. The app uses the new values the next time you run the pipeline. Every field is required. If you leave a field blank, the app shows a warning.

### Run the pipeline
1. Pick the **Stock date** you want to process.
2. Choose the **Steps to run**:
   - `all` — runs every step. Use this for normal daily work.
   - `transform` — extracts and cleans the raw files only.
   - `backup` — saves data to the monthly CSV backup only.
   - `excel` — writes the CSV backup into the Excel file only.

   Run a single step only after a previous run failed partway through — for example, if Excel was open on someone's computer. This avoids repeating the slower steps.
3. Click **Run pipeline**. The status box shows progress and any errors as they happen. If you already processed this date, the app shows a note that it skipped the backup step, to prevent duplicate rows, but still refreshed Excel.

### Replenishment Summary (AI agent)
Below the pipeline runner:

1. Set the **Shortage threshold** slider. This sets how far below forecast, in percent, a SKU or branch must be before the agent flags it. For example, 30% means the agent flags only items that are short by 30% or more.
2. Click **Run Agent**. The agent reads that day's data from the monthly backup CSV, flags shortages above your threshold, and asks the AI to write a short Thai-language summary of which branches and SKUs need follow-up.
3. The summary appears below the button and stays on screen. Click **Copy summary to clipboard** to paste it into an email or a Teams message.

**Note:** The agent reads data from the CSV backup. Run the pipeline for that date first, at least through the `backup` step, before you generate a summary.

---

## Advanced: run from the command line

Use the command line to troubleshoot a failed run, or to schedule automated runs. Run the same pipeline without the browser app:

```bash
uv run main.py
```

### Run one or more steps
```bash
uv run main.py --steps [all | transform | backup | excel]
```

| Step | What it does |
|---|---|
| `transform` | Extracts the forecast files and branch data, cleans the data, and caches it to a local Parquet file (`data/temp_transformed.parquet`). |
| `backup` | Reads the Parquet cache, checks whether data for that date already exists, and appends new rows to the monthly CSV file (`data/FSRM_consolidated_[Month]_[Year].csv`). It skips rows that already exist. |
| `excel` | Reads the current CSV file, checks that rows are unique, and builds or updates the Excel sheet through `xlwings`. |

### Set a different date
```bash
uv run main.py --day 15 --month 7 --year 2026
```
If you do not set a date, the pipeline uses today's date.

**Examples:**
```bash
# Run only the backup and Excel steps, using the existing local cache
uv run main.py --steps backup excel

# Rerun only the Excel step after you resolve a file-lock error
uv run main.py --steps excel
```

---

## Run the automated tests

The `tests/` folder holds automated checks for the data-cleaning and transformation logic in `pipeline/`. Run these tests after you change any file in `pipeline/`, before you use the change on real data.

Run all tests from the project root:

```bash
uv run pytest
```

### What the tests cover

| Test file | What it checks |
|---|---|
| `tests/test_extract.py` | Reading branch files, parsing file names, and flagging rows with missing required data. |
| `tests/test_transform.py` | Cleaning stock and shipment numbers, extracting branch codes, and combining forecast data. |
| `tests/test_load.py` | Detecting a stock date that already exists in the backup CSV. |

### Reading the output
- A line of dots means each test passed.
- `F` marks a failed test. Pytest prints the test name, the line that failed, and the values it expected versus the values it got.
- A summary line at the end shows the total passed and failed.

### Useful commands

Run one test file only:
```bash
uv run pytest tests/test_transform.py
```

Run tests whose name contains a keyword:
```bash
uv run pytest -k "branch_code"
```

Show each test name as it runs:
```bash
uv run pytest -v
```

**Note:** These tests check logic only. They use small, made-up data, not your real SharePoint files. Passing tests do not confirm that the SharePoint folder, input files, or Excel output are set up correctly — use **Run the pipeline** for that.

---

## Delete or restore backup rows (clear_csv_data.py)

Use this script to remove rows for specific dates from the monthly CSV backups. Use it when bad data reached the backup and you need to reprocess a date. It can also undo a deletion.

Run it from the project root:

```bash
uv run clear_csv_data.py --dates 2026-07-21 2026-07-22
```

### What it does
1. Finds the monthly backup CSV for each date you give it.
2. Locks that file, so no one else can change it at the same time.
3. Copies the current file to a timestamped `.bak` file, in the same folder, before it changes anything.
4. Removes the rows that match your dates.
5. Writes an entry to `delete_audit.log`, in the same folder: the time, your username, and the number of rows removed.
6. Keeps the 3 most recent `.bak` files per CSV, and deletes older ones.
7. Removes the lock.

**After you delete rows, run `uv run main.py --steps excel`.** This updates the Excel file with the change. `clear_csv_data.py` does not touch Excel or the local Parquet cache.

### Options

| Flag | What it does |
|---|---|
| `--dates` | One or more dates to remove, in `YYYY-MM-DD` format. Required, unless you use `--restore`. |
| `--dry-run` | Shows which rows match. Does not change any file. Use this to check before you delete. |
| `--yes` | Skips the "Delete N date(s)?" confirmation prompt. Use this in scheduled scripts, not by hand. |
| `--keep-backups` | Number of `.bak` files to keep per CSV. Default: 3. |
| `--restore` | Path to a `.bak` file. Restores that file. Ignores `--dates`. |

### Examples

Preview a deletion, without changing anything:
```bash
uv run clear_csv_data.py --dates 2026-07-21 --dry-run
```

Delete rows for two dates, with confirmation:
```bash
uv run clear_csv_data.py --dates 2026-07-21 2026-07-22
```

Restore a backup file:
```bash
uv run clear_csv_data.py --restore "D:/OneDrive/.../backup_csv/FSRM_consolidated_July_2026.20260721101500.bak"
```

**Warning:** If the script reports that a `.lock` file already exists, do not delete it unless you are sure no one else is running the script. Two people writing to the same CSV at the same time can corrupt it.

---

## Troubleshooting

| Message or symptom | Cause and fix |
|---|---|
| "SharePoint sync directory not found" (path looks correct) | OneDrive syncs to a different drive than the project expects — for example, OneDrive is on `D:`, but the project is on `C:`. The app looks for the SharePoint folder under your Windows user profile, which is not always where OneDrive puts it. Open `pipeline/paths.py`, find the `sp_root` function, and change it to return your OneDrive path directly, for example `Path("D:/OneDrive/Thai Beverage Public Company Limited/...")`. |
| "SharePoint sync directory not found" (path is missing) | The "Stock FSRM SSC" folder is not synced locally, or **SP_SYNC_PATH** in Settings does not match the local path. Sync the folder and check the path. |
| "Wrong file name format" | A branch file in the stock subfolder does not follow the required naming pattern. Check that the file was exported correctly. |
| "Expected N files, found M" | Some branch files are missing from the day's SharePoint subfolder, or extra unrelated files are present. Check the folder contents. |
| Excel step fails with a file-lock error | Someone has the output Excel file open. Close the file, then rerun with `--steps excel` (command line) or select `excel` only (app). |
| "No summary generated: GEMINI_API_KEY not set" | `.env` is missing `GEMINI_API_KEY`. Add the key to `.env`. |
| Replenishment Summary is empty or shows an error | Run the pipeline for that date first, at least through the `backup` step. |
| `clear_csv_data.py` stops with "another process may be writing" | A leftover `.lock` file exists in the `backup_csv` folder, from an earlier run that did not finish. Confirm no one else is running the script, delete the `.lock` file by hand, then run the command again. |

---

# คู่มือการใช้งานโปรเจกต์ (ภาษาไทย)

เอกสารนี้อธิบายวิธีติดตั้งและใช้งาน FSRM stock pipeline บน Windows ครอบคลุมแอป Streamlit (ใช้สำหรับงานประจำวัน) และฟีเจอร์ Agent Summary

---

## มีอะไรใหม่

- **1.1.1** — แก้ไข `scripts/setup.bat` ให้ไม่รัน `uv sync` อีกต่อไป เพราะ `scripts/launch_ui.bat` รัน `uv sync` ให้อยู่แล้วก่อนเปิดแอป การรันซ้ำสองครั้งจึงไม่จำเป็น
- **1.1.0** — `clear_csv_data.py` เพิ่มการล็อกไฟล์ระหว่างทำงาน เก็บไฟล์สำรองแบบมีวันเวลากำกับ บันทึก audit log และสามารถกู้คืนไฟล์สำรองเก่าได้ ดูหัวข้อ **ลบหรือกู้คืนข้อมูลใน backup** ด้านล่าง

---

## หน้าที่ของ pipeline

ทุกวัน pipeline ทำงานตามลำดับนี้:

1. อ่านไฟล์สต็อกและไฟล์เบิกจ่ายรายสาขา และไฟล์ forecast จาก SharePoint
2. ทำความสะอาดข้อมูลและรวมเป็นตารางเดียว
3. บันทึกไฟล์ CSV สำรองประจำเดือน เพื่อป้องกันข้อมูลสูญหาย
4. เขียนตารางผลลัพธ์สุดท้ายลงในไฟล์ที่ใช้ร่วมกันชื่อ `FSRM_consolidated.xlsx`
5. หากเปิดใช้งาน ระบบ AI จะเขียนสรุปสั้นๆ ว่าสาขาหรือ SKU ใดมีสต็อกต่ำ และแนะนำจุดที่ควรเติมสต็อกก่อน

คุณสามารถรันแต่ละขั้นตอนผ่านแอปในเบราว์เซอร์ หรือผ่าน command line ก็ได้

---

## ก่อนเริ่มใช้งาน

ติดตั้ง `uv` หากเครื่องของคุณยังไม่มี `uv` ให้เปิด PowerShell แล้วรันคำสั่งนี้:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## การตั้งค่า (ทำครั้งเดียว)

**คำเตือน:** วางโฟลเดอร์โปรเจกต์บน disk ในเครื่องเท่านั้น ห้ามวางไว้ในโฟลเดอร์ที่ซิงค์กับ OneDrive หรือ SharePoint ขั้นตอนติดตั้งจะสร้างโฟลเดอร์ `.venv` ซึ่งมีไฟล์หลายพันไฟล์ OneDrive จะพยายามซิงค์ไฟล์เหล่านี้ทั้งหมด ทำให้เครื่องช้าลง และอาจทำให้การซิงค์เสียหาย

### ขั้นตอนที่ 1: เลือกโฟลเดอร์โปรเจกต์
เลือกโฟลเดอร์ที่อยู่นอก OneDrive เช่น `C:\FSRM` แล้วคัดลอกโปรเจกต์ไปวางไว้ที่นั่น

### ขั้นตอนที่ 2: เปิดโฟลเดอร์โปรเจกต์
```bash
cd path/to/your/folder
```

### ขั้นตอนที่ 3: ติดตั้ง `uv`
ดับเบิลคลิกไฟล์ `scripts/setup.bat` สคริปต์นี้จะติดตั้ง `uv` หากยังไม่มี หากตั้งค่าไม่สำเร็จ สคริปต์จะแสดงข้อผิดพลาดและค้างหน้าต่างไว้ให้อ่าน

คุณไม่ต้องรัน `uv sync` ด้วยตนเอง แอปจะรันคำสั่งนี้ให้อัตโนมัติในครั้งแรกที่คุณเปิดแอป — ดูหัวข้อ **การใช้งานแอป** ด้านล่าง

### ขั้นตอนที่ 4: ซิงค์โฟลเดอร์ SharePoint
ขอสิทธิ์เข้าถึงโฟลเดอร์ SharePoint ชื่อ **"Stock FSRM SSC"** แล้วซิงค์ให้ปรากฏเป็นโฟลเดอร์ปกติบนเครื่องคอมพิวเตอร์ pipeline จะอ่านไฟล์สาขาและไฟล์ forecast จากโฟลเดอร์นี้ และเขียนไฟล์ Excel ผลลัพธ์กลับไปที่โฟลเดอร์นี้เช่นกัน

### ขั้นตอนที่ 5: เพิ่มไฟล์ input
คัดลอกไฟล์ master dimension, ไฟล์ SKU dimension และไฟล์ forecast ไปวางที่ `excel/input/` คุณตั้งชื่อไฟล์เหล่านี้ได้จากหน้า Settings ในแอป — ดูด้านล่าง

### ขั้นตอนที่ 6: ตั้งค่า environment variable
1. เปลี่ยนชื่อไฟล์ `.env.example` เป็น `.env`
2. เปิดไฟล์ `.env` แล้วเพิ่ม `GEMINI_API_KEY`

คุณต้องใส่ `GEMINI_API_KEY` เฉพาะเมื่อต้องการใช้ฟีเจอร์ AI Summary หากไม่ใส่ pipeline ยังทำงานได้ตามปกติ แต่จะแสดงข้อความว่ายังไม่ได้สร้างสรุป แทนที่จะแสดงสรุปจริง

---

## การใช้งานแอป (ใช้สำหรับงานประจำวัน)

เปิด terminal แล้วรันคำสั่งนี้:

```bash
uv run streamlit run st_app.py
```

**ทางลัด:** แทนที่จะพิมพ์คำสั่งนี้ ให้ดับเบิลคลิกไฟล์ `scripts/launch_ui.bat` ในโฟลเดอร์โปรเจกต์ สคริปต์นี้จะรัน `uv sync` ก่อน แล้วจึงเปิดแอป การรันครั้งแรกจะใช้เวลานานกว่าปกติเพราะต้องติดตั้ง dependencies ครั้งถัดไปจะเปิดเร็วขึ้น

คำสั่งนี้จะเปิดหน้า Dashboard ของ FSRM Daily Pipeline ในเบราว์เซอร์

### Settings (แถบด้านซ้าย)
เปิด **Settings** ในแถบด้านซ้ายเพื่อดูหรือแก้ไข path และชื่อโฟลเดอร์/ไฟล์: path ของ SharePoint, ชื่อไฟล์ input และชื่อไฟล์ output แก้ค่าที่ต้องการ แล้วกด **Save settings** แอปจะใช้ค่าใหม่ในการรันครั้งถัดไป ทุกช่องต้องกรอกข้อมูล หากปล่อยช่องใดว่าง แอปจะแสดงคำเตือน

### รัน pipeline
1. เลือก **Stock date** ที่ต้องการประมวลผล
2. เลือก **Steps to run**:
   - `all` — รันทุกขั้นตอน ใช้ตัวเลือกนี้สำหรับงานประจำวันปกติ
   - `transform` — ดึงและทำความสะอาดข้อมูลดิบเท่านั้น
   - `backup` — บันทึกข้อมูลลง CSV สำรองรายเดือนเท่านั้น
   - `excel` — เขียนข้อมูลจาก CSV สำรองลงไฟล์ Excel เท่านั้น

   ให้เลือกรันเฉพาะขั้นตอนเดียวเมื่อการรันครั้งก่อนล้มเหลวกลางทาง เช่น มีคนเปิดไฟล์ Excel ค้างไว้ วิธีนี้ช่วยไม่ต้องรันขั้นตอนที่ใช้เวลานานซ้ำ
3. กด **Run pipeline** กล่องสถานะจะแสดงความคืบหน้าและข้อผิดพลาด (ถ้ามี) แบบเรียลไทม์ หากคุณเคยประมวลผลวันที่นี้ไปแล้ว แอปจะแจ้งว่าข้ามขั้นตอนสำรองข้อมูลเพื่อป้องกันข้อมูลซ้ำ แต่ยังอัปเดต Excel ตามปกติ

### Replenishment Summary (AI agent)
ใต้ส่วนรัน pipeline:

1. ปรับแถบเลื่อน **Shortage threshold** เพื่อกำหนดว่าสต็อกต่ำกว่า forecast กี่เปอร์เซ็นต์ agent จึงจะแจ้งเตือน ตัวอย่างเช่น 30% หมายถึง agent จะแจ้งเตือนเฉพาะรายการที่ขาดตั้งแต่ 30% ขึ้นไป
2. กด **Run Agent** agent จะอ่านข้อมูลของวันนั้นจากไฟล์ CSV สำรองรายเดือน คัดกรองรายการที่ขาดสต็อกเกิน threshold ที่ตั้งไว้ แล้วให้ AI เขียนสรุปภาษาไทยสั้นๆ ว่าสาขาหรือ SKU ใดต้องติดตาม
3. สรุปจะแสดงใต้ปุ่มและค้างอยู่บนหน้าจอ กด **Copy summary to clipboard** เพื่อคัดลอกไปวางในอีเมลหรือข้อความ Teams

**หมายเหตุ:** agent อ่านข้อมูลจากไฟล์ CSV สำรอง ให้รัน pipeline สำหรับวันที่นั้นก่อน อย่างน้อยถึงขั้นตอน `backup` จึงจะสร้างสรุปได้

---

## ขั้นสูง: รันผ่าน command line

ใช้ command line เพื่อแก้ปัญหาการรันที่ล้มเหลว หรือตั้งเวลารันอัตโนมัติ รัน pipeline เดียวกันโดยไม่ต้องเปิดแอปในเบราว์เซอร์:

```bash
uv run main.py
```

### รันหนึ่งขั้นตอนหรือมากกว่า
```bash
uv run main.py --steps [all | transform | backup | excel]
```

| ขั้นตอน | สิ่งที่เกิดขึ้น |
|---|---|
| `transform` | ดึงข้อมูลจากไฟล์ forecast และข้อมูลสาขา ทำความสะอาดข้อมูล แล้วแคชลงไฟล์ Parquet ในเครื่อง (`data/temp_transformed.parquet`) |
| `backup` | อ่านข้อมูลจาก Parquet cache ตรวจสอบว่ามีข้อมูลของวันที่นั้นอยู่แล้วหรือไม่ แล้วแนบข้อมูลใหม่ต่อท้ายไฟล์ CSV รายเดือน (`data/FSRM_consolidated_[Month]_[Year].csv`) โดยข้ามแถวที่มีอยู่แล้ว |
| `excel` | อ่านไฟล์ CSV ปัจจุบัน ตรวจสอบว่าแถวข้อมูลไม่ซ้ำกัน แล้วสร้างหรืออัปเดตตาราง Excel ผ่าน `xlwings` |

### กำหนดวันที่อื่น
```bash
uv run main.py --day 15 --month 7 --year 2026
```
หากไม่ระบุวันที่ pipeline จะใช้วันที่ปัจจุบัน

**ตัวอย่าง:**
```bash
# รันเฉพาะขั้นตอน backup และ excel โดยใช้ local cache ที่มีอยู่
uv run main.py --steps backup excel

# รันขั้นตอน excel ใหม่ หลังจากแก้ปัญหาไฟล์ถูกล็อกแล้ว
uv run main.py --steps excel
```

---

## รันชุดทดสอบอัตโนมัติ (pytest)

โฟลเดอร์ `tests/` เก็บชุดทดสอบอัตโนมัติสำหรับตรวจสอบตรรกะการทำความสะอาดและแปลงข้อมูลใน `pipeline/` ให้รันชุดทดสอบนี้ทุกครั้งหลังแก้ไขไฟล์ใดๆ ใน `pipeline/` ก่อนนำไปใช้กับข้อมูลจริง

รันทุกชุดทดสอบจากโฟลเดอร์โปรเจกต์หลัก:

```bash
uv run pytest
```

### สิ่งที่ชุดทดสอบตรวจสอบ

| ไฟล์ทดสอบ | สิ่งที่ตรวจสอบ |
|---|---|
| `tests/test_extract.py` | การอ่านไฟล์สาขา การแยกชื่อไฟล์ และการตรวจจับแถวที่ขาดข้อมูลที่จำเป็น |
| `tests/test_transform.py` | การทำความสะอาดตัวเลขสต็อกและเบิกจ่าย การดึงรหัสสาขา และการรวมข้อมูล forecast |
| `tests/test_load.py` | การตรวจจับวันที่ที่มีอยู่แล้วใน backup CSV |

### วิธีอ่านผลลัพธ์
- จุด (.) แต่ละจุดหมายถึงการทดสอบผ่านหนึ่งรายการ
- `F` หมายถึงการทดสอบล้มเหลว pytest จะแสดงชื่อการทดสอบ บรรทัดที่ล้มเหลว และค่าที่คาดไว้เทียบกับค่าที่ได้จริง
- บรรทัดสรุปท้ายผลลัพธ์แสดงจำนวนที่ผ่านและล้มเหลวทั้งหมด

### คำสั่งที่มีประโยชน์

รันไฟล์ทดสอบเดียว:
```bash
uv run pytest tests/test_transform.py
```

รันเฉพาะการทดสอบที่มีชื่อตรงกับคำค้น:
```bash
uv run pytest -k "branch_code"
```

แสดงชื่อการทดสอบแต่ละรายการขณะรัน:
```bash
uv run pytest -v
```

**หมายเหตุ:** ชุดทดสอบนี้ตรวจสอบเฉพาะตรรกะของโค้ด โดยใช้ข้อมูลจำลองขนาดเล็ก ไม่ใช่ไฟล์จริงจาก SharePoint การทดสอบผ่านทั้งหมดไม่ได้ยืนยันว่าโฟลเดอร์ SharePoint ไฟล์ input หรือไฟล์ Excel output ถูกตั้งค่าถูกต้อง หากต้องการตรวจสอบส่วนนั้น ให้ใช้การ **รัน pipeline** แทน

---

## ลบหรือกู้คืนข้อมูลใน backup (clear_csv_data.py)

ใช้สคริปต์นี้เพื่อลบแถวข้อมูลของวันที่ที่ต้องการออกจากไฟล์ CSV สำรองรายเดือน ใช้เมื่อข้อมูลผิดพลาดหลุดเข้าไปใน backup แล้วต้องประมวลผลวันนั้นใหม่ สคริปต์นี้ยังใช้กู้คืนข้อมูลที่ลบไปแล้วได้ด้วย

รันจากโฟลเดอร์โปรเจกต์หลัก:

```bash
uv run clear_csv_data.py --dates 2026-07-21 2026-07-22
```

### สิ่งที่สคริปต์ทำ
1. หาไฟล์ CSV สำรองประจำเดือนของแต่ละวันที่ที่ระบุ
2. ล็อกไฟล์นั้น เพื่อไม่ให้คนอื่นแก้ไขพร้อมกัน
3. คัดลอกไฟล์ปัจจุบันเป็นไฟล์ `.bak` ที่มีวันเวลากำกับ ในโฟลเดอร์เดียวกัน ก่อนเปลี่ยนแปลงข้อมูลใดๆ
4. ลบแถวที่ตรงกับวันที่ที่ระบุ
5. บันทึกรายการลงไฟล์ `delete_audit.log` ในโฟลเดอร์เดียวกัน: เวลา, ชื่อผู้ใช้, จำนวนแถวที่ลบ
6. เก็บไฟล์ `.bak` ล่าสุด 3 ไฟล์ต่อ CSV หนึ่งไฟล์ และลบไฟล์เก่ากว่านั้น
7. ปลดล็อกไฟล์

**หลังจากลบแถวข้อมูล ให้รัน `uv run main.py --steps excel`** เพื่ออัปเดตไฟล์ Excel ให้ตรงกับข้อมูลที่เปลี่ยน สคริปต์นี้ไม่แตะไฟล์ Excel หรือ local Parquet cache

### Options

| Flag | สิ่งที่ทำ |
|---|---|
| `--dates` | วันที่ที่ต้องการลบ หนึ่งวันขึ้นไป รูปแบบ `YYYY-MM-DD` ต้องระบุ เว้นแต่ใช้ `--restore` |
| `--dry-run` | แสดงแถวที่ตรงกัน โดยไม่แก้ไขไฟล์ ใช้เพื่อตรวจสอบก่อนลบจริง |
| `--yes` | ข้ามคำถามยืนยัน "Delete N date(s)?" ใช้สำหรับสคริปต์อัตโนมัติ ไม่แนะนำให้ใช้เวลารันด้วยตนเอง |
| `--keep-backups` | จำนวนไฟล์ `.bak` ที่เก็บไว้ต่อ CSV หนึ่งไฟล์ ค่าเริ่มต้น: 3 |
| `--restore` | path ของไฟล์ `.bak` ที่ต้องการกู้คืน หากใช้ตัวเลือกนี้ จะไม่สนใจ `--dates` |

### ตัวอย่าง

ดูตัวอย่างผลลัพธ์การลบ โดยไม่แก้ไขไฟล์จริง:
```bash
uv run clear_csv_data.py --dates 2026-07-21 --dry-run
```

ลบแถวข้อมูลของสองวันที่ พร้อมคำถามยืนยัน:
```bash
uv run clear_csv_data.py --dates 2026-07-21 2026-07-22
```

กู้คืนไฟล์ backup:
```bash
uv run clear_csv_data.py --restore "D:/OneDrive/.../backup_csv/FSRM_consolidated_July_2026.20260721101500.bak"
```

**คำเตือน:** หากสคริปต์แจ้งว่ามีไฟล์ `.lock` อยู่แล้ว ห้ามลบไฟล์นั้นเว้นแต่มั่นใจว่าไม่มีคนอื่นกำลังรันสคริปต์อยู่ การเขียนไฟล์ CSV เดียวกันพร้อมกันสองคนอาจทำให้ไฟล์เสียหาย

---

## แก้ปัญหาเบื้องต้น

| ข้อความหรืออาการ | สาเหตุและวิธีแก้ |
|---|---|
| "SharePoint sync directory not found" (path ดูถูกต้องแล้ว) | OneDrive ซิงค์อยู่คนละ drive กับที่ pipeline คาดไว้ เช่น OneDrive อยู่ที่ `D:` แต่โปรเจกต์อยู่ที่ `C:` แอปจะหาโฟลเดอร์ SharePoint ใต้ user profile ของ Windows ซึ่งไม่ตรงกับตำแหน่งที่ OneDrive วางไฟล์เสมอไป ให้เปิดไฟล์ `pipeline/paths.py` หาฟังก์ชัน `sp_root` แล้วแก้ให้คืนค่า path ของ OneDrive โดยตรง เช่น `Path("D:/OneDrive/Thai Beverage Public Company Limited/...")` |
| "SharePoint sync directory not found" (path หายไปเลย) | โฟลเดอร์ "Stock FSRM SSC" ยังไม่ได้ซิงค์ในเครื่อง หรือ **SP_SYNC_PATH** ใน Settings ไม่ตรงกับ path จริง ให้ซิงค์โฟลเดอร์และตรวจสอบ path |
| "Wrong file name format" | ไฟล์สาขาบางไฟล์ในโฟลเดอร์สต็อกตั้งชื่อไม่ตรงตามรูปแบบที่กำหนด ให้ตรวจสอบว่า export ไฟล์ถูกต้อง |
| "Expected N files, found M" | ไฟล์สาขาบางไฟล์หายไปจากโฟลเดอร์ SharePoint ของวันนั้น หรือมีไฟล์อื่นที่ไม่เกี่ยวข้องปนอยู่ ให้ตรวจสอบเนื้อหาในโฟลเดอร์ |
| ขั้นตอน Excel ล้มเหลวเพราะไฟล์ถูกล็อก | มีคนเปิดไฟล์ Excel ปลายทางค้างไว้ ให้ปิดไฟล์ แล้วรันใหม่ด้วย `--steps excel` (command line) หรือเลือกเฉพาะ `excel` (แอป) |
| "No summary generated: GEMINI_API_KEY not set" | ไฟล์ `.env` ยังไม่มี `GEMINI_API_KEY` ให้เพิ่ม key ลงในไฟล์ `.env` |
| Replenishment Summary ว่างเปล่าหรือแสดง error | ให้รัน pipeline สำหรับวันที่นั้นก่อน อย่างน้อยถึงขั้นตอน `backup` |
| `clear_csv_data.py` หยุดทำงานพร้อมข้อความ "another process may be writing" | มีไฟล์ `.lock` ค้างอยู่ในโฟลเดอร์ `backup_csv` จากการรันครั้งก่อนที่ไม่เสร็จสมบูรณ์ ให้ตรวจสอบว่าไม่มีคนอื่นกำลังรันสคริปต์อยู่ แล้วลบไฟล์ `.lock` ด้วยตนเอง จากนั้นรันคำสั่งใหม่อีกครั้ง |