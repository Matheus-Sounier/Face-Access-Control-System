import streamlit as st
import config

from pages.register import register_page
from pages.chat import chat_page
from pages.unknown_faces import unknown_faces_page

register = st.Page(register_page, title="Register Person", icon=":material/person_add:")
chat = st.Page(chat_page, title="Analytics Chat", icon=":material/forum:")
unknown_faces = st.Page(unknown_faces_page, title="Unknown Faces", icon=":material/person_search:")

pg = st.navigation([register, chat, unknown_faces])
pg.run()