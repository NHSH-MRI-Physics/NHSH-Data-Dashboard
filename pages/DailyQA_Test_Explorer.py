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
if "current_slice" not in st.session_state:
    st.session_state.current_slice = 1

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
    #print(datetime.datetime.strptime(Date, "%Y-%m-%d %H-%M-%S").strftime("%Y-%m-%dT%H:%M:%S"))
    #print((datetime.datetime.strptime(Date, "%Y-%m-%d %H-%M-%S")+timedelta(hours=0.25)).strftime("%Y-%m-%dT%H:%M:%S"))
    #print(" ")
    Event = {
        "allDay": True,
        "title": Rows[Date][0]['Scanner'] + " - " + Rows[Date][0]['QA Type'].split("_")[1],
        "start": datetime.datetime.strptime(Date, "%Y-%m-%d %H-%M-%S").strftime("%Y-%m-%d"),
        "end": (datetime.datetime.strptime(Date, "%Y-%m-%d %H-%M-%S")+timedelta(hours=0.25)).strftime("%Y-%m-%d"),
        "color": "#FF6C6C",
            }
    events.append(Event)


Test =     {
        "title": "Event 17",
        "color": "#FFBD45",
        "start": "2025-12-03T15:30:00",
        "end": "2025-12-03T16:30:00",
            }
Test2 = {
            "title": "Event 1",
        "color": "#FF6C6C",
        "start": "2025-12-05",
        "end": "2025-12-05",
        "resourceId": "a",
}

#events.append(Test)         
#events.append(Test2) 

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

SelectedTest = None
FoundTest = False
if "callback" in state and state["callback"] is not None:
    if state["callback"] == "eventClick":
        SelectedDate = state["eventClick"]["event"]["start"]
        Scanner = state["eventClick"]["event"]["title"].split(" - ")[0]
        QAtype = state["eventClick"]["event"]["title"].split(" - ")[1]
        SelectedTest = None
        for Date in Rows:
            if Date.split()[0] == SelectedDate:
                if Rows[Date][0]['Scanner'] == Scanner:
                    if Rows[Date][0]['QA Type'].split("_")[1] == QAtype:
                        SelectedTest = []
                        for Seq in Rows[Date]:
                            SelectedTest.append(Seq)
                        FoundTest=True

