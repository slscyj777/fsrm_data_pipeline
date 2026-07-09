import io
import re
import traceback
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from st_copy import copy_button


import streamlit as st
from pipeline.settings import load_settings, save_settings

from main import run_pipeline, month_folder_name
from agent_summary import run_agent_summary

PROJECT_ROOT = Path(__file__).resolve().parent


# label = help text shown next to each field; edit this dict to add/remove fields
SETTINGS_FIELDS = {
    "SUB_FOLDER_NAME": "SharePoint stock subfolder name",
    "FSRM_FOLDER": "FSRM output folder name",
    "SP_SYNC_PATH": "SharePoint sync path (eg. ******* Public Company Limited/**** **** - Stock FSRM SSC)",
    "MASTER_DIM_FILE": "Master dimension Excel filename eg dim.xlsx",
    "SKU_DIM_FILE": "SKU dimension Excel filename eg sku.xlsx",
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
st.title("FSRM Daily Pipeline")

with st.sidebar:
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
                save_settings(current, new_values)
                st.success("Success!")

if "running" not in st.session_state:
    st.session_state.running = False
if "agent_summary" not in st.session_state:
    st.session_state.agent_summary = False


picked_date = st.date_input("Stock date", value=date.today())
step_choice = st.multiselect(
    "Steps to run",
    ["all", "transform", "backup", "excel"],
    default=["all"],
    help="'all' runs everything. Select specific steps to re-run those parts.",
)

st.caption(
    f"Processing **{picked_date.strftime('%B %d, %Y')}**\n"
    f"\nFolder: **`{month_folder_name(picked_date.month, picked_date.year)}`**"
)

run_clicked = st.button(
    "Run pipeline",
    type="primary",
    disabled=st.session_state.running or not step_choice,
)
 
if run_clicked:
    st.session_state.running = True
    st.rerun()

if st.session_state.running:
    with st.status("Running pipeline...", expanded=True) as status:
        log_stream = StreamlitLogger(st.empty())
        try:
            with redirect_stdout(log_stream):
                results = run_pipeline(
                    steps=step_choice,
                    day=picked_date.day,
                    month=picked_date.month,
                    year=picked_date.year,
                )
            if results:
                st.info("Already processed this date — backup skipped, Excel refreshed as usual.")
            status.update(label="Success!", state="complete", expanded=True)
        except (FileNotFoundError, ValueError) as e:
            status.update(label="Pipeline failed", state="error", expanded=True)
            st.error(str(e))
        except Exception:
            status.update(label="Pipeline failed — unexpected error", state="error", expanded=True)
            st.error("Something went wrong. Check stack trace below.")
            with st.expander("Technical details"):
                st.code("\n" + traceback.format_exc())
        finally:
            st.session_state.running = False


with st.container(border=True) as c:
    threshold_pct = st.slider("Shortage threshold (% below forecast)", 5, 100, 30) / 100
    run_agent = st.button(
        "Agent summary",
        type="primary",
        disabled= not picked_date,
    )


    if run_agent:
        with st.status("Generating summary...", expanded=True) as status:
            st.session_state.agent_summary = run_agent_summary(
                stock_date=picked_date,
                threshold_pct=threshold_pct
            )
            status.update(label="Success!", state="complete", expanded=True)

    # Persistent presentation layer
    if st.session_state.agent_summary:
        st.subheader("Replenishment Summary")
        st.markdown(st.session_state.agent_summary)

        copy_button(st.session_state.agent_summary, tooltip="Copy summary to clipboard")