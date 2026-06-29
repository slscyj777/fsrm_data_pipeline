# Project Setup Guide

This guide details the steps required to set up and run the application on **Windows**.

---

## Prerequisites

Before starting, ensure you have `uv` installed. If you haven't installed it yet, run the following command in your PowerShell terminal:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Installation & Setup

Follow these steps in your terminal to configure the project environment:

### 1. Navigate to the Project Directory
Change your current directory to the folder containing the project files:
```bash
cd path/to/your/folder
```

### 2. Synchronize Dependencies
Install the required dependencies using `uv`:
```bash
uv sync
```

### 3. Add Input Files
Place your required **Excel input files** into the input folder.
Get access to "Stock FSRM SSC" sharepoint folder and sync to add a PATH to your laptop

### 4. Configure Environment Variables
* Rename the file `.env.example` to `.env`.
* Open `.env` in an editor and add your environment variables.

---

## Running the Application

### Basic Execution
To execute the complete data pipeline end-to-end (Extraction -> Transformation -> Caching -> Backup -> Excel), run:

```bash
uv run main.py
```

### Advanced Execution (Pipeline Slices)
The pipeline is divided into modular segments. If a specific downstream layer fails (e.g., an Excel file lock error on SharePoint), you can re-run individual or combined slices using the `--steps` flag without executing the heavy transformation layer again.

```bash
uv run main.py --steps [all | transform | backup | excel]
```

* **`transform`**: Extracts raw forecast files and branch data, executes data cleansing pipelines, and caches to a fast local Parquet file (`data/temp_transformed.parquet`).
* **`backup`**: Reads the Parquet cache, evaluates if data for that run date already exists, and appends rows to the monthly CSV file (`data/FSRM_consolidated_[Month]_[Year].csv`) while skipping duplicates.
* **`excel`**: Reads the updated CSV file, executes an in-memory data integrity check to guarantee global uniqueness, and builds/updates target Excel sheets via `xlwings`.

**Examples:**
```bash
# Run only the backup and excel delivery steps from local cache
uv run main.py --steps backup excel

# Re-run only the Excel layer after a file-lock failure is resolved
uv run main.py --steps excel
```

---

# คู่มือการตั้งค่าโปรเจกต์ (Thai Ver.)

คู่มือนี้จะอธิบายขั้นตอนที่จำเป็นในการตั้งค่าและรันแอปพลิเคชันบน **Windows**

---

## สิ่งที่ต้องเตรียมก่อนเริ่ม (Prerequisites)

ก่อนเริ่มต้น ตรวจสอบให้แน่ใจว่าคุณได้ติดตั้ง `uv` เรียบร้อยแล้ว หากยังไม่ได้ติดตั้ง ให้รันคำสั่งต่อไปนี้ใน PowerShell terminal ของคุณ:

```powershell
powershell -ExecutionPolicy ByPass -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
```

---

## การติดตั้งและการตั้งค่า (Installation & Setup)

ทำตามขั้นตอนต่อไปนี้ใน terminal เพื่อตั้งค่าสภาพแวดล้อมของโปรเจกต์:

### 1. ไปยังโฟลเดอร์ของโปรเจกต์
เปลี่ยน directory ไปยังโฟลเดอร์ที่เก็บไฟล์โปรเจกต์:
```bash
cd path/to/your/folder
```

### 2. ซิงค์ Dependencies
ติดตั้ง dependencies ที่จำเป็นโดยใช้ `uv`:
```bash
uv sync
```

### 3. เพิ่มไฟล์ Input
* นำไฟล์ **Excel input** ที่จำเป็นไปใส่ไว้ในโฟลเดอร์ input
* ขอสิทธิ์เข้าถึงโฟลเดอร์ SharePoint "Stock FSRM SSC" และทำการซิงค์ (sync) เพื่อเชื่อมโยง PATH เข้ากับแล็ปท็อปของคุณ

### 4. ตั้งค่า Environment Variables
* เปลี่ยนชื่อไฟล์จาก `.env.example` เป็น `.env`
* เปิดไฟล์ `.env` ด้วยโปรแกรมแก้ไขข้อความ (editor) แล้วใส่ค่า environment variables ของคุณ

---

## การรันแอปพลิเคชัน (Running the Application)

### การรันแบบปกติ
หากต้องการรันกระบวนการของท่อส่งข้อมูล (Pipeline) ทั้งหมดตั้งแต่ต้นจนจบ (การดึงข้อมูล -> การแปลงข้อมูล -> การแคช -> การสำรองข้อมูล -> Excel) ให้ใช้คำสั่ง:

```bash
uv run main.py
```

### การรันแบบเลือกสเตป/แบ่งส่วน (Pipeline Slices)
โครงสร้างโปรเจกต์ถูกออกแบบให้แยกจากกันเป็นโมดูล หากเกิดข้อผิดพลาดที่เลเยอร์ปลายทาง (เช่น ไฟล์ Excel บน SharePoint ถูกเปิดค้างไว้โดยผู้ใช้อื่น) คุณสามารถเลือกสั่งรันเฉพาะบางขั้นตอนได้ผ่านการใช้แฟล็ก `--steps` โดยไม่ต้องประมวลผลขั้นตอนการแปลงข้อมูลใหม่ทั้งหมดให้เสียเวลา

```bash
uv run main.py --steps [all | transform | backup | excel]
```

* **`transform`**: ดึงข้อมูลจากไฟล์คาดการณ์และข้อมูลสาขา ทำความสะอาดข้อมูล และบันทึกสถานะไว้ในรูปแบบ Parquet แคชในเครื่อง (`data/temp_transformed.parquet`) อย่างรวดเร็ว
* **`backup`**: อ่านข้อมูลจาก Parquet แคช ตรวจสอบว่ามีข้อมูลของวันที่ดังกล่าวในระบบหรือยัง จากนั้นแนบข้อมูลต่อท้ายไฟล์ CSV สำรองรายเดือน (`data/FSRM_consolidated_[Month]_[Year].csv`) โดยจะข้ามอัตโนมัติหากพบวันที่ซ้ำกัน
* **`excel`**: อ่านข้อมูลจากไฟล์ CSV ล่าสุด ทำการตรวจสอบความถูกต้อง (Data Integrity) ในหน่วยความจำเพื่อยืนยันว่าไม่มีข้อมูลซ้ำซ้อน จากนั้นอัปเดตข้อมูลลงตาราง Excel ผ่าน `xlwings`

**ตัวอย่างการใช้งาน:**
```bash
# รันเฉพาะขั้นตอนสำรองข้อมูลและนำเข้า Excel โดยใช้ข้อมูลแคชเดิมในเครื่อง
uv run main.py --steps backup excel

# รันใหม่เฉพาะขั้นตอนนำเข้า Excel หลังจากแก้ไขปัญหาไฟล์ถูกล็อกเสร็จสิ้น
uv run main.py --steps excel
```




