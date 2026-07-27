import oracledb
from db.connection import get_connection

def insert_person(name: str, employee_id: str, access_level: str) -> int:
    """
    Inserts a new person with their facial embedding.
    Returns the generated id. Raises oracledb.IntegrityError if employee_id already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        result_id = cursor.var(int)
        cursor.execute(
            '''
            INSERT INTO DETECTED_PEOPLE (name, employee_id, access_level)
            VALUES (:name, :employee_id, :access_level)
            RETURNING id INTO :id
            ''',
            {
                "name": name,
                "employee_id": employee_id,
                "access_level": access_level,
                "id": result_id,
            },
        )
        conn.commit()
        return result_id.getvalue()[0]
    finally:
        cursor.close()
        conn.close()