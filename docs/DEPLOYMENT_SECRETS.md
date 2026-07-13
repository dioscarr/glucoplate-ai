# Deployment Secrets Strategy

GlucoPlate AI reads runtime secrets through `app.core.secrets.get_secret`, allowing local environment variables, GitHub Actions secrets, Render environment variables, and future managed vaults to use the same application code.

## Render runtime variables

Add this required secret to the Render service:

```text
GROQ_API_KEY=<your Groq API key>
```

The application automatically prefers Groq when this variable is present.

Optional Groq model override:

```text
GROQ_MODEL=llama-3.1-8b-instant
```

When `GROQ_MODEL` is omitted, the application uses `llama-3.1-8b-instant`. The Groq request is intentionally constrained to a compact JSON response, temperature `0.2`, and at most `420` completion tokens. Token usage is written to the application logs for monitoring.

## Provider order

In automatic mode, providers are attempted in this order:

```text
Groq -> Gemini (when configured) -> deterministic local fallback
```

Gemini is optional and may be removed from Render after Groq has been verified. These legacy variables remain supported:

```text
GEMINI_API_KEY
GOOGLE_API_KEY
GOOGLE_GEMINI_API_KEY
GEMINI_MODEL
```

## GitHub Actions

GitHub repository secrets are available to workflows, not directly to the running Render service. Keep CI-only values such as the following in GitHub Actions:

```text
CI_NOTIFICATION_WEBHOOK_URL
```

Runtime API keys must be entered in Render or injected there by a deployment workflow.

## Secret provider boundary

Application code should request values through the shared helper:

```python
from app.core.secrets import get_secret

api_key = get_secret("GROQ_API_KEY")
```

This keeps provider code independent from the hosting platform and makes a future migration to Azure Key Vault or another secret manager straightforward.
