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
- If one media device is missing, the call continues in video-only or audio-only mode.
- Cooks can select a camera or microphone without leaving the call.
- Every browser installation appears as a separate participant, even when multiple devices use the same account.
- Mobile cooks can flip between front and rear cameras with one tap.
- The call panel distinguishes room membership from active media presence (for example, **3 people in room · 2 devices on video**).
- Active device labels and camera/microphone state appear above the responsive tile grid.
- A 15-second media heartbeat removes stale or disconnected devices from the presence list after 45 seconds.
- Remote participant tracks appear in a responsive tile grid.
- LiveKit reconnection events preserve the rest of the cooking experience.
- Reconnecting, weak-connection, and disconnected states appear without replacing the recipe, timer, or chat UI.
- A disconnected call offers **Retry video** without requiring the cook to rejoin the room.
- Connection quality is displayed per active device, while unchanged polling heartbeats do not rebuild video tracks.
- Recording is disabled.
- Completing the cooking session disconnects media.
- Leaving the page stops local capture and disconnects the call.

## Verification checklist

1. Create or join the same Live Room from two organization accounts.
2. Select **Join video call** on both devices.
3. Approve camera and microphone permissions.
4. Confirm the member/device summary, both participant tiles, and remote audio.
5. Toggle microphone and camera on each device.
6. Background and restore the mobile PWA.
7. Disconnect Wi-Fi briefly and confirm reconnecting/weak-connection feedback while recipe controls remain usable.
8. Allow the call to disconnect and confirm **Retry video** reconnects inside the same cooking room.
9. Complete the cooking session and confirm capture ends.
