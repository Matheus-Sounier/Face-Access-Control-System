import oracledb
from db.connection import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE DETECTED_PEOPLE (
                id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name            VARCHAR2(255) NOT NULL,
                employee_id     VARCHAR2(50) NOT NULL UNIQUE,
                access_level    VARCHAR2(50) NOT NULL,
                enrolled_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("Table DETECTED_PEOPLE created.")
    except oracledb.DatabaseError as e:
        error, = e.args
        if error.code == 955:
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
            CREATE TABLE PERSON_FACES (
                id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                person_id    NUMBER NOT NULL REFERENCES DETECTED_PEOPLE(id) ON DELETE CASCADE,
                embedding    VECTOR(512, FLOAT32) NOT NULL,
                face_image   BLOB,
                enrolled_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("Table PERSON_FACES created.")
    except oracledb.DatabaseError as e:
        error, = e.args
        if error.code == 955:
            print("Table PERSON_FACES already exists, continuing...")
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
                id             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                person_id      NUMBER REFERENCES DETECTED_PEOPLE(id),
                employee_id    VARCHAR2(50),
                recognized     NUMBER(1) NOT NULL,
                access_granted NUMBER(1) NOT NULL,
                face_detected  BLOB,
                face_description VARCHAR2(500),
                attempted_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("Table ACCESS_LOGS's created.")
    except oracledb.DatabaseError as e:
        error, = e.args
        if error.code == 955:
            print("Table ACCESS_LOGS already exists, continuing...")
        else:
            raise
    finally:
        cursor.close()
        conn.close()