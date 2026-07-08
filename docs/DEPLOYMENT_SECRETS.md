# Deployment Secrets Strategy

GlucoPlate AI uses a small secret-provider abstraction so application code does not need to know whether a value came from a local `.env`, GitHub Actions secret, Render environment variable, Azure Key Vault, or another managed secret store.

## Recommended Strategy

```text
Local development
  .env or shell environment variables

GitHub Actions CI
  GitHub repository secrets

Render runtime deployment
  Render environment variables / secret values

Future Azure production
  Azure Key Vault through a new SecretProvider implementation
```

## Can GitHub Be the Key Vault?

GitHub can be the practical key vault for **CI and deployment automation**.

Use GitHub Secrets for:

- CI webhook URL
- test-only API keys
- deployment tokens
- Render deploy hook URL
- cloud provider credentials used by GitHub Actions
- environment-specific secrets used during a GitHub Actions deployment

Do not rely on GitHub Secrets as the direct runtime secret store unless GitHub Actions is the process that deploys the app and injects those secrets into the runtime platform.

For example:

```text
GitHub Actions secret
  ↓
GitHub Actions workflow
  ↓
Render deploy API / Render environment variable sync / deploy hook
  ↓
Running Render app reads environment variable
```

The running app on Render cannot automatically read GitHub Secrets by itself. GitHub Secrets are available to GitHub Actions workflows, not to arbitrary running servers.

## Current Secret Names

The app currently supports these Gemini key names:

```text
GEMINI_API_KEY
GOOGLE_API_KEY
GOOGLE_GEMINI_API_KEY
```

The app currently supports this Gemini model override:

```text
GEMINI_MODEL
```

The CI notification workflow supports this webhook secret:

```text
CI_NOTIFICATION_WEBHOOK_URL
```

## Secret Provider Boundary

Application code should use:

```python
from app.core.secrets import get_secret

api_key = get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY")
```

This allows the app to support multiple accepted names during migration while keeping feature code clean.

## Why This Helps Deployment

Without a secret boundary, each file calls `os.getenv` directly. That makes it harder to move from `.env` to GitHub Secrets, Render secrets, or Azure Key Vault.

With a boundary:

- local development keeps working
- production deployment stays clean
- future vault providers can be added in one place
- AI services do not need to change when the secret store changes
- tests can monkeypatch one layer instead of many files

## Future Azure Key Vault Extension

When the app is hosted in Azure, add an implementation similar to:

```python
class AzureKeyVaultSecretProvider:
    def get(self, name: str) -> str | None:
        ...
```

Then chain it before environment variables:

```python
return ChainedSecretProvider(
    AzureKeyVaultSecretProvider(),
    EnvironmentSecretProvider(),
)
```

That allows Azure Key Vault to be preferred in production while environment variables remain the fallback.

## Practical Next Step

For the current app, use GitHub Secrets for GitHub Actions and Render environment variables for Render runtime.

Minimum secrets to configure:

```text
GitHub Actions secret:
CI_NOTIFICATION_WEBHOOK_URL

Render environment variable:
GEMINI_API_KEY
```

Optional:

```text
Render environment variable:
GEMINI_MODEL=gemini-1.5-flash
```
