"""DEPRECATED.

The Streamlit application has been replaced by a modern JavaScript (React +
Vite + TypeScript + Tailwind) frontend backed by a FastAPI + Pydantic AI
service.

* Backend:  ``backend/app`` (run with ``uvicorn app.main:app`` from ``backend/``)
* Frontend: ``frontend`` (run with ``npm run dev``)
* Deploy:   ``deploy`` (Nginx + systemd for Ubuntu EC2)

See ``README.md`` and ``plans/paige-js-migration-plan.md`` for details.
"""

if __name__ == "__main__":
    raise SystemExit(
        "app.py (Streamlit) is deprecated. Start the FastAPI backend with "
        "'uvicorn app.main:app' from the backend/ directory and the React "
        "frontend with 'npm run dev' from the frontend/ directory."
    )
