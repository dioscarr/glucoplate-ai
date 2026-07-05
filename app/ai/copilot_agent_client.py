from __future__ import annotations

import os
import shutil


def _find_copilot_cli() -> str | None:
    """Locate the Copilot CLI binary from common install locations."""
    # 1. Explicit env override
    if path := os.environ.get("COPILOT_CLI_PATH"):
        return path
    # 2. Standard user bin (installed by the CLI installer)
    if path := shutil.which("copilot"):
        return path
    # 3. Codespaces VS Code extension cache location
    candidates = [
        os.path.expanduser("~/.local/bin/copilot"),
        os.path.expandvars(
            "${HOME}/.vscode-remote/data/User/globalStorage/"
            "github.copilot-chat/copilotCli/copilot"
        ),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


class CopilotAgentClient:
    """Small wrapper around the GitHub Copilot SDK cookbook API.

    The import is delayed so the application can still start in environments where
    the Copilot SDK is not installed. This is useful for local fallback mode,
    tests, and deployment experiments.
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    async def ask(self, prompt: str, timeout: float = 45.0) -> str:
        try:
            from copilot import CopilotClient, PermissionHandler, RuntimeConnection
        except ImportError as exc:
            raise RuntimeError(
                "GitHub Copilot SDK is not installed or available in this environment."
            ) from exc

        cli_path = _find_copilot_cli()
        connection = RuntimeConnection.for_stdio(path=cli_path) if cli_path else None
        client = CopilotClient(connection=connection) if connection else CopilotClient()
        await client.start()

        try:
            # If no model is specified, let the Copilot runtime choose a default
            if self.model:
                session = await client.create_session(
                    model=self.model,
                    on_permission_request=PermissionHandler.approve_all,
                )
            else:
                session = await client.create_session(on_permission_request=PermissionHandler.approve_all)
            response = await session.send_and_wait(prompt, timeout=timeout)
            # disconnect() is the SDK method to clean up a session object
            await session.disconnect()
        finally:
            await client.stop()

        if not response or not response.data or not response.data.content:
            raise RuntimeError("Copilot SDK returned an empty response.")

        return response.data.content
