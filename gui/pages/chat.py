import streamlit as st
import requests
from services.api_client import ask_analytics

def chat_page():
    st.title(":material/forum: Analytics Chat")
    st.caption("Ask questions in natural language about the recorded access events.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input(
        "Example: Who attempted to access outside business hours this week?"
    )

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking, it might take a while..."):
                try:
                    response = ask_analytics(question, st.session_state.chat_history[:-1])

                    if response.status_code == 200:
                        reply = response.json()["reply"]
                    else:
                        reply = (
                            f":material/error: Error ({response.status_code}): "
                            f"{response.text}"
                        )

                except requests.exceptions.RequestException as exc:
                    reply = f":material/cloud_off: Unable to connect to the API.\n\n{exc}"

                st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})