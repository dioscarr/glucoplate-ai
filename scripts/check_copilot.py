import asyncio
import json
import sys


async def main():
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

    # Try the runtime default first, then probe several common model names
    models_to_try = [None, "gpt-4o", "gpt-4", "gpt-3.5"]
    session = None
    last_exc = None
    for model in models_to_try:
        try:
            if model:
                session = await client.create_session(
                    model=model,
                    on_permission_request=PermissionHandler.approve_all,
                )
            else:
                session = await client.create_session(on_permission_request=PermissionHandler.approve_all)
            break
        except Exception as exc:
            last_exc = exc
            continue

    if session is None:
        print(json.dumps({"copilot_installed": True, "error": f"failed to create session: {last_exc}"}))
        await client.stop()
        return 3

    try:
        prompt = "Return the single word 'pong'"
        response = await session.send_and_wait(prompt, timeout=20.0)
        await session.disconnect()

        if not response or not getattr(response, 'data', None) or not getattr(response.data, 'content', None):
            print(json.dumps({"copilot_installed": True, "session": "ok", "response": None, "error": "empty response"}))
            return 4

        print(json.dumps({
            "copilot_installed": True,
            "session": "ok",
            "response_preview": str(response.data.content)[:100],
        }))
        return 0
    except Exception as exc:
        print(json.dumps({"copilot_installed": True, "error": f"session send error: {exc}"}))
        return 5
    finally:
        try:
            await client.stop()
        except Exception:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
