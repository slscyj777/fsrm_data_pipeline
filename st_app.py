import io
import re
import traceback
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path


import streamlit as st
from pipeline.settings import load_settings, save_settings

from main import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"

# label = help text shown next to each field; edit this dict to add/remove fields
SETTINGS_FIELDS = {
    "SUB_FOLDER_NAME": "SharePoint stock subfolder name",
    "FSRM_FOLDER": "FSRM output folder name",
    "SP_SYNC_PATH": "SharePoint sync path (eg. ******* Public Company Limited/**** **** - Stock FSRM SSC)",
    "MASTER_DIM_FILE": "Master dimension Excel filename",
    "SKU_DIM_FILE": "SKU dimension Excel filename",
    "FORECAST_FILE": "forecast Excel filename",
    "OUTPUT_FILE": "Output Excel filename",
}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

def clean_log(text: str) -> str:
    return ANSI_RE.sub("", text).replace("\r", "\n")

class StreamlitLogger(io.StringIO):
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder

    def write(self, s):
        super().write(s)
        self.placeholder.code(clean_log(self.getvalue()), language="text")
        return len(s)


st.set_page_config(page_title="FSRM Pipeline", layout="centered")
st.title("FSRM Data Pipeline")

with st.expander("⚙️ Settings"):
    current = load_settings()
    new_values = {
        key: st.text_input(key, value=current.get(key, ""), help=help_text)
        for key, help_text in SETTINGS_FIELDS.items()
    }
    if st.button("Save settings"):
        missing = [key for key, value in new_values.items() if not value]
        if missing:
            st.error(f"These fields cannot be empty: {', '.join(missing)}")
        else:
            save_settings(new_values)
            st.success("Success!")

picked_date = st.date_input("Stock date to process", value=date.today())
step_choice = st.multiselect(
    "Steps to run",
    ["all", "transform", "backup", "excel"],
    default=["all"],
    help="'all' runs everything. Select specific steps to re-run those parts.",
)

if st.button("Run pipeline", type="primary", disabled=not step_choice):
    with st.status("Running pipeline...", expanded=True) as status:
        log_stream = StreamlitLogger(st.empty())
        try:
            with redirect_stdout(log_stream):
                run_pipeline(
                    steps=step_choice,
                    day=picked_date.day,
                    month=picked_date.month,
                    year=picked_date.year,
                )
            status.update(label="Success!", state="complete", expanded=True)
        except Exception:
            log_stream.write("\n" + traceback.format_exc())
            status.update(label="Pipeline failed — see log below.", state="error", expanded=True)
