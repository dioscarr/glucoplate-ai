# Post-cook history and feedback

Live Cook Rooms preserve a private, participant-visible event timeline after a host finishes or ends a session early. Video recording remains disabled; history contains cooking events and metadata only.

## Lifecycle behavior

- Only the Chef can start, complete, or end a session early.
- Complete and abandon transitions are idempotent. Repeating the same terminal request does not create another completion event.
- A terminal transition saves its actor, timestamp, final revision, session ID, recipe ID, and correlation ID.
- Existing ingredient, timer, step, help, join, and leave activity becomes the chronological session timeline.
- Only users who joined the room can read its history or leave feedback.
- Feedback is stored per participant and may be updated without reopening the session.
- Feedback failure never blocks the terminal lifecycle transition.

## API

- `POST /api/live-cook-rooms/{room_id}/complete`
- `POST /api/live-cook-rooms/{room_id}/abandon`
- `GET /api/live-cook-rooms/{room_id}/history`
- `POST /api/live-cook-rooms/{room_id}/feedback`

Feedback payload:

```json
{
  "rating": 5,
  "would_cook_again": true,
  "note": "Loved cooking this together."
}
```

## Manual verification

1. Create a Live Cook Room as the Chef and join from a second organization account.
2. Start cooking, change steps, check an ingredient, run a timer, and send a help request.
3. Select **Finish session** and cancel once; confirm cooking remains active.
4. Finish again and confirm the room reports **Session completed**.
5. Select **View timeline** from both participant devices.
6. Confirm events are chronological and include the actions from step 2 plus one completion event.
7. Submit feedback from each participant and confirm the summary updates.
8. Attempt to load the history using an account that never joined; confirm the API returns 403.
9. Repeat the flow with **End early** and confirm the status is **Session ended early**.
10. Refresh or reopen the PWA and confirm the saved timeline is still available.
