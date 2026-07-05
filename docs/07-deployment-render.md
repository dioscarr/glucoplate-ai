# Deploy GlucoPlate AI for Free with Render

## Branch

Deployment work starts on:

```bash
feature/deployment-render
```

## Free Hosting Choice

Use Render Free Web Service for the FastAPI app and static UI.

Render free services may spin down when idle, so the first request after inactivity can be slow. Local generated image files are not guaranteed to persist long term on free ephemeral storage.

## Files Added

- `render.yaml`
- Updated `.github/workflows/ci.yml` to run CI on this branch and main.

## Render Setup

1. Go to Render.
2. Create a new Web Service or Blueprint from this repository.
3. Connect:

```text
dioscarr/glucoplate-ai
```

4. Use the `render.yaml` blueprint.
5. Confirm settings:

```text
Build Command: pip install -e .
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
Plan: Free
```

## Environment Variables in Render

Set these in the Render dashboard:

```text
GOOGLE_GEMINI_API_KEY=<your Gemini key>
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image-preview
```

Do not commit real keys to GitHub.

## CI/CD Options

### Simple Option

Let Render auto-deploy from `main` after the PR is merged.

### Controlled Option

Keep `autoDeploy: false` in `render.yaml` and deploy manually from Render after CI passes.

### Deploy Hook Option

If you want GitHub Actions to trigger deploys after tests pass:

1. In Render, create a deploy hook for the service.
2. In GitHub, add a repository secret named:

```text
RENDER_DEPLOY_HOOK_URL
```

3. Add a separate deploy step to GitHub Actions after the test job.

Recommended later workflow shape:

```yaml
name: Python CI Deploy

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e .[dev]
      - run: ruff check .
      - run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Trigger Render deploy
        env:
          RENDER_DEPLOY_HOOK_URL: ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
        run: curl -fsS "$RENDER_DEPLOY_HOOK_URL"
```

## Post-Deploy Checks

After deployment, test:

```text
/
/health
/api/recipes/generate
/api/stores/search
/api/products/search
/api/recipes/gallery
```

## Known Limitation

Gemini-generated images saved under `/static/generated/...` may disappear on free hosting because the filesystem is ephemeral. For persistent galleries, add Cloudinary, Supabase Storage, or S3-compatible storage later.
