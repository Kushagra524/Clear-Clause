import os
import requests
import time
import config

_call_timestamps = []
RATE_LIMIT_WINDOW = 3600
MAX_CALLS_PER_HOUR = 3600


def _check_rate_limit():
    global _call_timestamps
    now = time.time()
    _call_timestamps = [t for t in _call_timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_call_timestamps) >= MAX_CALLS_PER_HOUR:
        wait_time = RATE_LIMIT_WINDOW - (now - _call_timestamps[0])
        raise RuntimeError(f"Rate limit approaching. Wait {int(wait_time)}s before next call.")
    _call_timestamps.append(now)


def _query_llm(prompt, max_tokens=None, temperature=None):
    _check_rate_limit()

    api_key = config.LLM_API_KEY
    if not api_key:
        raise RuntimeError("LLM_API_KEY / GROQ_API_KEY is not set. Please set it in your environment or .env file.")

    api_url = config.LLM_API_URL or "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    clean_prompt = (
        prompt.replace("<s>", "").replace("</s>", "").replace("[INST]", "").replace("[/INST]", "").strip()
    )

    payload = {
        "model": config.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are ClearClause, an expert legal contract analysis assistant. Always respond in valid, well-structured JSON format."
            },
            {"role": "user", "content": clean_prompt}
        ],
        "max_tokens": max_tokens or config.LLM_MAX_TOKENS,
        "temperature": temperature or config.LLM_TEMPERATURE,
    }

    retries = int(os.getenv("LLM_RETRIES", "2"))
    timeout = int(os.getenv("LLM_TIMEOUT", "20"))
    last_error = "unknown error"

    for attempt in range(retries):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)

            if response.status_code in (429, 503):
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                try:
                    wait = min(20.0, float(response.headers.get("retry-after", "")))
                except (ValueError, TypeError):
                    wait = min(15, 3 * (attempt + 1))
                time.sleep(wait)
                continue

            if response.status_code >= 400:
                raise RuntimeError(f"LLM API HTTP {response.status_code}: {response.text[:300]}")

            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            last_error = "request timed out"
            time.sleep(1)
        except requests.exceptions.RequestException as err:
            last_error = f"network error: {err}"
            time.sleep(1)

    raise RuntimeError(f"Failed to get response from LLM after {retries} attempts: {last_error}")


def query_mistral(prompt, max_tokens=None, temperature=None):
    try:
        return _query_llm(prompt, max_tokens, temperature)
    except Exception as err:
        print(f"[LLM ERROR] {err}", flush=True)
        raise


def build_prompt(system_instruction, context_chunks, user_query):
    context_text = ""
    for i, chunk in enumerate(context_chunks[:3]):
        meta = chunk.get("metadata", chunk)
        text = meta.get("text", str(meta))[:800]
        section = meta.get("section", "")
        source = meta.get("source", "")
        header = f"[Source: {source}]" if source else ""
        if section:
            header += f" [Section: {section}]"
        context_text += f"\n--- Reference {i+1} {header} ---\n{text}\n"

    prompt = f"""{system_instruction}

LEGAL KNOWLEDGE CONTEXT:
{context_text}

DOCUMENT / CONTRACT TO ANALYZE:
{user_query}

CRITICAL: Return ONLY valid JSON as requested. Do not include markdown codeblocks or conversational text outside the JSON."""

    return prompt
