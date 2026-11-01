import os
import requests
import time
import config

# groq's openai-compatible endpoint (hugging face router needs paid credits)
API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")

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


def _query_llm(prompt, max_tokens=None, temperature=None):
    # sends a prompt to the llm via huggingface inference providers (chat completions)
    _check_rate_limit()

    if not config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    # the chat endpoint adds its own template, so strip the mistral-specific tags
    clean_prompt = (
        prompt.replace("<s>", "").replace("[INST]", "").replace("[/INST]", "").strip()
    )

    payload = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "user", "content": clean_prompt}],
        "max_tokens": max_tokens or config.LLM_MAX_TOKENS,
        "temperature": temperature or config.LLM_TEMPERATURE,
    }

    # reasoning models think before answering, so keep that short (set LLM_REASONING_EFFORT="" on Render to disable)
    effort = os.getenv("LLM_REASONING_EFFORT", "low")
    if effort and "gpt-oss" in config.LLM_MODEL:
        payload["reasoning_effort"] = effort


    retries = 3
    last_error = "unknown error"
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)


            if response.status_code in (429, 503):
            # rate limited or model busy: wait as long as the server asks, up to 30 s
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                try:
                    wait = min(30.0, float(response.headers.get("retry-after", "")))
                except ValueError:
                    wait = min(30, 10 * (attempt + 1))
                time.sleep(wait)
                continue

            if response.status_code >= 400:
                # auth, permission or model problems will not fix themselves, so fail loudly
                raise RuntimeError(f"LLM API HTTP {response.status_code}: {response.text[:300]}")

            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            last_error = "request timed out"
            time.sleep(5)
        except requests.exceptions.RequestException as err:
            last_error = f"network error: {err}"
            time.sleep(5)

    raise RuntimeError(f"Failed to get response from LLM after retries: {last_error}")


def query_mistral(prompt, max_tokens=None, temperature=None):
    # wrapper so every llm failure is printed to the render logs before the agents fall back
    try:
        return _query_llm(prompt, max_tokens, temperature)
    except Exception as err:
        print(f"[LLM ERROR] {err}", flush=True)
        raise 


def build_prompt(system_instruction, context_chunks, user_query):
    # formats a prompt with system instruction, retrieved context, and user question
    # context is trimmed (3 chunks, 800 chars each) to stay inside free-tier token limits
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

    prompt = f"""<s>[INST] {system_instruction}

LEGAL KNOWLEDGE CONTEXT:
{context_text}

DOCUMENT/QUERY:
{user_query}

Provide your analysis in valid JSON format. Be precise and cite specific clauses where possible. [/INST]"""

    return prompt
