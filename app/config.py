"""API-key storage. Keys live in the OS credential store (keyring), never in
repo files. Env vars are a fallback so the app still works in CI/headless."""

import os

try:
    import keyring
except Exception:  # pragma: no cover
    keyring = None

KEYRING_SERVICE = "ModelManager"

# providers the Settings dialog exposes (add more here later)
PROVIDERS = [
    ("kie", "kie.ai — nano-banana"),
    ("imgbb", "imgbb — reference image hosting"),
    ("openrouter", "OpenRouter — Hermes casting agent"),
    ("replicate", "Replicate"),
    ("fal", "fal.ai"),
    ("openai", "OpenAI"),
]


def get_key(provider: str) -> str:
    if keyring is not None:
        try:
            v = keyring.get_password(KEYRING_SERVICE, f"apikey:{provider}")
            if v:
                return v
        except Exception:
            pass
    return os.environ.get(f"{provider.upper()}_KEY", "") or os.environ.get(f"{provider.upper()}_API_KEY", "")


def set_key(provider: str, value: str):
    if keyring is None:
        return
    try:
        keyring.set_password(KEYRING_SERVICE, f"apikey:{provider}", value or "")
    except Exception:
        pass
