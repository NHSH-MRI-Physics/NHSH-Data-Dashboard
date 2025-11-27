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
dfDQA = dfDQA.fillna(value="Not Provided")
MedACRQA = conn.read(worksheet="MedACRQA")
MedACRQA = MedACRQA.fillna(value="Not Provided")

DDQATestState = '<span style="color:red">failed</span>'
if dfDQA.iloc[-1]["Result"] == "Pass":
    DDQATestState = '<span style="color:green">passed</span>'

last_qa_date = pd.to_datetime(dfDQA.iloc[-1]["Date"], format="%Y-%m-%d %H-%M-%S")
NumberOfDaySinceLastDQA = (datetime.datetime.now() - last_qa_date).days
QAInDate = '<span style="color:green">DailyQA is currently in date</span>'
if NumberOfDaySinceLastDQA > 0:
    QAInDate = '<span style="color:red">DailyQA is currently ' + str(NumberOfDaySinceLastDQA) + ' days out of date</span>'

st.subheader("Daily QA Status")
st.markdown(f""" 
- Last ran on {dfDQA.iloc[-1]['Date']}.  
- The previous run result: {DDQATestState}.
- {QAInDate}.
""", unsafe_allow_html=True)


last_qa_date = pd.to_datetime(MedACRQA.iloc[-1]["DateScanned"], format="%d-%m-%Y %H:%M:%S")
NumberOfDaySinceLast_MonthlyQA = (datetime.datetime.now() - last_qa_date).days

def LastDueQADate():
    year = date.today().year
    month = date.today().month
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    while last_day.weekday() != 3:  # Thursday == 3 (Mon=0)
        last_day -= timedelta(days=1)
    return last_day

QAInDate = '<span style="color:green">MonthlyQA is currently in date</span>'
LastQADueDate = LastDueQADate()
if date.today() > LastQADueDate: #If we area passed the last QA due date this month
    if LastQADueDate - last_qa_date.date() >= timedelta(days=7): #And the last QA was done over a week ago then flag as out of date
        days_out_of_date = (date.today() - LastQADueDate).days
        QAInDate = '<span style="color:red">MonthlyQA is currently out of date by ' + str(days_out_of_date) + ' days</span>'
    
st.subheader("Monthly QA Status")
st.markdown(f""" 
- Last ran on {MedACRQA.iloc[-1]['DateScanned']}.  
- {QAInDate}.
""", unsafe_allow_html=True)
