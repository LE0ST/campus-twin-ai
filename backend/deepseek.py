"""Cliente DeepSeek limitado a una llamada de herramienta por solicitud."""
import json
import os
from functools import lru_cache

BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"


class ProviderError(Exception):
    pass


@lru_cache(maxsize=1)
def _client(key):
    from openai import OpenAI
    return OpenAI(api_key=key, base_url=BASE_URL, timeout=3.5, max_retries=0)


def call_tool(name, parameters, prompt):
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ProviderError("not_configured")
    try:
        response = _client(key).chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL),
            messages=[{"role": "system", "content": "Usa únicamente la herramienta indicada. No inventes datos."},
                      {"role": "user", "content": prompt}],
            tools=[{"type": "function", "function": {"name": name, "parameters": parameters}}],
            tool_choice={"type": "function", "function": {"name": name}},
            extra_body={"thinking": {"type": "disabled"}},
        )
        calls = response.choices[0].message.tool_calls or []
        if len(calls) != 1 or calls[0].type != "function" or calls[0].function.name != name:
            raise ProviderError("invalid_tool_call")
        def unique_pairs(pairs):
            result = {}
            for k, v in pairs:
                if k in result:
                    raise ValueError("duplicate key")
                result[k] = v
            return result
        args = json.loads(calls[0].function.arguments, object_pairs_hook=unique_pairs)
        if not isinstance(args, dict):
            raise ValueError("arguments must be an object")
        return args
    except ProviderError:
        raise
    except Exception:
        # Never expose provider error bodies, request details or credentials.
        raise ProviderError("provider_unavailable") from None
