import requests
import json
import time
import config


API_URL = f"https://api-inference.huggingface.co/models/{config.LLM_MODEL}"

# tracks recent calls to avoid hitting the free tier limit
_call_timestamps = []
RATE_LIMIT_WINDOW = 3600
MAX_CALLS_PER_HOUR = 900


def _check_rate_limit():
    # prevents exhausting the free tier api quota
    global _call_timestamps
    now = time.time()
    _call_timestamps = [t for t in _call_timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_call_timestamps) >= MAX_CALLS_PER_HOUR:
        wait_time = RATE_LIMIT_WINDOW - (now - _call_timestamps[0])
        raise RuntimeError(f"Rate limit approaching. Wait {int(wait_time)}s before next call.")
    _call_timestamps.append(now)


def query_mistral(prompt, max_tokens=None, temperature=None):
    # sends a prompt to mistral-7b via huggingface inference api
    _check_rate_limit()

    headers = {}
    if config.HF_API_TOKEN:
        headers["Authorization"] = f"Bearer {config.HF_API_TOKEN}"
    headers["Content-Type"] = "application/json"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens or config.LLM_MAX_TOKENS,
            "temperature": temperature or config.LLM_TEMPERATURE,
            "return_full_text": False,
            "do_sample": True,
        }
    }

    retries = 3
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)

            if response.status_code == 503:
                # model is loading, wait and retry
                wait = min(30, 10 * (attempt + 1))
                time.sleep(wait)
                continue

            if response.status_code == 429:
                # rate limited by api
                time.sleep(60)
                continue

            response.raise_for_status()
            result = response.json()

            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "").strip()
            elif isinstance(result, dict):
                return result.get("generated_text", "").strip()

            return str(result)

        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise RuntimeError("LLM request timed out after retries")
        except requests.exceptions.RequestException as err:
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise RuntimeError(f"LLM API error: {err}")

    raise RuntimeError("Failed to get response from LLM after retries")


def build_prompt(system_instruction, context_chunks, user_query):
    # formats a prompt with system instruction, retrieved context, and user question
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        meta = chunk.get("metadata", chunk)
        text = meta.get("text", str(meta))
        section = meta.get("section", "")
        source = meta.get("source", "")
        header = f"[Source: {source}]" if source else ""
        if section:
            header += f" [Section: {section}]"
        context_text += f"\n--- Reference {i+1} {header} ---\n{text}\n"

    prompt = f"""<s>[INST] {system_instruction}

LEGAL KNOWLEDGE CONTEXT:
{context_text}

DOCUMENT/QUERY:
{user_query}

Provide your analysis in valid JSON format. Be precise and cite specific clauses where possible. [/INST]"""

    return prompt
