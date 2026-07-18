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

if submit:
    missing_fields = (
        not full_name or
        not employee_id or
        photo is None
    )

    if missing_fields:
        st.error(
            ":material/error: Please provide the full name, employee ID, "
            "and upload a face image before registering."
        )
    else:
        with st.spinner("Extracting face embedding and saving the record..."):
            try:
                files = {
                    "photo": (
                        photo.name,
                        photo.getvalue(),
                        photo.type,
                    )
                }

                data = {
                    "name": full_name,
                    "employee_id": employee_id,
                    "access_level": access_level,
                }

                # ArcFace extraction
                response = requests.post(
                    f"{API_URL}/enroll",
                    data=data,
                    files=files,
                    timeout=15,
                )

                if response.status_code == 200:
                    st.success(
                        f":material/check_circle: {full_name} was registered successfully."
                    )
                else:
                    # return a message
                    st.error(
                        f":material/cancel: Registration failed "
                        f"({response.status_code})\n\n{response.text}"
                    )

            except requests.exceptions.RequestException as exc:
                st.error(
                    f":material/cloud_off: Unable to connect to the API.\n\n{exc}"
                )