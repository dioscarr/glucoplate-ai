from __future__ import annotations

import os
from functools import lru_cache
from typing import Protocol


class SecretProvider(Protocol):
    """Read application secrets without exposing the backing store to feature code."""

    def get(self, name: str) -> str | None:
        """Return a secret value by name, or None when not configured."""


class EnvironmentSecretProvider:
    """Secret provider for local development and platform-provided environment secrets."""

    def get(self, name: str) -> str | None:
        return os.getenv(name)


class ChainedSecretProvider:
    """Try multiple providers in order and return the first configured value."""

    def __init__(self, *providers: SecretProvider) -> None:
        self.providers = providers

    def get(self, name: str) -> str | None:
        for provider in self.providers:
            value = provider.get(name)
            if value:
                return value
        return None


@lru_cache(maxsize=1)
def get_secret_provider() -> SecretProvider:
    """Return the app's configured secret provider.

    Today this returns environment-backed secrets so local development and Render-style
    deployments continue working. The boundary exists so production can add Azure Key Vault,
    AWS Secrets Manager, Doppler, or another provider without changing application services.
    """

    return ChainedSecretProvider(EnvironmentSecretProvider())


def get_secret(*names: str) -> str | None:
    """Return the first configured secret from a list of accepted names.

    This supports smooth migrations where an old environment variable and a new vault secret
    name may temporarily exist at the same time.
    """

    provider = get_secret_provider()
    for name in names:
        value = provider.get(name)
        if value:
            return value
    return None
