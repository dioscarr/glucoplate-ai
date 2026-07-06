import json
import os
import threading
import time
import uuid
from typing import Dict, Any, List

from app.services.recipe_gallery_service import RecipeGalleryService

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
JOBS_PATH = os.path.join(DATA_DIR, 'gallery_jobs.json')
os.makedirs(DATA_DIR, exist_ok=True)

_lock = threading.Lock()


def _read_jobs() -> List[Dict[str, Any]]:
    if not os.path.exists(JOBS_PATH):
        return []
    try:
        with open(JOBS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _write_jobs(jobs: List[Dict[str, Any]]):
    with open(JOBS_PATH, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


class GalleryJobService:
    """Simple file-backed job queue. Jobs processed in background threads.

    This is deliberately lightweight for development. In production use a real queue.
    """

    def enqueue(self, request: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job = {
            'id': job_id,
            'request': request,
            'status': 'pending',
            'created_at': time.time(),
            'result': None,
            'error': None,
        }
        with _lock:
            jobs = _read_jobs()
            jobs.insert(0, job)
            _write_jobs(jobs)
        # start background worker thread
        t = threading.Thread(target=self._process_job, args=(job_id,), daemon=True)
        t.start()
        return job_id

    def get(self, job_id: str) -> Dict[str, Any] | None:
        jobs = _read_jobs()
        for j in jobs:
            if j.get('id') == job_id:
                return j
        return None

    def _process_job(self, job_id: str):
        with _lock:
            jobs = _read_jobs()
            job = next((j for j in jobs if j.get('id') == job_id), None)
            if not job:
                return
            job['status'] = 'running'
            _write_jobs(jobs)

        try:
            # call the existing RecipeGalleryService to generate images synchronously
            service = RecipeGalleryService()
            req = job['request']
            result = service.generate_gallery(SimpleNamespace(**req) if False else req)
            # result expected to be serializable
            with _lock:
                jobs = _read_jobs()
                for j in jobs:
                    if j.get('id') == job_id:
                        j['status'] = 'completed'
                        j['result'] = result
                _write_jobs(jobs)
        except Exception as exc:
            with _lock:
                jobs = _read_jobs()
                for j in jobs:
                    if j.get('id') == job_id:
                        j['status'] = 'failed'
                        j['error'] = str(exc)
                _write_jobs(jobs)


# Simple helper to avoid circular import; service expects a dataclass-like object in some code paths.
class SimpleNamespace:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
