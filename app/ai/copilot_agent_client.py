from __future__ import annotations


class CopilotAgentClient:
    """Small wrapper around the GitHub Copilot SDK cookbook API.

    The import is delayed so the application can still start in environments where
    the Copilot SDK is not installed. This is useful for local fallback mode,
    tests, and deployment experiments.
    """

    def __init__(self, model: str = "gpt-5") -> None:
        self.model = model

    async def ask(self, prompt: str, timeout: float = 45.0) -> str:
        try:
            from copilot import CopilotClient, MessageOptions, PermissionHandler, SessionConfig
        except ImportError as exc:
            raise RuntimeError(
                "GitHub Copilot SDK is not installed or available in this environment."
            ) from exc

        client = CopilotClient()
        await client.start()

        try:
            session = await client.create_session(
                SessionConfig(
                    model=self.model,
                    on_permission_request=PermissionHandler.approve_all,
                )
            )
            response = await session.send_and_wait(MessageOptions(prompt=prompt), timeout=timeout)
            await session.destroy()
        finally:
            await client.stop()

        if not response or not response.data or not response.data.content:
            raise RuntimeError("Copilot SDK returned an empty response.")

        return response.data.content
