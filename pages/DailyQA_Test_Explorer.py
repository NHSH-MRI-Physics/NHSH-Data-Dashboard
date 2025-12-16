import streamlit as st
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from scipy import stats
import pandas as pd
pd.options.mode.chained_assignment = None
import requests
import xmltodict
import datetime
import sys
from datetime import date, timedelta
import calendar
from scipy import stats
from dataclasses import dataclass
from streamlit_calendar import calendar

st.title("NHSH MRI QA Data Dashboard: Daily QA Test Explorer")

#st.cache_data.clear()
#st.cache_resource.clear()
conn = st.connection("gsheets", type=GSheetsConnection,ttl=None)

df = conn.read(worksheet="DailyQA")
df = df.fillna(value="No Data")
df = df.drop_duplicates(keep='last')

class DataEntry:
    def __init__(self,sequences,sliceCount):
        self.ROI = {}
        slices = [f"Slice {i+1} ROI" for i in range(sliceCount)]
        for sequence in sequences:
            for slice in slices:
                self.ROI[sequence][slice] = {}
        self.date = None
        self.scanner = None
        self.archivePath = None
        self.QaType = None
        self.result = None
        self.avgSNR = None

Rows = {}
for index, row in df.iterrows():
    Date = row['Date']
    if Date not in Rows:
        Rows[Date] = [row]
    else:
        Rows[Date].append(row)

events = []
for Date in Rows:
    Event = {
        "title": "DQA",
        "start": Date,
        "end": Date,
    }
    events.append(Event)

calendar_options = {
    "editable": "False",
    "navLinks": "False",
    "selectable": "true",
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridDay,dayGridWeek,dayGridMonth",
    },
    "initialView": "dayGridMonth",
}

state = calendar(
    events=st.session_state.get("events", events),
    options=calendar_options,
    custom_css="""
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: 700;
    }
    .fc-toolbar-title {
        font-size: 2rem;
    }
    """,
    key="daygrid",
)

if state.get("eventsSet") is not None:
    st.session_state["events"] = state["eventsSet"]

st.write(state)

st.markdown("## API reference")
st.help(calendar)