# LiveKit video calls

GlucoPlate Live Rooms support real multi-participant audio and video through LiveKit. The synchronized recipe, checklist, timer, and chat continue to work when video is unavailable.

## Render configuration

Set these environment variables on the GlucoPlate web service:

- `LIVE_COOK_MEDIA_PROVIDER=livekit`
- `LIVEKIT_URL=wss://<your-project>.livekit.cloud`
- `LIVEKIT_API_KEY=<server API key>`
- `LIVEKIT_API_SECRET=<server API secret>`

Redeploy after saving the values. Keep the API secret server-side; the authenticated `/media/access` endpoint follows LiveKit's custom token-generation pattern and returns `serverUrl` plus `participantToken` only after verifying the Firebase user belongs to the requested GlucoPlate organization and has joined the Live Room.

Without all three LiveKit credentials, the UI automatically remains in private device-preview mode.

## Product behavior

- Joining video is optional.
- Camera and microphone can be toggled independently.
- Cooks can select a camera or microphone without leaving the call.
- Mobile cooks can flip between front and rear cameras with one tap.
- Remote participant tracks appear in a responsive tile grid.
- LiveKit reconnection events preserve the rest of the cooking experience.
- Recording is disabled.
- Completing the cooking session disconnects media.
- Leaving the page stops local capture and disconnects the call.

## Verification checklist

1. Create or join the same Live Room from two organization accounts.
2. Select **Join video call** on both devices.
3. Approve camera and microphone permissions.
4. Confirm both participant tiles and remote audio.
5. Toggle microphone and camera on each device.
6. Background and restore the mobile PWA.
7. Disconnect Wi-Fi briefly and confirm the reconnect state.
8. Complete the cooking session and confirm capture ends.
