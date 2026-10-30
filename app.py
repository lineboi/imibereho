"""Start the Imibereho API from the repository root.

    pip install -r requirements.txt
    python app.py

The solution's code is in `backend/` (FastAPI API) and `frontend/` (React web app). This file only
starts the API, on port 8000 unless PORT says otherwise; it needs `backend/.env` and a migrated,
seeded database (see README.md).
"""

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", app_dir="backend", host="0.0.0.0", port=port)  # noqa: S104
