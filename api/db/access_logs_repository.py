from db.connection import get_connection

def log_access(person_id, employee_id, recognized: bool, access_granted: bool, face_image_bytes: bytes = None) -> int:
    """no recognizable face in the submitted cutout"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        result_id = cursor.var(int)
        cursor.execute(
            '''
            INSERT INTO ACCESS_LOGS (person_id, employee_id, recognized, access_granted, face_detected)
            VALUES (:person_id, :employee_id, :recognized, :access_granted, :face_detected)
            RETURNING id INTO :id
            ''',
            {
                "person_id": person_id,
                "employee_id": employee_id,
                "recognized": 1 if recognized else 0,
                "access_granted": 1 if access_granted else 0,
                "face_detected": face_image_bytes,
                "id": result_id,
            },
        )
        conn.commit()
        return result_id.getvalue()[0]
    finally:
        cursor.close()
        conn.close()

def update_log_description(log_id: int, description: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE ACCESS_LOGS SET face_description = :description WHERE id = :log_id",
            {"description": description, "log_id": log_id},
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def has_recent_unknown_log(within_seconds: int = 60) -> bool:
    """Checks if an unrecognized attempt was already logged very recently"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT COUNT(*) FROM ACCESS_LOGS
            WHERE recognized = 0
              AND attempted_at >= SYSTIMESTAMP - NUMTODSINTERVAL(:seconds, 'SECOND')
            ''',
            {"seconds": within_seconds},
        )
        count = cursor.fetchone()[0]
        return count > 1
    finally:
        cursor.close()
        conn.close()

def get_unknown_faces(limit: int = 40) -> list[dict]:
    """
    Returns the most recent unrecognized access attempts
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT id, face_detected, face_description, attempted_at
            FROM ACCESS_LOGS
            WHERE recognized = 0
            ORDER BY attempted_at DESC
            FETCH FIRST :limit ROWS ONLY
            ''',
            {"limit": limit},
        )

        results = []
        for log_id, face_blob, description, attempted_at in cursor.fetchall():
            image_bytes = face_blob.read() if face_blob is not None else None
            results.append({
                "id": log_id,
                "image_bytes": image_bytes,
                "description": description,
                "attempted_at": attempted_at.isoformat(),
            })
        return results
    finally:
        cursor.close()
        conn.close()