import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")

st.set_page_config(
    page_title="Facial Access Control",
    page_icon=":material/badge:"
)

st.title(":material/person_add: Register Person")
st.caption("Register a new person in the facial recognition system.")

with st.form("registration_form", clear_on_submit=True):
    full_name = st.text_input("Full Name")
    employee_id = st.text_input("Employee ID")
    access_level = st.selectbox(
        "Access Level",
        ["Visitor", "Employee", "Administrator"]
    )
    photo = st.file_uploader(
        "Face Image",
        type=["jpg", "jpeg", "png"]
    )

    if photo is not None:
        st.image(photo, caption="Preview", width=200)

    submit = st.form_submit_button(
        ":material/how_to_reg: Register"
    )