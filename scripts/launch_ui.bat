@echo off
cd /d "%~dp0.."

uv run streamlit run st_app.py
pause