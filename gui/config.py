from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

API_URL = os.getenv("API_URL_INTERNAL")

st.set_page_config(
    page_title="Face Access Control System",
    page_icon=":material/badge:"
)