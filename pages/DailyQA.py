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

st.title("NHSH MRI QA Data Dashboard: Daily QA Overview")

option = st.selectbox(
    "Choose a scanner",
    ("MRI 1", "MRI 2"),
)

SigDeg = st.checkbox("Only show regression results which are degrading over time (significant negative slope)")


st.cache_data.clear()
st.cache_resource.clear()
conn = st.connection("gsheets", type=GSheetsConnection,ttl=1)

df = conn.read(worksheet="DailyQA")
df = df.fillna(value="No Data")
df = df.drop_duplicates(keep='last')
df = df[df["Scanner"] == option]
df["Date"] = pd.to_datetime(df["Date"], errors='coerce',dayfirst=True, format="%Y-%m-%d %H-%M-%S")

dStart = st.date_input("Show data from this date", value=df["Date"].min(),format="DD-MM-YYYY")
dEnd = st.date_input("Show data to this date", value=datetime.date.today(),format="DD-MM-YYYY")
df = df[(df["Date"] >= pd.to_datetime(dStart)) & (df["Date"] <= pd.to_datetime(dEnd))]


def MakePlots(Seq,df,Title,NumberOfSlices):
    st.subheader(Title)

    # Filter DataFrame for the specified sequence
    df_Filtered  = df[df["Sequence"] == Seq]
    if len(df_Filtered) == 0:
        st.markdown(f""" 
        - No Daily QA data found for sequence {Seq}.  
        """, unsafe_allow_html=True)
        return

    #df_Filtered["Date"] = pd.to_datetime(df_Filtered["Date"], errors='coerce',dayfirst=True, format="%Y-%m-%d %H-%M-%S")
    df_Filtered["SNR Avg"] = pd.to_numeric(df_Filtered["SNR Avg"], errors='coerce')
    df_Filtered["Date_numeric"] = (df_Filtered["Date"] - df_Filtered["Date"].min()).dt.days

    #Get regression results - convert to DataFrame for display
    slice_cols = [c for c in df_Filtered.columns if str(c).startswith("Slice")]
    
    def _regress(name, series):
        ser = pd.to_numeric(series, errors="coerce")
        mask = df_Filtered["Date_numeric"].notna() & ser.notna()
        n = int(mask.sum())
        if n >= 2:
            res = stats.linregress(df_Filtered.loc[mask, "Date_numeric"], ser[mask])
            # calculate 95% confidence interval for the slope
            t_crit = stats.t.ppf(0.975, n - 2)  # two-tailed t-critical value
            ci_lower = res.slope - t_crit * res.stderr
            ci_upper = res.slope + t_crit * res.stderr
            return {
                "metric": name,
                "slope": res.slope,
                "95% Confidence Lower": ci_lower,
                "95% Confidence Upper": ci_upper,
                "intercept": res.intercept,
                "rvalue": res.rvalue,
                "pvalue": res.pvalue,
                "stderr": res.stderr,
                "n": n,
            }
        else:
            return {"metric": name, "slope": None, "95% Confidence Lower": None, "95% Confidence Upper": None, "intercept": None, "rvalue": None, "pvalue": None, "stderr": None, "n": n}

    results = []
    results.append(_regress("SNR Avg", df_Filtered["SNR Avg"]))
    for col in slice_cols[: 5 * NumberOfSlices]:
        results.append(_regress(col, df_Filtered[col]))

    df_regression = pd.DataFrame(results).set_index("metric")
    st.subheader("Regression results")
    cols_to_display = ["slope", "95% Confidence Lower", "95% Confidence Upper", "pvalue", "n"]

    def color_coding(row):
        return ['background-color:red'] * len(
            row) if row.pvalue <=0.05 and row.slope<0 else ['background-color:green'] * len(row)

    metrics = df_regression.index.tolist()
    if SigDeg:
        df_regression = df_regression[df_regression["pvalue"] <= 0.05]
        df_regression = df_regression[df_regression["slope"] < 0]
    st.dataframe(df_regression[cols_to_display].style.apply(color_coding, axis=1), use_container_width=True, height=150)


    
    selected = st.selectbox("Select metric to plot", metrics, key=f"select_{Seq}")

    if selected:
        fig_T2 = px.scatter(df_Filtered,color="Result",color_discrete_sequence=["green", "red"] ,x="Date", y=selected, title=selected,hover_data=["Date","QA Type","Sequence","Result","Scanner","Archive"])
        fig_T2.update_xaxes(title_text="Scan Date")
        fig_T2.update_yaxes(title_text="SNR")
        

        for res in results:
            if res["metric"] == selected:
                x_min = df_Filtered["Date"].min()
                x_max = df_Filtered["Date"].max()
                x_range = pd.date_range(start=x_min, end=x_max, periods=100)
                x_numeric = (x_range - df_Filtered["Date"].min()).days
                y_line = res["slope"] * x_numeric + res["intercept"]
                fig_T2.add_scatter(x=x_range, y=y_line, mode='lines', name='Regression line', line=dict(color='blue', width=2))

        st.plotly_chart(fig_T2)

st.header("Head Daily QA")
MakePlots("Ax T2 FSE head",df[df['QA Type'] == 'DQA_Head'], "Head Daily QA - T2 Sequence", 5)
MakePlots("Ax EPI-GRE head",df[df['QA Type'] == 'DQA_Head'], "Head Daily QA - EPI Sequence", 14)

st.header("Body Daily QA")
MakePlots("Ax T2 SSFSE TE 90 Top",df[df['QA Type'] == 'DQA_Body'], "Top Body Daily QA - T2 Sequence", 12) 
MakePlots("Ax T2 SSFSE TE 90 Bot",df[df['QA Type'] == 'DQA_Body'], "Bot Body Daily QA - T2 Sequence", 12) 
MakePlots("Ax EPI-GRE body Top",df[df['QA Type'] == 'DQA_Body'], "Top Body Daily QA - EPI Sequence", 13) 
MakePlots("Ax EPI-GRE body Bot",df[df['QA Type'] == 'DQA_Body'], "Bot Body Daily QA - EIP Sequence", 13) 

st.header("Spine Daily QA")
MakePlots("Ax T2 SSFSE TE 90 Top",df[df['QA Type'] == 'DQA_Spine'], "Top Spine Daily QA - T2 Sequence", 12) 
MakePlots("Ax T2 SSFSE TE 90 Bot",df[df['QA Type'] == 'DQA_Spine'], "Bot Spine Daily QA - T2 Sequence", 12) 
MakePlots("Ax EPI-GRE body Top",df[df['QA Type'] == 'DQA_Spine'], "Top Spine Daily QA - EPI Sequence", 12) 
MakePlots("Ax EPI-GRE body Bot",df[df['QA Type'] == 'DQA_Spine'], "Bot Spine Daily QA - EPI Sequence", 12) 