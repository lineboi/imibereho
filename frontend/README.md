# Imibereho — Frontend Application

React 19 + TypeScript + Vite frontend client for the **Imibereho** Household Financial Resilience & Public Planning Portal.

---

## Presentation & Testing Credentials

Two pre-seeded testing accounts are configured in the PostgreSQL database for evaluation:

| Account Type | Email / Login | Password | Database Role | Landing View |
| :--- | :--- | :--- | :--- | :--- |
| **Citizen Portal** | `citizen@imibereho.rw` | `Citizen2026!` | `citizen` | Household Tracker, Agro-Swaps, Resilience |
| **Decision-Maker** | `planner@imibereho.rw` | `Planner2026!` | `decision_maker` | Macro Overview, 30-District Heatmap, Policy Simulator |

> **1-Click Demo Fill**: In the Sign-In modal, click either preset card to auto-fill these credentials without typing.

---

## Key Modules & UI Structure

### Citizen Portal (`role: citizen`)
- **Daily Tracker** ([`src/components/DailyTracker/`](src/components/DailyTracker/)): Safe-to-spend gauge, transaction logging, real PostgreSQL sync.
- **District Advisor** ([`src/components/DistrictAdvisor/`](src/components/DistrictAdvisor/)): 30-district EICV7 benchmark comparison.
- **Seasonal Agro-Swaps** ([`src/components/SeasonalAgroSwaps/`](src/components/SeasonalAgroSwaps/)): Affordable staple substitutions for food security.
- **Resilience Simulator** ([`src/components/ResilienceSimulator/`](src/components/ResilienceSimulator/)): Household economic runway shock testing.

### Government Decision-Maker Workspace (`role: decision_maker`)
- **Macro Overview** ([`src/components/DecisionMaker/MacroOverviewView.tsx`](src/components/DecisionMaker/MacroOverviewView.tsx)): Live KPIs, 6-month trends, income source shares.
- **District Heatmap** ([`src/components/DecisionMaker/DistrictHeatmapView.tsx`](src/components/DecisionMaker/DistrictHeatmapView.tsx)): 5x6 colored tile grid of all 30 districts, score bands, composite sub-indicators.
- **Policy Simulator** ([`src/components/DecisionMaker/PolicySimulatorView.tsx`](src/components/DecisionMaker/PolicySimulatorView.tsx)): Fiscal cash transfer modeling and household balance sheet comparison.
- **Data Methodology** ([`src/components/DecisionMaker/DataMethodologyView.tsx`](src/components/DecisionMaker/DataMethodologyView.tsx)): NISR, FinScope, and SAS official citations.

---

## Development & Build Commands

```bash
# Start development server
npm run dev

# Run TypeScript & ESLint verification
npm run lint

# Production build
npm run build
```
