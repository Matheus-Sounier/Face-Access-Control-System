import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return oracledb.connect(
        user=os.getenv("USER"),
        password=os.getenv("ORACLE_PWD"),
        host=os.getenv("ORACLE_HOSTNAME"),
        port=os.getenv("PORT_DB"),
        service_name=os.getenv("SERVICE_NAME"),
    )