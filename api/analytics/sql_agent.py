from datetime import datetime, date
from decimal import Decimal

import os
import time
import re
import json
import httpx
import oracledb

def get_readonly_connection():
    return oracledb.connect(
        user=os.getenv("ANALYTICS_DB_USER"),
        password=os.getenv("ANALYTICS_DB_PWD"),
        host=os.getenv("ORACLE_HOSTNAME"),
        port=os.getenv("PORT_DB"),
        service_name=os.getenv("SERVICE_NAME"),
    )

SCHEMA_DESCRIPTION = """
You are a data analyst with access to an Oracle facial access control database.
Answer only in English.

## Conversation memory
- The messages above in this conversation ARE your memory of this session.
- If the user asks about a previous question or answer, look back at the prior
  messages in this same conversation and answer based on them directly.
- Never claim you have no memory of the conversation — the full conversation
  so far is provided to you in the messages array.

## Response style
- Be extremely concise. No preamble, no "let me check", no restating the question.
- Give the number/fact first, then at most one sentence of context if truly needed.
- Do not explain your SQL query or your reasoning process — just answer the question.
- When the answer involves 2 or more distinct items (names, timestamps, events, rows),
  format them as a Markdown bullet list or table — never as a comma-separated sentence.
  - Bad:  "Detections at 09:12, 09:45, 10:03, 14:20"
  - Good: "- 09:12\\n- 09:45\\n- 10:03\\n- 14:20"
- Use a Markdown table when there are 2+ columns of information to show per item
  (e.g. name + timestamp + access_level).
- Never invent numbers or rows. Every fact must come from an execute_sql result.

## When to query
Always call execute_sql before answering — never guess or assume from memory,
and never assume a table is empty or inaccessible without querying it first.
This includes questions like:
- what is stored / who is registered / list people / show data
- describe records / summarize the database
- any question about counts, timestamps, names, or patterns in the data

## Tables (read-only)

DETECTED_PEOPLE
  - id             NUMBER (PK)
  - name           VARCHAR2
  - employee_id    VARCHAR2
  - access_level   VARCHAR2 ('Visitor', 'Employee', 'Administrator')
  - enrolled_at    TIMESTAMP

ACCESS_LOGS
  - id             NUMBER (PK)
  - person_id      NUMBER (FK -> DETECTED_PEOPLE.id; NULL = unrecognized face)
  - employee_id    VARCHAR2 (may be NULL)
  - recognized     NUMBER(1) (1 = recognized, 0 = unknown)
  - access_granted NUMBER(1) (1 = granted, 0 = denied)
  - attempted_at   TIMESTAMP
  (this table also has a BLOB column storing the captured face image —
   never SELECT it, it is not useful for analysis and cannot be displayed as text)

## Business rules
- NULL person_id/employee_id in ACCESS_LOGS represents an access attempt by an unknown face.
- "Business hours" means Monday to Friday, 08:00-18:00, unless the user specifies otherwise.
- Only generate SELECT statements. Never generate INSERT, UPDATE, DELETE, or DDL statements.
"""

FORBIDDEN_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|MERGE|CREATE|EXEC|CALL)\b",
    re.IGNORECASE,
)

MAX_ROWS = 200

def validate_sql(query: str) -> str:
    """Raises ValueError if the query is not a single safe SELECT statement."""
    stripped = query.strip().rstrip(";")

    if not re.match(r"^\s*SELECT\b", stripped, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")

    if FORBIDDEN_PATTERN.search(stripped):
        raise ValueError("The query contains a forbidden SQL keyword.")

    if ";" in stripped:
        raise ValueError("Multiple SQL statements are not allowed.")

    return stripped

def _serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, oracledb.LOB):
        return f"<binary data, {value.size()} bytes>"
    return value

def execute_sql(query: str) -> dict:
    safe_query = validate_sql(query)

    conn = get_readonly_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(safe_query)

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchmany(MAX_ROWS)

        data = [
            dict(zip(columns, (_serialize(v) for v in row)))
            for row in rows
        ]

        return {
            "columns": columns,
            "rows": data,
            "row_count": len(data),
        }

    finally:
        cursor.close()
        conn.close()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": (
                "Executes a read-only Oracle SELECT query against the "
                "ACCESS_LOGS and DETECTED_PEOPLE tables and returns the result."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A single Oracle SQL SELECT statement."
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    }
]

def _call_openrouter(messages: list, max_retries: int = 2) -> dict:
    for attempt in range(max_retries + 1):
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "tools": TOOLS,
                "max_tokens": 2000,
            },
            timeout=30,
        )

        if response.status_code == 429:
            print(f"[sql_agent] 429 body: {response.text}")
            print(f"[sql_agent] 429 headers: {dict(response.headers)}")

            if attempt < max_retries:
                wait_seconds = 5 * (attempt + 1)
                print(f"[sql_agent] Received 429, waiting {wait_seconds}s before retrying...")
                time.sleep(wait_seconds)
                continue

        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise RuntimeError(f"OpenRouter error: {result['error']}")
        if "choices" not in result:
            raise RuntimeError(f"Unexpected OpenRouter response: {result}")

        return result

    raise RuntimeError("Too many 429 responses from OpenRouter, giving up.")

def run_chat(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    messages = [{"role": "system", "content": SCHEMA_DESCRIPTION}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # print(f"[sql_agent] Sending {len(messages)} messages: {json.dumps(messages, ensure_ascii=False)[:2000]}")

    for _ in range(5):
        try:
            result = _call_openrouter(messages)
        except Exception as exc:
            print(f"[sql_agent] OpenRouter call failed: {exc}")
            return (
                "I couldn't communicate with the analysis model at the moment. "
                "Please check the API logs for more details.",
                history,
            )

        message = result["choices"][0]["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls")

        if not tool_calls:
            final_text = message.get("content", "")

            new_history = history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": final_text},
            ]

            return final_text, new_history

        for tool_call in tool_calls:
            args = json.loads(tool_call["function"]["arguments"])
            query = args.get("query", "")

            try:
                tool_result = execute_sql(query)
            except Exception as exc:
                tool_result = {"error": str(exc)}

            # print(f"[sql_agent] query: {query!r} -> {tool_result}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    fallback = (
        "I couldn't complete the analysis within the maximum number of steps. "
        "Please try rephrasing your question."
    )

    return fallback, history