if FoundTest == True:
    st.divider()    
    st.header("Selected Test Details")
    col1, col2 = st.columns(2)
    with col1:
        SeqResults= "\n"
        for i in range(len(SelectedTest)):
            Result = QAInDate = '<span style="color:green">Pass</span>'
            if SelectedTest[i]['Result'] != "Pass":
                Result = '<span style="color:red">Fail</span>'
            SeqResults += "**Sequence:** " + SelectedTest[i]['Sequence'] +"\n"
            SeqResults += "- Result: " + Result  +"\n"
            SeqResults += "- Average SNR: " + str(round(SelectedTest[i]['SNR Avg'],2)) + "\n\n"

        st.markdown(f""" 
        - Scanner: {SelectedTest[0]['Scanner']}  
        - QA Type: {SelectedTest[0]['QA Type']}
        - Date Run: {SelectedTest[0]['Date']}
        """, unsafe_allow_html=True)
        st.markdown(SeqResults, unsafe_allow_html=True)
    
    with col2:
        Sequences = []
        for i in range(len(SelectedTest)):
            Sequences.append(SelectedTest[i]['Sequence'])
        option = st.selectbox("Choose a Sequence", Sequences, key="sequence_option")
        # detect change of selected sequence and reset current slice
        if "prev_sequence" not in st.session_state:
            st.session_state.prev_sequence = option
        elif st.session_state.prev_sequence != option:
            st.session_state.prev_sequence = option
            st.session_state.current_slice = 1
            st.rerun()

        for i in range(len(SelectedTest)):
            if SelectedTest[i]['Sequence'] == option:
                ChosenSequence = SelectedTest[i]
        ChosenSequence = ChosenSequence[ChosenSequence != "No Data"]
        MaxSlices = int(ChosenSequence.keys()[-1].split()[1])

        OfflineMode = False
        if OfflineMode== False:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            if SelectedTest[0]['QA Type'] == "DQA_Head": #draw a circle
                circle = plt.Circle((0.5, 0.5), 0.4, color='blue', fill=False, linewidth=2)
                ax.add_artist(circle)

                x = (0.5, 0.5)
                width = 0.15
                Square1 = plt.Rectangle((x[0]-width/2.0, x[1]-width/2.0), width, width, color='green', fill=False, linewidth=2)
                ax.add_artist(Square1)
                plt.text(x[0],x[1], '1', fontsize=22, va='center', ha='center',color='green')
                plt.text(x[0], x[1]+0.1, str(round(ChosenSequence['Slice ' + str(st.session_state.current_slice) + ' M1'],2)), fontsize=11, va='center', ha='center',color='green')

                x = (0.7, 0.35)
                Square2 = plt.Rectangle((x[0]-width/2.0, x[1]-width/2.0), width, width, color='green', fill=False, linewidth=2)
                ax.add_artist(Square2)
                plt.text(x[0], x[1], '2', fontsize=22, va='center', ha='center',color='green')
                plt.text(x[0], x[1]+0.1, str(round(ChosenSequence['Slice ' + str(st.session_state.current_slice) + ' M2'],2)), fontsize=11, va='center', ha='center',color='green')

                x = (0.3, 0.65)
                Square3 = plt.Rectangle((x[0]-width/2.0, x[1]-width/2.0), width, width, color='green', fill=False, linewidth=2)
                ax.add_artist(Square3)
                plt.text(x[0], x[1], '3', fontsize=22, va='center', ha='center',color='green')
                plt.text(x[0], x[1]+0.1, str(round(ChosenSequence['Slice ' + str(st.session_state.current_slice) + ' M3'],2)), fontsize=11, va='center', ha='center',color='green')

                x = (0.7, 0.65)
                Square4 = plt.Rectangle((x[0]-width/2.0, x[1]-width/2.0), width, width, color='green', fill=False, linewidth=2)
                ax.add_artist(Square4)
                plt.text(x[0], x[1], '4', fontsize=22, va='center', ha='center',color='green')
                plt.text(x[0], x[1]+0.1, str(round(ChosenSequence['Slice ' + str(st.session_state.current_slice) + ' M4'],2)), fontsize=11, va='center', ha='center',color='green')

                x = (0.3, 0.35)
                Square5 = plt.Rectangle((x[0]-width/2.0, x[1]-width/2.0), width, width, color='green', fill=False, linewidth=2)
                ax.add_artist(Square5)
                plt.text(x[0], x[1], '5', fontsize=22, va='center', ha='center',color='green')
                plt.text(x[0], x[1]+0.1, str(round(ChosenSequence['Slice ' + str(st.session_state.current_slice) + ' M5'],2)), fontsize=11, va='center', ha='center',color='green')

                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)

        ax.set_axis_off()
        ax.set_aspect('equal', adjustable='box')
        ax.set_title('Slice ' + str(st.session_state.current_slice))
        st.pyplot(fig) # instead of plt.show()
        button_col1, button_spacer, button_col2 = st.columns([1, 1.6, 1])
        with button_col1:
            PrevSlice = st.button("Previous Slice")
            if PrevSlice:
                st.session_state.current_slice -= 1
                if st.session_state.current_slice < 1:
                    st.session_state.current_slice = MaxSlices
                st.rerun()
        with button_col2:
            NextSlice = st.button("Next Slice")
            if NextSlice:
                st.session_state.current_slice += 1
                if st.session_state.current_slice > MaxSlices:
                    st.session_state.current_slice = 1
                st.rerun()


        import urllib.request
        urllib.request.urlretrieve("https://github.com/NHSH-MRI-Physics/DailyQA/raw/refs/heads/main/BaselineData/Head/ROI_Head_Baseline.npy", "test.npy")
        import numpy as np  
        import os
        dir_path = os.path.dirname(os.path.realpath(__file__))
        ROIBaseline = np.load("test.npy",allow_pickle=True).item()
        st.write(ROIBaseline)
        urllib.request.urlretrieve("https://github.com/NHSH-MRI-Physics/DailyQA/raw/refs/heads/main/DQA_Scripts/Thresholds.txt", "test.txt")
        f = open("test.txt")
        st.write(f.read())