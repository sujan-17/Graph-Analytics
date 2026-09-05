# 🎬 Graph Analytics: Reviewer Demo Script & Presentation Guide

Welcome to the official **Presentation & Live Demonstration Script** for **Graph Analytics: A Multi-Agent System for Stateful Data Analysis**. 

This guide provides a word-for-word script, step-by-step UI actions, timing allocations, and a technical Q&A cheat sheet to impress project reviewers and evaluators.

---

## ⏱️ Demo Time Allocation (Total: 12-15 Minutes)

| Segment | Topic | Focus Area | Duration |
| :--- | :--- | :--- | :--- |
| **Part 1** | Project Pitch & Problem Statement | Why general LLM chatbots fail for enterprise data | 1.5 Min |
| **Part 2** | System Architecture Overview | LangGraph Multi-Agent State Machine & AST Sandbox | 2.5 Min |
| **Part 3** | Dataset Upload & Automated Intelligence | Profiling, Quality Score, Initial Dashboard | 3.0 Min |
| **Part 4** | LangGraph Stateful Conversational Analysis | Live Queries, Plan Inspection, Code AST, Plotly Charts | 5.0 Min |
| **Part 5** | Explainability Audit & PDF Report Export | History Inspector & ReportLab PDF Download | 2.5 Min |
| **Part 6** | Reviewer Q&A | Technical Deep-Dive Defense | Flexible |

---

## 📢 Part 1: Project Pitch & Problem Statement (1.5 Minutes)

### 💬 What to Say:
> *"Good morning/afternoon, evaluators. Today I am presenting **Graph Analytics: A Multi-Agent System for Stateful Data Analysis**.*
>
> *Organizations collect massive amounts of structured business data in CSV files. However, extracting actionable insights usually requires technical expertise in Python, SQL, Power BI, or Tableau.*
>
> *When non-technical managers try using general-purpose AI chatbots like ChatGPT for data analysis, three major problems occur:*
> 1. **Hallucination**: LLMs fabricate numbers when calculating totals or aggregations over large datasets.
> 2. **Data Privacy**: Sending entire raw CSV datasets into LLM prompts violates corporate privacy and exceeds token context limits.
> 3. **Lack of Stateful Memory**: Standard chatbots forget analytical context between follow-up questions like 'Only for 2025' or 'Compare that with last year'.
>
> ***Graph Analytics solves this problem by combining LangGraph multi-agent orchestration with deterministic Pandas execution inside an AST-validated security sandbox.***
>
> *The LLM is strictly used as the reasoning component—while code execution and numerical calculations are performed deterministically on local data."*

---

## 🏗️ Part 2: System Architecture Overview (2.5 Minutes)

