from db.schema import init_db
from db.people_repository import insert_person
from db.faces_repository import insert_face, find_closest_match, MATCH_THRESHOLD
from db.access_logs_repository import (
    log_access,
    update_log_description,
    has_recent_unknown_log,
    get_unknown_faces,
)

__all__ = [
    "init_db",
    "insert_person",
    "insert_face",
    "find_closest_match",
    "MATCH_THRESHOLD",
    "log_access",
    "update_log_description",
    "has_recent_unknown_log",
    "get_unknown_faces",
]

if __name__ == "__main__":
    init_db()