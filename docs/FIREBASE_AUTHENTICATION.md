# Firebase Authentication

GlucoPlate uses Firebase Authentication in the browser and verifies Firebase ID tokens in FastAPI.

## Firebase Console

Enable these providers under **Authentication → Sign-in method**:

- Google
- Anonymous

Apple and email/password are planned follow-up providers.

Add the production Render hostname under **Authentication → Settings → Authorized domains**.

## Render environment variables

```text
FIREBASE_WEB_API_KEY
FIREBASE_AUTH_DOMAIN
FIREBASE_PROJECT_ID
FIREBASE_STORAGE_BUCKET
FIREBASE_MESSAGING_SENDER_ID
FIREBASE_APP_ID
FIREBASE_MEASUREMENT_ID
FIREBASE_SERVICE_ACCOUNT_JSON
```

`FIREBASE_SERVICE_ACCOUNT_JSON` must contain the complete service-account JSON and must never be committed to GitHub.

## API

- `GET /api/firebase-auth/config` returns safe browser configuration and readiness flags.
- `GET /api/firebase-auth/session` verifies `Authorization: Bearer <Firebase ID token>` and returns the authenticated user summary.

## Client behavior

The Profile screen exposes Google and guest sign-in. Firebase persistence is browser-local. After Firebase changes authentication state, the client obtains an ID token, verifies it with FastAPI, and stores only the resulting session summary and current ID token in browser storage.

## Security notes

- Backend authorization must be based on the verified Firebase UID, never a UID supplied in JSON.
- Future recipe and notification ownership routes should derive the user from the verified bearer token.
- Firebase web configuration is public by design; service-account credentials are private.