### 💻 Screen Action:
Open the architecture diagram from [`PROJECT_EXPLANATION.md`](file:///c:/Users/LENOVO/Desktop/Graph%20Analytics/PROJECT_EXPLANATION.md) or summarize the workflow.

### 💬 What to Say:
> *"Our application is built on a clean 4-tier architecture:*
> 1. **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, and Plotly React.
> 2. **Backend Application**: FastAPI, SQLAlchemy, and SQLite persistence.
> 3. **Orchestration Layer**: LangGraph state machine powered by Google Gemini API.
> 4. **Execution Layer**: AST static code validator and isolated subprocess sandbox worker.
>
> *When a user asks a question, it passes through a 10-node LangGraph workflow:*
> - **Query Understanding Node**: Extracts intent, metric, grouping, and context.
> - **Clarification Node**: Detects ambiguous queries and prompts the user before running code.
> - **Planner Node**: Generates a step-by-step logical plan.
> - **Code Generator Node**: Generates Pandas Python code.
> - **AST Code Validator**: Statically analyzes generated code to block dangerous system imports (`os`, `sys`, `subprocess`, `open`, `eval`).
> - **Subprocess Sandbox**: Runs Pandas code in an isolated worker process with strict timeout controls.
> - **Self-Correction Recovery Node**: If code execution fails, captures the stack trace and auto-corrects the code in a retry loop.
> - **Visualization & Insight Nodes**: Constructs interactive Plotly chart specs and synthesizes executive business insights derived strictly from execution results."*

---

## 📊 Part 3: Dataset Upload & Automated Intelligence (3.0 Minutes)

### 💻 Screen Action:
1. Open browser at `http://localhost:3000`.
2. Login / Register.
3. Click **Create Workspace** $\rightarrow$ Name it `"Retail Sales Strategy Workspace"`.
4. Click **Datasets & Quality** tab $\rightarrow$ Click **Upload New CSV**.
5. Select [`sample_retail_sales.csv`](file:///c:/Users/LENOVO/Desktop/Graph%20Analytics/sample_retail_sales.csv).

### 💬 What to Say:
> *"Let's see this in action. I will upload our business dataset `sample_retail_sales.csv`.*
>
> *Notice what happens immediately upon upload without the user writing a single line of code:*
> 1. **Dataset Profiler**: Calculates dataset health score—here it's **96%**. It checks missing cells, duplicate rows, and provides automated quality recommendations.
> 2. **Column Profiling**: Shows exact data types, unique value counts, null percentages, and statistical summaries (min, max, mean, median, std).
> 3. **Automatic Initial Dashboard**: The backend automatically detected business KPIs—**Total Sales**, **Total Profit**, **Order Count**—and generated initial Plotly Line Trend and Bar Charts on the Overview tab!
> 4. **Proactive Analysis Suggestions**: The system automatically suggested relevant questions like 'Performance analysis grouped by Region' and 'Top product revenue ranking'."*

---

## 🤖 Part 4: LangGraph Stateful Conversational Analysis (5.0 Minutes)

### 💻 Screen Action:
Click the **AI Analyst Chat** tab.

#### Demo Query 1: Initial Analysis
- Type & Send: **`Which region generated the highest revenue?`**

### 💬 What to Say:
> *"Now let's ask our first natural language question: 'Which region generated the highest revenue?'*
>
> *Look at the rich response returned by the multi-agent graph:*
> - **Intent Tag**: Automatically parsed intent as `grouping` on metric `Sales/Revenue` grouped by `Region`.
> - **Plan Accordion**: Expand 'Plan' to show the step-by-step logic: *1. Group records by Region, 2. Sum Sales, 3. Sort descending.*
> - **Inspect Code Button**: Click 'Inspect Code'. Here is the exact AST-validated Pandas Python code generated and executed safely inside our isolated worker process:
>   ```python
>   result = df.groupby('Region', as_index=False)['Sales'].sum().sort_values('Sales', ascending=False)
>   ```
> - **Result Data Table**: Interactive table displaying exact numbers with a 1-click **Export CSV** option.
> - **Interactive Plotly Chart**: Hover over the bar chart to inspect values interactively.
> - **AI Executive Insights**: Concise business explanation derived strictly from the verified table output, along with Actionable Recommendations."*

---

#### Demo Query 2: Stateful Conversational Follow-Up
- Type & Send: **`Only for 2025`**

### 💬 What to Say:
> *"Now notice the power of LangGraph statefulness. I won't re-type the full question. I simply type: 'Only for 2025'.*
>
> *Standard chatbots fail here because they treat every prompt as isolated. But our LangGraph `AnalysisState` retains the active dataset profile, target metric `Sales`, grouping `Region`, and conversation history.*
>
> *The Query Understanding node recognizes that 'Only for 2025' is a date filter modification, updates the state, filters `Order Date` for 2025, and updates the table, Plotly chart, and business insights in real time!"*

---

#### Demo Query 3: Multi-Turn Contextual Comparison
- Click the suggested follow-up chip: **`Show top 5 products`** or type **`Compare top 5 products by profit`**

### 💬 What to Say:
> *"Notice the suggested follow-up chips at the bottom of the response. The system proactively anticipates what a business manager will want to explore next. Clicking a chip immediately executes the next analytical node."*

---

## 📜 Part 5: Explainability Audit & PDF Report Export (2.5 Minutes)

### 💻 Screen Action 1: History Inspector
1. Click the **Analysis History** tab.
2. Expand the top analysis entry.

### 💬 What to Say:
> *"For enterprise compliance and auditing, every single analysis run is recorded in the **Analysis History** tab. Evaluators can inspect the exact Query Intent JSON, logical plan steps, AST-validated Python snippet, and execution status."*

---

### 💻 Screen Action 2: PDF Report Export
1. Click **Save Insight** on an AI response in the Chat tab.
2. Click the **Reports & Insights** tab.
3. Show bookmarked insight.
4. Type Report Title: `"Q1 Executive Revenue & Sales Report"`.
5. Click **Generate PDF Report** $\rightarrow$ Click **Download PDF**.
6. Open the generated PDF file.

### 💬 What to Say:
> *"Finally, once managers complete their analysis, they can bookmark key findings and generate an executive PDF report. Our backend uses ReportLab to dynamically compile the executive summary, dataset health score, KPIs, bookmarked insights, and safety methodology into a polished PDF document ready for board presentations!"*

---

## 🎯 Part 6: Reviewer Q&A Cheat Sheet (Anticipated Questions & Answers)

### Q1: Why did you use LangGraph instead of a simple LangChain LLMChain?
> **Answer**: *"Standard LLM chains are linear (Prompt $\rightarrow$ Output). Data analysis requires stateful memory, conditional branching, validation cycles, and self-correction. LangGraph allows us to define a stateful graph where nodes represent specialized agents (Query Parser, Planner, Code Generator, Validator, Recovery Agent) and edges control conditional flow—such as requesting user clarification or triggering an error recovery retry loop when execution fails."*

---

### Q2: How do you prevent the LLM from hallucinating numbers or metrics?
> **Answer**: *"We never ask the LLM to perform math or calculations! The LLM's role is strictly limited to translating natural language intent into structured Python/Pandas code. All calculations are executed deterministically on the actual CSV DataFrame using Pandas in local python runtime. The insight generator node then receives the verified DataFrame output and is instructed to summarize only numbers present in the table."*

---

### Q3: How do you secure the server against malicious code execution?
> **Answer**: *"We implement defense-in-depth security:*
> 1. **AST Static Analysis**: Before running any generated code, Python's `ast.NodeVisitor` parses the syntax tree to detect forbidden imports (`os`, `sys`, `subprocess`, `socket`, `open`, `eval`, `exec`).
> 2. **Subprocess Isolation**: Generated code is NEVER executed inside the main FastAPI process. It is run in a separate, isolated worker process (`worker.py`).
> 3. **Timeouts**: Process execution has a 15-second timeout limit to prevent infinite loops or Denial-of-Service."*

---

### Q4: How does the system resolve ambiguous user queries?
> **Answer**: *"If a user asks an underspecified question like 'Show revenue' when the dataset contains both 'Gross Revenue' and 'Net Revenue', the Query Understanding node sets `needs_clarification: true`. The workflow halts before code generation and returns a clarification message with selectable option buttons to the user."*

---

### Q5: What happens if generated code encounters a runtime error?
> **Answer**: *"Our graph includes an automated **Self-Correction Recovery Node**. If the subprocess execution returns an error (such as a KeyError due to a mismatched column name), the recovery agent receives the error traceback and dataset schema, fixes the code, and retries execution automatically up to 2 times."*
