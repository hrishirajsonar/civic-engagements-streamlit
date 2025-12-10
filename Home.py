import streamlit as st

st.set_page_config(layout="wide")


st.components.v1.iframe(
    "https://public.tableau.com/views/CivicEngagementsPhase2/Dashboard1?:embed=yes&:showVizHome=no&:toolbar=no",
    width=2400,     # any large value is fine once CSS is applied
    height=2200  
)