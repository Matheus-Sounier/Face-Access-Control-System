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