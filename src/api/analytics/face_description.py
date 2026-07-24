import os
import base64
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL")

DESCRIPTION_PROMPT = """
Describe this person's physical appearance for a security log, focused only on
observable, changeable attributes that would help someone visually locate them
in a building right now:
- clothing (colors, type: jacket, shirt, cap, etc.)
- accessories (hat, glasses, mask, bag, etc.)
- hair color and style
- any clearly visible distinguishing feature (e.g. a visible tattoo, its color skin)

Do not guess age, gender, ethnicity, or race. Do not speculate about identity,
intent, or emotional state. One concise sentence, factual and neutral tone.
If the image is too unclear or too cropped to describe reliably, say so.
"""

import time

def describe_face(image_bytes: bytes, max_retries: int = 2) -> str:
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    for attempt in range(max_retries + 1):
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": DESCRIPTION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                            },
                        ],
                    }
                ],
                "max_tokens": 1200,
            },
            timeout=60,
        )

        if response.status_code == 429 and attempt < max_retries:
            wait_seconds = 5 * (attempt + 1)
            print(f"[face_description] 429 received, waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
            continue

        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise RuntimeError(f"OpenRouter error: {result['error']}")
        if "choices" not in result:
            raise RuntimeError(f"Unexpected OpenRouter response: {result}")

        return result["choices"][0]["message"]["content"].strip()

    raise RuntimeError("Too many 429 responses from OpenRouter, giving up.")