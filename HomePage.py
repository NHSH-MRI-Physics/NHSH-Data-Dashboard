import streamlit as st
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from scipy import stats
import pandas as pd
import requests
import xmltodict
import datetime
import sys
from datetime import date, timedelta
import calendar
st.set_page_config(initial_sidebar_state='auto',page_title="NHSH MRI QA Data Dashboard")

st.title("NHSH MRI QA Data Dashboard")
st.markdown("""
""")

st.cache_data.clear()
st.cache_resource.clear()
conn = st.connection("gsheets", type=GSheetsConnection,ttl=1)

dfDQA = conn.read(worksheet="DailyQA")
dfDQA = dfDQA.drop_duplicates(keep='last')
dfDQA = dfDQA.fillna(value="Not Provided")
MedACRQA = conn.read(worksheet="MedACRQA")
MedACRQA = MedACRQA.fillna(value="Not Provided")
MedACRQA = MedACRQA.drop_duplicates(keep='last')

def GetScannerStatus(ScannerName):
    st.header(ScannerName+ " QA Status")
    dfDQAMRI = dfDQA[dfDQA["Scanner"] == ScannerName]
    if len(dfDQAMRI) == 0:
        st.markdown(f""" 
        ### Daily QA Status
        - No Daily QA data found for {ScannerName}.  
        """, unsafe_allow_html=True)
        return
    dfDQAMRI["Date_parsed"] = pd.to_datetime(dfDQAMRI["Date"], errors="coerce", format="%Y-%m-%d %H-%M-%S")
    Last_DQA_MRI = dfDQAMRI.loc[dfDQAMRI["Date_parsed"].idxmax()]["Date"]
    EntriesOnDate = dfDQAMRI[dfDQAMRI["Date"] == Last_DQA_MRI]

    #Daily QA Status
    DDQATestState = '<span style="color:red">Fail</span>'
    FailResults = EntriesOnDate[EntriesOnDate["Result"] == "Fail"]
    if len(FailResults) == 0:
        DDQATestState = '<span style="color:green">Pass</span>'

    NumberOfDaySinceLastDQA = (datetime.datetime.now() - datetime.datetime.strptime(Last_DQA_MRI, "%Y-%m-%d %H-%M-%S")).days
    QAInDate = '<span style="color:green">DailyQA is currently in date</span>'
    if NumberOfDaySinceLastDQA > 0:
        QAInDate = '<span style="color:red">DailyQA is currently ' + str(NumberOfDaySinceLastDQA) + ' days out of date</span>'
    

    
    DateOfLastQAFormatted = datetime.datetime.strptime(Last_DQA_MRI, "%Y-%m-%d %H-%M-%S").strftime('%d-%m-%Y %H:%M:%S')
    st.markdown(f""" 
    ### Daily QA Status
    - Last ran on {DateOfLastQAFormatted}.  
    - QA Type: {EntriesOnDate["QA Type"].values[0]}
    - The previous run result: {DDQATestState}.
    - {QAInDate}.
    """, unsafe_allow_html=True)


    #Monthly QA Status
    if ScannerName == "MRI 1":
        dfMonthlyMRI = MedACRQA[MedACRQA["ScannerSerialNumber"] == "00000000203MRS01"]
    else:
        dfMonthlyMRI = MedACRQA[MedACRQA["ScannerSerialNumber"] == "00000000203MRS02"]
    if len(dfMonthlyMRI) == 0:
        st.markdown(f""" 
        ### Monthly QA Status
        - No Monthly QA data found for {ScannerName}.  
        """, unsafe_allow_html=True)
        return


    dfMonthlyMRI["Date_parsed"] = pd.to_datetime(dfMonthlyMRI["DateScanned"], errors="coerce", format="%d-%m-%Y %H:%M:%S").dt.date

    Last_MonthlyQA_Date = dfMonthlyMRI.loc[dfMonthlyMRI["Date_parsed"].idxmax()]["Date_parsed"]
    EntriesOnDate = dfMonthlyMRI[dfMonthlyMRI["Date_parsed"] == Last_MonthlyQA_Date]

    def NextQADate():
        year = date.today().year
        month = date.today().month
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        while last_day.weekday() != 3:  # Thursday == 3 (Mon=0)
            last_day -= timedelta(days=1)
        return last_day
    def LastQADate():
        year = date.today().year
        month = date.today().month-1
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        while last_day.weekday() != 3:  # Thursday == 3 (Mon=0)
            last_day -= timedelta(days=1)
        return last_day

    
    NextQA_Date = NextQADate()
    PrevQA_Date = LastQADate()
    if PrevQA_Date <= Last_MonthlyQA_Date <= NextQA_Date:
        QAInDate = '<span style="color:green">MonthlyQA is currently in date</span>'   
    else:
        DaysOutOfDate = (date.today() - Last_MonthlyQA_Date).days
        QAInDate = '<span style="color:red">MonthlyQA is currently out of date by ' + str(DaysOutOfDate) + ' days</span>'   

         
    st.subheader("Monthly QA Status")
    st.markdown(f""" 
    - Last ran on {Last_MonthlyQA_Date.strftime('%d-%m-%Y')}.  
    - {QAInDate}.
    """, unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    GetScannerStatus("MRI 1")
with col2:
    GetScannerStatus("MRI 2")