import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Paralympics Dashboard",
    page_icon=":sports_medal:",
    layout="wide"
)

data = {
    "Year": [2012, 2016, 2020, 2012, 2016, 2020, 2012, 2016, 2020],
    "Country": [
        "Spain", "Spain", "Spain",
        "USA", "USA", "USA",
        "China", "China", "China"
    ],
    "Gold_Medals": [8, 9, 10, 36, 40, 38, 95, 107, 96],
    "Athletes": [120, 130, 140, 300, 320, 310, 280, 290, 300]
}

df = pd.DataFrame(data)

st.title(":sports_medal: Paralympic Games Dashboard")
st.markdown("Example dashboard with dummy data")

st.sidebar.header("Filters")

selected_country = st.sidebar.selectbox(
    "Select Country",
    df["Country"].unique()
)

filtered_df = df[df["Country"] == selected_country]

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Total Gold Medals",
        value=filtered_df["Gold_Medals"].sum()
    )

with col2:
    st.metric(
        label="Total Athletes",
        value=filtered_df["Athletes"].sum()
    )

fig_medals = px.line(
    filtered_df,
    x="Year",
    y="Gold_Medals",
    markers=True,
    title=f"Gold Medals Evolution - {selected_country}"
)

st.plotly_chart(fig_medals, use_container_width=True)

fig_athletes = px.bar(
    filtered_df,
    x="Year",
    y="Athletes",
    title=f"Athletes Participation - {selected_country}"
)

st.plotly_chart(fig_athletes, use_container_width=True)

st.subheader("Dataset")
st.dataframe(filtered_df)