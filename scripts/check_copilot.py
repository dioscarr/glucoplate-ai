import asyncio
import json
import sys


async def main() -> int:
    try:
        from copilot import CopilotClient, PermissionHandler
    except Exception as exc:
        print(json.dumps({"copilot_installed": False, "error": str(exc)}))
        return 1

    client = CopilotClient()
    try:
        await client.start()
    except Exception as exc:
        print(json.dumps({"copilot_installed": True, "error": f"failed to start client: {exc}"}))
        return 2

    session = None
    try:
        session = await client.create_session(on_permission_request=PermissionHandler.approve_all)
        response = await session.send_and_wait("Return the single word pong", timeout=20.0)

        if not response or not getattr(response, "data", None) or not getattr(response.data, "content", None):
            print(
                json.dumps(
                    {
                        "copilot_installed": True,
                        "session": "ok",
                        "response": None,
                        "error": "empty response",
                    }
                )
            )
            return 4

        print(
            json.dumps(
                {
                    "copilot_installed": True,
                    "session": "ok",
                    "response_preview": str(response.data.content)[:100],
                }
            )
        )
        return 0
    except Exception as exc:
        print(json.dumps({"copilot_installed": True, "error": f"session send error: {exc}"}))
        return 5
    finally:
        try:
            if session:
                await session.disconnect()
            await client.stop()
        except Exception:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
