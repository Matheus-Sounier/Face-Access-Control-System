import requests

from config import API_URL

def recognize_face(image_bytes):
    try:
        response = requests.post(
            f"{API_URL}/recognize",
            files={
                "file": (
                    "face.jpg",
                    image_bytes,
                    "image/jpeg",
                )
            },
            timeout=3,
        )

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None