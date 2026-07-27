import array
from db.connection import get_connection

MATCH_THRESHOLD = 0.6J

def insert_face(person_id: int, embedding, face_image_bytes: bytes) -> int:
    """
    Adds one face embedding + image.
    called multiple times for the same person_id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    vector_value = array.array("f", embedding.tolist())

    try:
        result_id = cursor.var(int)
        cursor.execute(
            '''
            INSERT INTO PERSON_FACES (person_id, embedding, face_image)
            VALUES (:person_id, :embedding, :face_image)
            RETURNING id INTO :id
            ''',
            {
                "person_id": person_id,
                "embedding": vector_value,
                "face_image": face_image_bytes,
                "id": result_id,
            },
        )
        conn.commit()
        return result_id.getvalue()[0]
    finally:
        cursor.close()
        conn.close()

def find_closest_match(embedding):
    """
    Search for the person whose embedding is closest to the one provided.
    Returns a dict with the person's data + distance, or None if
    no one in the database falls within the MATCH_THRESHOLD
    """
    conn = get_connection()
    cursor = conn.cursor()

    vector_value = array.array("f", embedding.tolist())

    try:
        cursor.execute(
            '''
            SELECT p.id, p.name, p.employee_id, p.access_level,
                   MIN(VECTOR_DISTANCE(f.embedding, :embedding, COSINE)) AS distance
            FROM PERSON_FACES f
            JOIN DETECTED_PEOPLE p ON p.id = f.person_id
            GROUP BY p.id, p.name, p.employee_id, p.access_level
            ORDER BY distance ASC
            FETCH FIRST 1 ROW ONLY
            ''',
            {"embedding": vector_value},
        )
        row = cursor.fetchone()

        if row is None:
            return None

        person_id, name, employee_id, access_level, distance = row

        if distance > MATCH_THRESHOLD:
            return None

        return {
            "id": person_id,
            "name": name,
            "employee_id": employee_id,
            "access_level": access_level,
            "distance": distance,
        }
    finally:
        cursor.close()
        conn.close()