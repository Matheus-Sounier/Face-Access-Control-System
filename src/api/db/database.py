import os
import oracledb
import array
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

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE DETECTED_PEOPLE (
                id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name          VARCHAR2(255) NOT NULL,
                employee_id   VARCHAR2(50) NOT NULL UNIQUE,
                access_level  VARCHAR2(50) NOT NULL,
                embedding     VECTOR(512, FLOAT32) NOT NULL,
                enrolled_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("Table DETECTED_PEOPLE created.")
    except oracledb.DatabaseError as e:
        error, = e.args
        if error.code == 955:  # ORA-00955
            print("Table DETECTED_PEOPLE already exists, continuing...")
        else:
            raise
    finally:
        cursor.close()
        conn.close()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE ACCESS_LOGS (
                id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                person_id    NUMBER REFERENCES DETECTED_PEOPLE(id),
                employee_id  VARCHAR2(50),
                recognized   NUMBER(1) NOT NULL,
                access_granted NUMBER(1) NOT NULL,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("Table ACCESS_LOGS's created.")
    except oracledb.DatabaseError as e:
        error, = e.args
        if error.code == 955:  # ORA-00955
            print("Table ACCESS_LOGS already exists, continuing...")
        else:
            raise
    finally:
        cursor.close()
        conn.close()
        
def insert_person(name: str, employee_id: str, access_level: str, embedding) -> int:
    """
    Inserts a new person with their facial embedding.
    Returns the generated id. Raises oracledb.IntegrityError if employee_id already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    vector_value = array.array("f", embedding.tolist())

    try:
        result_id = cursor.var(int)
        cursor.execute(
            '''
            INSERT INTO DETECTED_PEOPLE (name, employee_id, access_level, embedding)
            VALUES (:name, :employee_id, :access_level, :embedding)
            RETURNING id INTO :id
            ''',
            {
                "name": name,
                "employee_id": employee_id,
                "access_level": access_level,
                "embedding": vector_value,
                "id": result_id,
            },
        )
        conn.commit()
        return result_id.getvalue()[0]
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_db()