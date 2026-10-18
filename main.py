import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Layer 1: hardcoded defaults
DEFAULTS = {"port": 8000, "workers": 1, "debug": False, "log_level": "info", "api_key": "default-secret-000"}
# Layer 2: config.development.yaml
YAML_LAYER = {"log_level": "info", "api_key": "key-z8lrxx4a62"}
# Layer 3: .env file
DOTENV_LAYER = {"APP_API_KEY": "key-8ub2vf8tob"}
# Layer 4: OS env vars (APP_*)
OS_LAYER = {"APP_WORKERS": "9", "APP_API_KEY": "key-tdlxf7ldp7"}

ALIASES = {"num_workers": "workers"}
INT_KEYS = {"port", "workers"}


def norm_key(k: str) -> str:
    k = k.strip()
    if k.upper().startswith("APP_"):
        k = k[4:]
    k = k.lower()
    return ALIASES.get(k, k)


def coerce(k, v):
    if k in INT_KEYS:
        try:
            return int(str(v).strip())
        except ValueError:
            return v
    if k == "debug":
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("true", "1", "yes", "on")
    return str(v)


def merge(*layers):
    out = {}
    for layer in layers:
        for k, v in layer.items():
            out[norm_key(k)] = v
    return out


@app.get("/effective-config")
def effective_config(request: Request):
    real_os = {k: v for k, v in os.environ.items() if k.startswith("APP_")}
    cli = {}
    for item in request.query_params.getlist("set"):
        if "=" in item:
            k, v = item.split("=", 1)
            cli[k] = v
    merged = merge(DEFAULTS, YAML_LAYER, DOTENV_LAYER, OS_LAYER, real_os, cli)
    result = {k: coerce(k, v) for k, v in merged.items()}
    result["api_key"] = "****"
    return result
