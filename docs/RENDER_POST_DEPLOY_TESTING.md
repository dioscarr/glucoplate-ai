# Render post-deployment verification

The `Deploy to Render and Run Live Tests` GitHub Actions workflow deploys the latest `main` revision, waits for that specific Render deploy to become live, and then runs production HTTP smoke tests.

## Required GitHub Actions secrets

- `RENDER_DEPLOY_HOOK`: the full secret deploy hook URL for the GlucoPlate web service.
- `RENDER_API_KEY`: a Render personal API key with access to that service.

Never print or commit either value. Regenerate the deploy hook if it is exposed.

## Render auto-deploy setting

This workflow explicitly triggers deployments. Set the service's **Auto-Deploy** option to **Off** to prevent a push to `main` from creating both an automatic deploy and a deploy-hook deploy.

If you prefer Render's automatic deployment, remove the workflow's **Trigger Render deploy** step and change its resolution logic to locate the auto-deploy for `GITHUB_SHA`.

## Workflow behavior

1. Validate that both secrets exist.
2. Trigger the Render deploy hook.
3. Extract the service ID and the specific deployment ID.
4. If Render returns `202 Accepted`, locate the queued deploy by Git commit.
5. Poll `https://api.render.com/v1/services/{serviceId}/deploys/{deployId}`.
6. Stop immediately on a failed, canceled, or deactivated deploy.
7. Stop after 30 minutes instead of waiting forever.
8. Retry the live health endpoint.
9. Run `pytest -m live tests/test_live.py` against `https://glucoplate-ai.onrender.com`.

## Live checks

The smoke suite verifies:

- `GET /health` returns the exact production health contract.
- The root serves the GlucoPlate application shell.
- The PWA manifest is served with its expected content type.
- The service worker is available with a no-cache policy.

The live test module skips during ordinary local and pull-request test runs when `LIVE_SITE_URL` is absent.

## Troubleshooting

- **401 from Render API:** replace `RENDER_API_KEY` with a valid personal API key.
- **Could not extract service ID:** verify `RENDER_DEPLOY_HOOK` is the complete hook URL containing `srv-...`.
- **Hook returns 401:** the hook was regenerated; update the GitHub secret.
- **Queued deploy cannot be resolved:** check whether the Render service is linked to this repository and `main`.
- **Deployment is live but smoke tests fail:** open the workflow log and compare the failing endpoint with Render runtime logs.
