# Imibereho

Imibereho ("livelihood / well-being" in Kinyarwanda) is a household financial-resilience demo for
Rwanda. It is an illustrative hackathon demo built on **synthetic data, not official
statistics**.

| Part | Folder | Owner |
|---|---|---|
| Citizen portal and decision-maker workspace (React + TypeScript + Vite) | [`frontend/`](frontend/) | Frontend team |
| API (Python 3.12, FastAPI, PostgreSQL) | [`backend/`](backend/README.md) | Backend team |
| Project documents, requirements, API contract, plan | [`docs/`](docs/) | Shared |

- Start with [`docs/PROJECT_DOCUMENT.md`](docs/PROJECT_DOCUMENT.md).
- The frontend–backend contract is
  [`docs/architecture/api-contract-proposal.md`](docs/architecture/api-contract-proposal.md).
- For backend setup (local PostgreSQL through pgAdmin 4, no Docker), see
  [`backend/README.md`](backend/README.md).
- Backend CI is [`.github/workflows/backend-ci.yml`](.github/workflows/backend-ci.yml). It runs
  only for backend changes.
