# Sellora - Real Profitability SaaS for Indian Marketplace Sellers

Sellora is a production-grade multi-tenant SaaS platform built for Indian e-commerce merchants selling on **Amazon India** (`amazon.in`) and **Flipkart** (`seller.flipkart.com`). It eliminates financial guesswork by calculating **real net profit** down to the SKU level—accounting for marketplace commissions, closing fees, shipping/logistics, returns/RTO, advertising spend, and custom product unit acquisition costs (COGS).

---

## Architecture & Technology Stack

### 1. Technology Choices & Rationale
* **FastAPI (Python)**: High-performance, async-capable REST API with native Pydantic v2 data validation, OpenAPI/Swagger auto-generation, and strong typing.
* **SQLAlchemy 2.0 + PostgreSQL 16**: Normalized, relational schema with foreign key constraints, indexes, and strict support for `Numeric(12, 2)` decimal types.
* **Celery + Redis**: Asynchronous background job processing for marketplace synchronization without locking the web server or client browser.
* **Next.js 14 (App Router) + TypeScript + Tailwind CSS**: Server-rendered and client-cached React application with type safety, responsive layout, and modern UI tokens.
* **TanStack Query (React Query)**: Robust state management with query deduplication, optimistic updates, and background refetching.
* **Recharts**: Responsive SVG charting tailored for financial time-series visualization.
* **Docker Compose**: Containerized multi-service orchestration ensuring 100% parity between local development and production deployment.

### 2. Core Architectural Principles
* **Marketplace Abstraction Layer**: Core services interact exclusively with the standardized data models (`StandardOrder`, `StandardProduct`, `StandardFee`) defined in `app/integrations/marketplaces/base.py`. Amazon India and Flipkart connectors translate external payloads into internal models.
* **Tenant Isolation**: Every database entity (`products`, `orders`, `fees`, `expenses`, `sync_jobs`) is strictly foreign-keyed to `organization_id`. API endpoints enforce organizational scoping.
* **Deterministic Decimal Precision**: Financial calculations never use IEEE 754 floating-point numbers. All math uses Python `Decimal` and SQL `Numeric`.

---

## Directory Structure

```text
sellora/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints (health, dashboard, products, orders, profit, marketplaces)
│   │   ├── core/            # Config, database engine, security, auth dependencies
│   │   ├── models/          # Normalized SQLAlchemy models (User, Org, Product, Order, Fee, etc.)
│   │   ├── schemas/         # Pydantic v2 request/response contracts
│   │   ├── integrations/    # MarketplaceConnector abstraction & mock implementations
│   │   ├── services/        # Deterministic profit engine & seed data generator
│   │   ├── workers/         # Celery task queue & worker definition
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Pytest suite (health, profit engine, tenant isolation, abstraction)
│   ├── Dockerfile           # Python 3.11 container definition
│   └── requirements.txt     # Backend dependencies
│
├── frontend/
│   ├── app/                 # Next.js App Router pages (dashboard, products, orders, profit, marketplaces)
│   ├── components/          # UI components (sidebar, header, metric cards, charts, tables)
│   ├── lib/                 # API client, currency formatting (₹), and utility helpers
│   ├── types/               # TypeScript interfaces
│   ├── Dockerfile           # Node.js container definition
│   └── package.json         # Frontend dependencies
│
├── docker-compose.yml       # Orchestrates Postgres, Redis, FastAPI, Celery worker & Next.js
├── .env.example             # Template for all environment variables
└── README.md
```

---

## Running Locally

### Option 1: Using Docker Compose (Recommended)

1. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

2. Build and start all services:
   ```bash
   docker compose up --build
   ```

3. Access the services:
   * **Web Dashboard**: [http://localhost:3000](http://localhost:3000)
   * **API Documentation (Swagger UI)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   * **API Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Option 2: Running Directly on Host (Development)

#### 1. Backend

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run automated tests:
   ```bash
   cd backend
   pytest -v
   ```

4. Start the FastAPI server:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

#### 2. Frontend

1. Install Node dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start Next.js development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000).

---

## Phase 1 Verification Checklist

- [x] **Monorepo scaffolding**: Standardized structure for frontend, backend, worker, and documentation.
- [x] **PostgreSQL normalized schema**: Organizations, Users, MarketplaceAccounts, Products, Orders, OrderItems, Fees, Expenses, AdvertisingCosts, and SyncJobs.
- [x] **Tenant isolation**: Scoped queries and dependency verification ensuring zero cross-tenant data leakage.
- [x] **Deterministic Profit Engine**: Exact formula implemented and tested:
  $$\text{Net Profit} = \text{Revenue} - \text{COGS} - \text{Fees} - \text{Shipping} - \text{Ads} - \text{Returns} - \text{Other}$$
  $$\text{Margin \%} = \frac{\text{Net Profit}}{\text{Revenue}} \times 100$$
- [x] **Marketplace Abstraction Layer**: `MarketplaceConnector` abstract base class ready for official Amazon SP-API and Flipkart integrations.
- [x] **SaaS Frontend UI**: Dashboard with ₹ currency formatting, KPI metrics, revenue vs net profit charts, product COGS editor, order ledger, and marketplace connection cards.
