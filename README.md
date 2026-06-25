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

### 4. Configure Environment Variables
* Rename the file `.env.example` to `.env`.
* Open `.env` in an editor and add your environment variables.

---

## Running the Application

Once the setup is complete, execute the main script:

```bash
uv run main.py
```

---


Extra
DAY = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]




