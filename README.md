# FSRM Daily Pipeline — User Guide

This guide covers everything needed to set up and run the FSRM stock pipeline on **Windows**, including the **Streamlit app** (recommended for daily use) and the **Agent Summary** feature.

---

## What this project does

Every day, this tool:
1. Pulls branch-level stock/shipment files and forecast files from SharePoint.
2. Cleans and consolidates them into one dataset.
3. Saves a backup CSV (split per month) so no data is lost.
4. Pushes the final table into the shared `FSRM_consolidated.xlsx` Excel file.
5. (Optional) Uses AI to fetch and write a plain-language summary of branches/SKUs that are most short on stock, so you don't have to scan the whole sheet manually.

You can run all of this through the browser UI or directly in the CLI.

---

## Prerequisites

Ensure `uv` is installed. If not, run this in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Installation & Setup (one-time)

> **Shortcut:** Steps 1–2 below can be done in one click by double-clicking **`scripts/setup.bat`** inside the project folder. It installs `uv` if missing and runs `uv sync` for you. If it fails, it prints the error and waits so you can read it before the window closes. You can chose to do the setup manually if you wish.

### 1. Navigate to the Project Directory
```bash
cd path/to/your/folder
```

### 2. Synchronize Dependencies
```bash
uv sync
```

### 3. Sync SharePoint Folder
Get access to the **"Stock FSRM SSC"** SharePoint folder and sync it so it appears as a folder on your laptop. This is where the pipeline reads branch files/forecasts from and writes the output Excel file to.

