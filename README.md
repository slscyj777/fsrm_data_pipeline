# FSRM Daily Pipeline — User Guide

This document explains how to install and run the FSRM stock pipeline on Windows. It covers the Streamlit app (use this for daily work) and the Agent Summary feature.

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

**Shortcut:** Steps 1 and 2 below run automatically when you double-click `scripts/setup.bat` in the project folder. This script installs `uv` if it is missing, then runs `uv sync`. If setup fails, the script prints the error and stays open so you can read it. You can also do these steps by hand — see below.

### Step 1: Open the project folder
```bash
cd path/to/your/folder
```

### Step 2: Install the dependencies
```bash
uv sync
```

### Step 3: Sync the SharePoint folder
Get access to the SharePoint folder named **"Stock FSRM SSC"**. Sync it, so it appears as a normal folder on your computer. The pipeline reads branch files and forecast files from this folder, and writes the output Excel file back to it.

### Step 4: Add the input files
Copy the master dimension file, the SKU dimension file, and the forecast file into `excel/input/`. You set these file names in the app Settings panel — see below.

### Step 5: Set the environment variable
1. Rename `.env.example` to `.env`.
2. Open `.env` and add `GEMINI_API_KEY`.

You need `GEMINI_API_KEY` only for the AI Summary feature. Without it, the pipeline still runs. Instead of a summary, you see a message that says no summary was generated.

---

## Run the app (use this for daily work)

Open a terminal and run this command:

```bash
uv run streamlit run st_app.py
```

**Shortcut:** Instead of this command, double-click `scripts/launch_ui.bat` in the project folder.

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

## Troubleshooting

| Message or symptom | Cause and fix |
|---|---|
| "SharePoint sync directory not found" | The "Stock FSRM SSC" folder is not synced locally, or **SP_SYNC_PATH** in Settings does not match the local path. Sync the folder and check the path. |
| "Wrong file name format" | A branch file in the stock subfolder does not follow the required naming pattern. Check that the file was exported correctly. |
| "Expected N files, found M" | Some branch files are missing from the day's SharePoint subfolder, or extra unrelated files are present. Check the folder contents. |
| Excel step fails with a file-lock error | Someone has the output Excel file open. Close the file, then rerun with `--steps excel` (command line) or select `excel` only (app). |
| "No summary generated: GEMINI_API_KEY not set" | `.env` is missing `GEMINI_API_KEY`. Add the key to `.env`. |
| Replenishment Summary is empty or shows an error | Run the pipeline for that date first, at least through the `backup` step. |

---

# คู่มือการใช้งานโปรเจกต์ (ภาษาไทย)

เอกสารนี้อธิบายวิธีติดตั้งและใช้งาน FSRM stock pipeline บน Windows ครอบคลุมแอป Streamlit (ใช้สำหรับงานประจำวัน) และฟีเจอร์ Agent Summary

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

**ทางลัด:** ขั้นตอนที่ 1 และ 2 ด้านล่างทำงานอัตโนมัติเมื่อดับเบิลคลิกไฟล์ `scripts/setup.bat` ในโฟลเดอร์โปรเจกต์ สคริปต์นี้จะติดตั้ง `uv` หากยังไม่มี แล้วรัน `uv sync` ต่อ หากตั้งค่าไม่สำเร็จ สคริปต์จะแสดงข้อผิดพลาดและค้างหน้าต่างไว้ให้อ่าน คุณสามารถทำขั้นตอนเหล่านี้ด้วยตนเองได้เช่นกัน — ดูด้านล่าง

### ขั้นตอนที่ 1: เปิดโฟลเดอร์โปรเจกต์
```bash
cd path/to/your/folder
```

### ขั้นตอนที่ 2: ติดตั้ง dependencies
```bash
uv sync
```

### ขั้นตอนที่ 3: ซิงค์โฟลเดอร์ SharePoint
ขอสิทธิ์เข้าถึงโฟลเดอร์ SharePoint ชื่อ **"Stock FSRM SSC"** แล้วซิงค์ให้ปรากฏเป็นโฟลเดอร์ปกติบนเครื่องคอมพิวเตอร์ pipeline จะอ่านไฟล์สาขาและไฟล์ forecast จากโฟลเดอร์นี้ และเขียนไฟล์ Excel ผลลัพธ์กลับไปที่โฟลเดอร์นี้เช่นกัน

### ขั้นตอนที่ 4: เพิ่มไฟล์ input
คัดลอกไฟล์ master dimension, ไฟล์ SKU dimension และไฟล์ forecast ไปวางที่ `excel/input/` คุณตั้งชื่อไฟล์เหล่านี้ได้จากหน้า Settings ในแอป — ดูด้านล่าง

### ขั้นตอนที่ 5: ตั้งค่า environment variable
1. เปลี่ยนชื่อไฟล์ `.env.example` เป็น `.env`
2. เปิดไฟล์ `.env` แล้วเพิ่ม `GEMINI_API_KEY`

คุณต้องใส่ `GEMINI_API_KEY` เฉพาะเมื่อต้องการใช้ฟีเจอร์ AI Summary หากไม่ใส่ pipeline ยังทำงานได้ตามปกติ แต่จะแสดงข้อความว่ายังไม่ได้สร้างสรุป แทนที่จะแสดงสรุปจริง

---

## การใช้งานแอป (ใช้สำหรับงานประจำวัน)

เปิด terminal แล้วรันคำสั่งนี้:

```bash
uv run streamlit run st_app.py
```

**ทางลัด:** แทนที่จะพิมพ์คำสั่งนี้ ให้ดับเบิลคลิกไฟล์ `scripts/launch_ui.bat` ในโฟลเดอร์โปรเจกต์

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

## แก้ปัญหาเบื้องต้น

| ข้อความหรืออาการ | สาเหตุและวิธีแก้ |
|---|---|
| "SharePoint sync directory not found" | โฟลเดอร์ "Stock FSRM SSC" ยังไม่ได้ซิงค์ในเครื่อง หรือ **SP_SYNC_PATH** ใน Settings ไม่ตรงกับ path จริง ให้ซิงค์โฟลเดอร์และตรวจสอบ path |
| "Wrong file name format" | ไฟล์สาขาบางไฟล์ในโฟลเดอร์สต็อกตั้งชื่อไม่ตรงตามรูปแบบที่กำหนด ให้ตรวจสอบว่า export ไฟล์ถูกต้อง |
| "Expected N files, found M" | ไฟล์สาขาบางไฟล์หายไปจากโฟลเดอร์ SharePoint ของวันนั้น หรือมีไฟล์อื่นที่ไม่เกี่ยวข้องปนอยู่ ให้ตรวจสอบเนื้อหาในโฟลเดอร์ |
| ขั้นตอน Excel ล้มเหลวเพราะไฟล์ถูกล็อก | มีคนเปิดไฟล์ Excel ปลายทางค้างไว้ ให้ปิดไฟล์ แล้วรันใหม่ด้วย `--steps excel` (command line) หรือเลือกเฉพาะ `excel` (แอป) |
| "No summary generated: GEMINI_API_KEY not set" | ไฟล์ `.env` ยังไม่มี `GEMINI_API_KEY` ให้เพิ่ม key ลงในไฟล์ `.env` |
| Replenishment Summary ว่างเปล่าหรือแสดง error | ให้รัน pipeline สำหรับวันที่นั้นก่อน อย่างน้อยถึงขั้นตอน `backup` |