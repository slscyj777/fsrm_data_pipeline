@echo off
cd /d "%~dp0.."

uv run streamlit run streamlit_app.py
pause