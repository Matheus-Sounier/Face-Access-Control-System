import base64
from io import BytesIO

import streamlit as st
import requests
from services.api_client import get_unknown_faces, regenerate_description

def unknown_faces_page():
    st.title(":material/person_search: Unknown Faces")
    st.caption("Recent access attempts by faces that couldn't be matched, with AI-generated descriptions.")

    limit = st.slider("Number of recent attempts to show", min_value=5, max_value=50, value=20, step=5)

    if st.button(":material/refresh: Refresh"):
        st.rerun()

    try:
        response = get_unknown_faces(limit)
    except requests.exceptions.RequestException as exc:
        st.error(f":material/cloud_off: Unable to connect to the API.\n\n{exc}")
        return

    if response.status_code != 200:
        st.error(f":material/error: Error ({response.status_code}): {response.text}")
        return

    faces = response.json()["faces"]

    if not faces:
        st.info(":material/info: No unrecognized access attempts logged yet.")
        return

    for face in faces:
        col_img, col_info = st.columns([1, 3])

        with col_img:
            if face["image_base64"]:
                image_bytes = base64.b64decode(face["image_base64"])
                st.image(BytesIO(image_bytes), width=120)
            else:
                st.caption("No image")

        with col_info:
            st.markdown(f"**{face['attempted_at']}**")
            if face["description"]:
                st.write(face["description"])
            else:
                st.caption(":material/hourglass_empty: Description not generated yet (or generation failed).")
                if face["image_base64"] and st.button(":material/refresh: Generate description", key=f"regen_{face['id']}"):
                    with st.spinner("Generating description..."):
                        try:
                            response = regenerate_description(face["id"], image_bytes)
                            if response.status_code == 200:
                                st.rerun()
                            else:
                                st.error(f"Failed ({response.status_code}): {response.text}")
                        except requests.exceptions.RequestException as exc:
                            st.error(f"Failed to request regeneration: {exc}")

        st.divider()