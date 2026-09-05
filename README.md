# Graph Analytics: A Multi-Agent System for Stateful Data Analysis

A full-stack, enterprise-grade AI-powered conversational analytics workspace built with **LangChain**, **LangGraph**, **FastAPI**, **Pandas**, **Plotly**, **ReportLab**, and **React + TypeScript + Vite + Tailwind CSS**.

---

## 🌟 Key Product Differentiators

1. **Multi-Agent LangGraph Workflow**: State-machine architecture orchestrating Query Understanding, Ambiguity Clarification, Logical Planning, AST-Validated Code Generation, Isolated Sandbox Execution, Error Recovery Loop, Result Validation, Chart Spec Generation, Business Insight Synthesis, and Follow-up Question Suggestions.
2. **AST-Validated Isolated Sandbox**: Security layer enforcing AST static analysis to block dangerous module imports (`os`, `sys`, `subprocess`, `socket`, `open`, `eval`, `exec`), running Pandas snippets in an isolated worker process with strict timeout limits.
3. **Dataset Profiler & Quality Engine**: Automated CSV profiling calculating row/column metrics, data types, unique values, missing cell %, duplicate counts, dataset health score (0-100%), and automatic KPI candidate detection.
4. **Initial Dashboard & Interactive Plotly Charts**: Automatic initial line and bar chart generation upon CSV upload, and interactive Plotly visualization for every analytical response.
5. **Stateful Conversational Context**: Preserves dataset context, active filters, previous metrics, and conversational history across questions (e.g. *"Show revenue by region"* $\rightarrow$ *"Only for 2025"* $\rightarrow$ *"Compare that with 2024"*).
6. **Executive PDF Reports**: ReportLab PDF generation compiling executive summary, dataset quality score, key KPIs, saved insights, and analytical findings into downloadable PDF documents.

---

## 🛠️ Project Structure

```
Graph Analytics/
├── backend/
│   ├── venv/                      # Python virtual environment
│   ├── app/
│   │   ├── main.py                # FastAPI entry point & CORS configuration
│   │   ├── core/                  # Security, JWT, SQLite database config
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── services/              # Dataset profiling, dashboard, PDF reports, storage
│   │   ├── execution/             # AST validator & isolated subprocess sandbox
│   │   ├── graph/                 # LangGraph AnalysisState & Multi-Agent nodes
│   │   └── api/                   # REST API endpoints
│   ├── storage/                   # Datasets, reports, export files & sample CSV
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # Layout, Dashboard, Profiler, AI Analyst Chat, Reports
│   │   ├── pages/                 # Auth, Dashboard, Workspace pages
│   │   ├── services/              # Axios API clients
│   │   └── types/                 # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: 3.11+
- **Node.js**: v18+ and `npm`

### 2. Backend Setup
```bash
cd backend

# Virtual environment is pre-configured at backend/venv
# To activate on Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install requirements (if modifying):
pip install -r requirements.txt

# Start FastAPI Backend Server:
uvicorn app.main:app --reload --port 8000
```
Backend API interactive documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies:
npm install

# Start Vite React Frontend Development Server:
npm run dev
```
Open `http://localhost:3000` (or `http://localhost:5173`) in your web browser.

---

## 🔑 Setting your Gemini API Key

You can configure your free Google Gemini API Key in two ways:
1. In the Frontend UI top header bar: Click **API Key** and enter your key.
2. In `backend/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

---

## 📊 Sample CSV Dataset Included

A realistic sample sales dataset is included at `backend/storage/sample_sales.csv` (`Order ID`, `Order Date`, `Region`, `Category`, `Product`, `Sales`, `Profit`, `Quantity`, `Customer Type`, `Discount`). Upload it to test profiling, initial dashboards, multi-turn stateful conversational analysis, and PDF report generation!