### 4. Add Input Files
Place the required master dimension, SKU dimension, and forecast Excel files into `excel/input/` (filenames are set in the app's Settings panel — see below).

### 5. Configure Environment Variables
* Rename `.env.example` to `.env`.
* Open `.env` and add:
  * `GEMINI_API_KEY` — required only if you want to use the AI Summary feature. Without it, the pipeline still runs fine; you'll just see a message saying no summary was generated.

---

## Running the App (recommended — for daily use)

Launch the app from your terminal:

```bash
uv run streamlit run st_app.py
```

> **Shortcut:** Instead of the command above, you can just double-click **`scripts/launch_ui.bat`** inside the project folder.

This opens a browser tab with the FSRM Daily Pipeline dashboard.

### Settings (sidebar)
Expand **Settings** in the left sidebar to view/edit the file paths and folder names the pipeline uses (SharePoint sync path, input filenames, output filename, etc). Update a field and click **Save settings** — changes are written automatically and used the next time you run the pipeline. All fields are required; the app will warn you if one is left blank.

### Run the pipeline
1. Pick the **Stock date** you want to process.
2. Choose which **Steps to run**:
   - `all` — runs everything end-to-end (recommended for normal daily use)
   - `transform` — re-extract and clean the raw files only
   - `backup` — re-save to the monthly CSV backup only
   - `excel` — re-push the CSV backup into the Excel file only
   
   Use a specific step only if a previous run failed partway through (e.g. Excel was open on someone's machine) — this avoids re-running the slow steps unnecessarily.
3. Click **Run pipeline**. Progress and any errors are shown live in the status box. If the date was already processed before, you'll see a note that the backup step was skipped (to avoid duplicate rows) but Excel was still refreshed.

### Replenishment Summary (AI agent)
Below the pipeline runner:
1. Adjust the **Shortage threshold** slider — this sets how far below forecast (in %) a SKU/branch needs to be before it's flagged (e.g. 30% means only items short by 30% or more are included).
2. Click **Run Agent**. This initializes the agent to reads that day's data from the monthly backup CSV, flags shortages above your threshold, and asks AI to write a short Thai-language summary of which branches/SKUs need follow-up.
3. The summary appears below and stays on screen. Use **Copy summary to clipboard** to paste it into an email, Teams message, etc.

> Note: the agent reads from the CSV backup, so you must run the pipeline (at least through the `backup` step) for that date before generating a summary.

---

## Advanced: Running via Command Line

For troubleshooting or scheduled/automated runs, the same pipeline can be run without the browser UI:

```bash
uv run main.py
```

### Pipeline Slices
```bash
uv run main.py --steps [all | transform | backup | excel]
```

* **`transform`**: Extracts raw forecast files and branch data, executes data cleansing pipelines, and caches to a fast local Parquet file (`data/temp_transformed.parquet`).
* **`backup`**: Reads the Parquet cache, checks if data for that run date already exists, and appends rows to the monthly CSV file (`data/FSRM_consolidated_[Month]_[Year].csv`) while skipping duplicates.
* **`excel`**: Reads the updated CSV file, checks for uniqueness, and builds/updates the target Excel sheet via `xlwings`.

### Date override
```bash
uv run main.py --day 15 --month 7 --year 2026
```
Defaults to today's date if not specified.

**Examples:**
```bash
# Run only the backup and excel delivery steps from local cache
uv run main.py --steps backup excel

# Re-run only the Excel layer after a file-lock failure is resolved
uv run main.py --steps excel
```

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| "SharePoint sync directory not found" | Make sure the "Stock FSRM SSC" folder is synced locally, and that the **SP_SYNC_PATH** in Settings matches your local path. |
| "Wrong file name format" | A branch file in the stock subfolder doesn't follow the expected naming pattern — check the file was exported correctly. |
| "Expected N files, found M" | Some branch files are missing from the day's SharePoint subfolder, or extra unrelated files exist there. |
| Excel step fails with a file lock error | Someone has the output Excel file open — close it and re-run with `--steps excel` (CLI) or select just `excel` in the app. |
| "No summary generated: GEMINI_API_KEY not set" | Add `GEMINI_API_KEY` to your `.env` file. |
| Replenishment Summary is empty/errors on a date | Make sure the pipeline has been run (through at least the `backup` step) for that date first. |

---

# คู่มือการใช้งานโปรเจกต์ (Thai Ver.)

คู่มือนี้ครอบคลุมสิ่งที่จำเป็นในการตั้งค่าและรัน FSRM stock pipeline บน **Windows** รวมถึง **แอป Streamlit** (แนะนำสำหรับใช้งานประจำวัน) และฟีเจอร์ **Agent Summary**

---

## โปรเจกต์นี้ทำอะไรบ้าง

ทุกวัน เครื่องมือนี้จะ:
1. ดึงไฟล์สต็อก/เบิกจ่ายรายสาขา และไฟล์ forecast จาก SharePoint
2. ทำความสะอาดและรวมข้อมูลเป็นชุดเดียว
3. บันทึกไฟล์ CSV สำรอง (แยกไฟล์ตามเดือน) เพื่อไม่ให้ข้อมูลสูญหาย
4. นำข้อมูลสุดท้ายเข้าสู่ไฟล์ Excel กลาง `FSRM_consolidated.xlsx`
5. (ทางเลือก) ใช้ AI ดึงและเขียนสรุปภาษาที่เข้าใจง่ายว่าสาขา/SKU ใดขาดสต็อกมากที่สุด เพื่อไม่ต้องไล่ดูทั้งชีตเอง

คุณสามารถรันทุกขั้นตอนผ่านหน้าจอเบราว์เซอร์ (UI) หรือรันตรงผ่าน CLI ก็ได้ตามต้องการ

---

## สิ่งที่ต้องเตรียมก่อนเริ่ม

ตรวจสอบว่าติดตั้ง `uv` แล้ว หากยังไม่ได้ติดตั้ง รันคำสั่งนี้ใน PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## การติดตั้งและตั้งค่า (ทำครั้งเดียว)

> **ทางลัด:** ขั้นตอนที่ 1–2 ด้านล่างสามารถทำได้ในคลิกเดียวโดยดับเบิลคลิกไฟล์ **`scripts/setup.bat`** ในโฟลเดอร์โปรเจกต์ ระบบจะติดตั้ง `uv` ให้อัตโนมัติ (ถ้ายังไม่มี) และรัน `uv sync` ให้เสร็จสรรพ โดยไม่ต้องพิมพ์คำสั่งใน terminal เอง หากล้มเหลว หน้าต่างจะแสดง error ค้างไว้ให้อ่านก่อนปิด

### 1. ไปยังโฟลเดอร์โปรเจกต์
```bash
cd path/to/your/folder
```

### 2. ซิงค์ Dependencies
```bash
uv sync
```

### 3. ซิงค์โฟลเดอร์ SharePoint
ขอสิทธิ์เข้าถึงโฟลเดอร์ **"Stock FSRM SSC"** แล้วซิงค์ให้ปรากฏเป็นโฟลเดอร์บนเครื่อง เพราะ pipeline จะอ่านไฟล์สาขา/forecast จากที่นี่ และเขียนไฟล์ Excel ผลลัพธ์กลับไปที่นี่เช่นกัน

### 4. เพิ่มไฟล์ Input
นำไฟล์ master dimension, SKU dimension และ forecast ที่จำเป็นไปวางไว้ที่ `excel/input/` (ชื่อไฟล์ตั้งค่าได้จากหน้า Settings ในแอป — ดูด้านล่าง)

### 5. ตั้งค่า Environment Variables
* เปลี่ยนชื่อ `.env.example` เป็น `.env`
* เปิดไฟล์ `.env` แล้วใส่:
  * `GEMINI_API_KEY` — จำเป็นเฉพาะถ้าต้องการใช้ฟีเจอร์ AI Summary เท่านั้น หากไม่ใส่ pipeline ยังรันได้ปกติ เพียงแต่จะขึ้นข้อความว่ายังไม่ได้สร้างสรุป

---

## การใช้งานแอป (แนะนำ — สำหรับใช้งานประจำวัน)

เปิดแอปจาก terminal:

```bash
uv run streamlit run st_app.py
```

> **ทางลัด:** แทนที่จะพิมพ์คำสั่งด้านบน สามารถดับเบิลคลิกไฟล์ **`scripts/launch_ui.bat`** ในโฟลเดอร์โปรเจกต์ได้เลย

จะเปิดแท็บเบราว์เซอร์แสดงหน้า Dashboard ของ FSRM Daily Pipeline

### Settings (แถบด้านซ้าย)
กดขยาย **Settings** เพื่อดู/แก้ไข path และชื่อโฟลเดอร์/ไฟล์ที่ pipeline ใช้ (path ของ SharePoint, ชื่อไฟล์ input, ชื่อไฟล์ output ฯลฯ) แก้ค่าแล้วกด **Save settings** ระบบจะบันทึกอัตโนมัติและใช้ในการรันครั้งถัดไป ทุกช่องต้องกรอก มิฉะนั้นแอปจะแจ้งเตือน

### รัน Pipeline
1. เลือก **Stock date** ที่ต้องการประมวลผล
2. เลือก **Steps to run**:
   - `all` — รันทุกขั้นตอนตั้งแต่ต้นจนจบ (แนะนำสำหรับใช้งานปกติ)
   - `transform` — ดึงและทำความสะอาดข้อมูลดิบเท่านั้น
   - `backup` — บันทึกลง CSV สำรองรายเดือนเท่านั้น
   - `excel` — นำข้อมูล CSV เข้าสู่ไฟล์ Excel เท่านั้น
   
   ใช้การเลือกเฉพาะขั้นตอนเมื่อการรันครั้งก่อนล้มเหลวกลางทาง (เช่น มีคนเปิดไฟล์ Excel ค้างไว้) เพื่อไม่ต้องรันขั้นตอนที่ใช้เวลานานซ้ำโดยไม่จำเป็น
3. กด **Run pipeline** ความคืบหน้าและข้อผิดพลาด (ถ้ามี) จะแสดงแบบเรียลไทม์ในกล่องสถานะ หากวันที่นั้นเคยประมวลผลไปแล้ว ระบบจะแจ้งว่าข้ามขั้นตอนสำรองข้อมูล (เพื่อกันข้อมูลซ้ำ) แต่ยังอัปเดต Excel ให้ตามปกติ

### Replenishment Summary (AI agent)
ใต้ส่วนรัน pipeline:
1. ปรับแถบเลื่อน **Shortage threshold** — กำหนดว่าสต็อกต่ำกว่าค่า forecast กี่ % จึงจะถูกดึงมาแจ้งเตือน (เช่น 30% หมายถึงเฉพาะรายการที่ขาดตั้งแต่ 30% ขึ้นไป)
2. กด **Run Agent** ระบบจะเริ่มการทำงานของ agent เพื่ออ่านข้อมูลวันนั้นจากไฟล์ CSV สำรองรายเดือน คัดกรองรายการที่ขาดสต็อกเกิน threshold แล้วให้ AI เขียนสรุปภาษาไทยสั้นๆ ว่าสาขา/SKU ใดต้องติดตาม
3. สรุปจะแสดงด้านล่างและค้างอยู่บนหน้าจอ ใช้ปุ่ม **Copy summary to clipboard** เพื่อคัดลอกไปวางในอีเมล, Teams เป็นต้น

> หมายเหตุ: agent อ่านข้อมูลจากไฟล์ CSV สำรอง ดังนั้นต้องรัน pipeline (อย่างน้อยถึงขั้นตอน `backup`) สำหรับวันที่นั้นก่อน จึงจะสร้างสรุปได้

---

## ขั้นสูง: การรันผ่าน Command Line

สำหรับการแก้ปัญหาหรือการรันแบบตั้งเวลาอัตโนมัติ สามารถรัน pipeline เดียวกันได้โดยไม่ต้องเปิดเบราว์เซอร์:

```bash
uv run main.py
```

### การรันแบบเลือกสเตป
```bash
uv run main.py --steps [all | transform | backup | excel]
```

* **`transform`**: ดึงข้อมูลจากไฟล์คาดการณ์และข้อมูลสาขา ทำความสะอาดข้อมูล และแคชไว้ที่ไฟล์ Parquet ในเครื่อง (`data/temp_transformed.parquet`)
* **`backup`**: อ่านข้อมูลจาก Parquet แคช ตรวจสอบว่ามีข้อมูลของวันที่ดังกล่าวอยู่แล้วหรือไม่ แล้วแนบข้อมูลต่อท้ายไฟล์ CSV รายเดือน (`data/FSRM_consolidated_[Month]_[Year].csv`) โดยข้ามรายการซ้ำ
* **`excel`**: อ่านไฟล์ CSV ล่าสุด ตรวจสอบความไม่ซ้ำซ้อนของข้อมูล แล้วสร้าง/อัปเดตตาราง Excel ปลายทางผ่าน `xlwings`

### กำหนดวันที่เอง
```bash
uv run main.py --day 15 --month 7 --year 2026
```
หากไม่ระบุ จะใช้วันที่ปัจจุบันโดยอัตโนมัติ

**ตัวอย่าง:**
```bash
# รันเฉพาะขั้นตอนสำรองข้อมูลและนำเข้า Excel โดยใช้แคชเดิมในเครื่อง
uv run main.py --steps backup excel

# รันใหม่เฉพาะขั้นตอน Excel หลังจากแก้ไขปัญหาไฟล์ถูกล็อกเสร็จสิ้น
uv run main.py --steps excel
```

---

## แก้ปัญหาเบื้องต้น

| อาการ | สาเหตุที่เป็นไปได้ / วิธีแก้ |
|---|---|
| "SharePoint sync directory not found" | ตรวจสอบว่าโฟลเดอร์ "Stock FSRM SSC" ซิงค์อยู่ในเครื่อง และ **SP_SYNC_PATH** ใน Settings ตรงกับ path จริงในเครื่องคุณ |
| "Wrong file name format" | ไฟล์สาขาบางไฟล์ในโฟลเดอร์สต็อกตั้งชื่อไม่ตรงตามรูปแบบที่กำหนด — ตรวจสอบว่า export ไฟล์ถูกต้อง |
| "Expected N files, found M" | ไฟล์สาขาบางไฟล์หายไปจากโฟลเดอร์ SharePoint ของวันนั้น หรือมีไฟล์อื่นที่ไม่เกี่ยวข้องปนอยู่ |
| ขั้นตอน Excel ล้มเหลวเพราะไฟล์ถูกล็อก | มีคนเปิดไฟล์ Excel ปลายทางค้างไว้ — ปิดไฟล์แล้วรันใหม่ด้วย `--steps excel` (CLI) หรือเลือกเฉพาะ `excel` ในแอป |
| "No summary generated: GEMINI_API_KEY not set" | เพิ่ม `GEMINI_API_KEY` ในไฟล์ `.env` |
| Replenishment Summary ว่างเปล่า/error สำหรับวันที่หนึ่ง | ตรวจสอบว่าได้รัน pipeline (อย่างน้อยถึงขั้นตอน `backup`) สำหรับวันที่นั้นแล้ว |
