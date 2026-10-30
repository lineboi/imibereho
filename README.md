# Imibereho (Household Financial Resilience & Public Planning Portal)

**Imibereho** (*"Livelihood / Well-Being"* in Kinyarwanda) is a dual-engine household financial resilience and public policy simulation platform tailored for Rwanda.

The platform bridges micro-level citizen financial management with macro-level public policy planning, grounded in official statistical baselines from the National Institute of Statistics of Rwanda (**NISR**), **MINECOFIN**, and **Access to Finance Rwanda (AFR)**.

---

## 🌐 Live Public Deployment

- **Production URL**: [https://imibereho.vercel.app](https://imibereho.vercel.app)
- **Direct Tunnel Fallback**: [https://bike-talking-requested-ascii.trycloudflare.com](https://bike-talking-requested-ascii.trycloudflare.com)
- **API Readiness Check**: [https://imibereho.vercel.app/ready](https://imibereho.vercel.app/ready)
- Demonstration video: [https://drive.google.com/file/d/1jQ4Xwip7Mw0HB2XjH5yBMmI3UThXDSVQ/view?usp=sharing](https://drive.google.com/file/d/1jQ4Xwip7Mw0HB2XjH5yBMmI3UThXDSVQ/view?usp=sharing)

---

## Repository Structure

```text
imibereho/
├── README.md          Project documentation
├── app.py             Starts the API from the repository root
├── requirements.txt   Python packages for the API
├── backend/           FastAPI API, database migrations and tests
├── frontend/          React web application
├── data/              CSV copies of the data used (official and synthetic)
├── demo/              Demonstration video
├── student_cards/     Eligibility documents
└── docs/
    ├── architecture/  Project document and backend requirements
    ├── api/           API contract and endpoint documents
    ├── data/          Data evidence notes
    └── development/   Plans, requirements and engineering audit
```

---

## Hardcoded Presentation & Testing Credentials

For evaluators, juries, and presentation demonstrations, two hardcoded accounts are pre-seeded in the live PostgreSQL database:

| Persona | Email / Identifier | Password | Database Role | Access Portal |
| :--- | :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@imibereho.rw` | `Citizen2026!` | `citizen` | **Citizen Portal** (Personal Budgeting, Daily Tracker, Agro-Swaps, Resilience Simulator) |
| **Government / Decision-Maker** | `planner@imibereho.rw` | `Planner2026!` | `decision_maker` | **Public Planning Workspace** (Macro Overview, 30-District Heatmap, Policy Cash Transfer Simulator) |

> **Presentation Tip (1-Click Fill)**: Open the **Sign In** modal anywhere in the app to find the **Preset Testing Accounts** card. Clicking either button instantly populates the testing credentials with zero typing needed.

---

## Role-Based Architecture & Portal Routing

Access between the two platforms is governed **strictly by the user's role stored in the PostgreSQL database** (`household_accounts.role`):

- **No manual switch buttons**: The user's authenticated session profile dynamically decides whether the application renders the Citizen Portal or the Public Planning Workspace.
- **Dynamic Role Management**: Any user can switch their role directly inside their **Household Profile** modal (`Platform Role & Workspace` &rarr; *Citizen* vs *Decision-Maker*). Saving updates PostgreSQL (`PATCH /api/v1/user/profile`) and immediately shifts the active workspace.
- **Direct Database Assignment**:
  ```sql
  -- Switch to Government Decision-Maker Workspace
  UPDATE household_accounts SET role = 'decision_maker' WHERE identifier = 'citizen@imibereho.rw';

  -- Switch to Citizen Portal
  UPDATE household_accounts SET role = 'citizen' WHERE identifier = 'planner@imibereho.rw';
  ```

---

## Platform Modules

### 1. Citizen Portal (`role: citizen`)
- **Daily Budget Health & Tracker**: Real-time spending tracker calculating daily safe-to-spend limits, remaining cushion, and category breakdown (Food, Transport, Utilities, Other). All transactions persist to PostgreSQL `tracker_transactions`.
- **District Living Standards Advisor**: Compares household spending against official EICV7 benchmarks across all 30 Rwandan districts, factoring in household size and inflation Paasche deflators.
- **Seasonal Agro-Swaps**: Recommends affordable, locally abundant seasonal staple food alternatives (e.g., swapping Irish Potatoes for Sweet Potatoes in Season A) to protect nutritional security during price spikes.
- **Household Resilience Simulator**: Tests household vulnerability against real-world economic shocks (e.g. 25% income dip, school fees, medical emergencies) with runway calculations and active coping levers.

---

### 2. Decision-Maker / Public Planning Workspace (`role: decision_maker`)
- **Macro Overview**:
  - 4 Live KPI Cards: Synthetic Sample (3,000 households), Reference Monthly Income (500,000 RWF), Average Essentials Ratio, and Zero-Cushion Headcount.
  - 6-Month Essentials Trend bar chart with reference income guidelines.
  - Primary income sources breakdown (Wage, Agriculture, Informal Enterprise).
  - Policy gap insights and priority district recommendations.
- **District Heatmap**:
  - Full 30-district interactive colored tile grid (5 rows &times; 6 columns).
  - Risk Bands: **Band 1** (0–39, Low), **Band 2** (40–59, Moderate), **Band 3** (60–69, High), **Band 4** (70–100, Critical).
  - Selected district drill-down displaying composite sub-indicators (40% income instability, 40% essential-cost pressure, 20% low-buffer exposure).
  - Highest Demo Scores ranking the top 6 vulnerable districts in Rwanda.
- **Policy Cash Transfer Simulator**:
  - Dynamic simulation of fiscal intervention scenarios (e.g. 6,000 RWF to 25,000 RWF/month across 500 to 10,000 households).
  - Direct fiscal budget calculations (`Budget = Support x Duration x Households`).
  - Household balance sheet scenario comparison matrix (*Baseline* vs *Shock only* vs *Shock + support*).
- **Data Methodology & Institutional Evidence Base**:
  - Official survey citations (EICV7 2023/24, FinScope 2024, Seasonal Agricultural Survey 2025).
  - Mathematical formula breakdowns, candidate data integration pipeline, and pre-production governance checklist.

---

## Tech Stack & Data Integrity

- **Frontend**: React 19, TypeScript, Tailwind CSS, Lucide Icons, Vite.
  - Zero static simulation objects: all metrics, charts, transactions, and benchmarks are dynamically fetched from the live backend.
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL 16+.
  - Passwords hashed using Argon2id (`$argon2id$...`).
  - Strict OpenAPI validation contract governing all endpoints.

---

## Running the Project Locally

### 1. Backend Service
```bash
cd backend
~/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Health & Readiness Check:
```bash
curl http://127.0.0.1:8000/ready
# {"status":"ready","checks":{"database":"ok","migrations":"ok","seed":"ok"}}
```

### 2. Frontend Application
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 3. Linting & Production Build
```bash
cd frontend
npm run lint    # 0 errors, 0 warnings
npm run build   # Production asset compilation
```
