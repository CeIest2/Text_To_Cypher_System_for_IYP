# 🧠 Autonomous Cypher Agent
### *for Neo4j · Internet Yellow Pages (IYP)*

> Translate natural language into precise Cypher queries —
> autonomously, accurately, and with self-correcting capabilities.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini_2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](./LICENSE)
[![CypherEval](https://img.shields.io/badge/Benchmark-CypherEval-a855f7?style=flat-square)](https://codeberg.org/dimitrios/CypherEval)

</div>

---

## 📖 Overview

The **Autonomous Cypher Agent** is an advanced, self-healing pipeline designed to bridge the gap between human language and complex Graph Database (Neo4j) queries.

Unlike standard Text-to-Cypher generators, this agent:
- 🔍 **Dynamically explores schemas** before generating any query
- 🧩 **Decomposes complex questions** into logical, sequential sub-tasks
- 🧪 **Tests its own queries** against the live database
- 🔧 **Auto-corrects errors** based on the database engine's feedback

Powered by **Google Gemini** and a strict **Dual-Database Architecture**, it ensures that the target data environment (IYP — Internet Yellow Pages) is accessed securely in **read-only mode**.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎯 **Zero-Hallucination** | Relies on strict schema documentation (`IYP_doc.md`) to prevent hallucinated nodes, relationships, or properties |
| 🧩 **Plan-and-Solve Decomposition** | Breaks down complex queries into iterative sub-tasks based on [arXiv:2312.11242](https://arxiv.org/pdf/2312.11242) |
| 🔧 **Self-Healing Execution** | Catches Neo4j syntax or logic errors and auto-corrects them iteratively via an autonomous *Investigator* agent |
| 🧪 **Tested & Validated** | Rigorously evaluated using the open-source **[CypherEval](https://codeberg.org/dimitrios/CypherEval)** benchmark |
| 🔒 **Strict Output Typing** | Uses **Pydantic** + Gemini Structured Outputs for robust, fully typed data pipelines |
| 🔭 **Full Observability** | Native **Langfuse** integration for tracing reasoning steps, execution time, and token costs |

---

## 🏗️ Multi-Agent Architecture

The system's intelligence relies on five dynamically orchestrated specialized agents:

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUERY                           │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
               ┌───────────────────────┐
               │   Orchestrator Agent  │
               └──────────┬────────────┘
                          │
    ┌─────────────────────▼───────────────────────────────┐
    │  1. 🔍 Pre-Analysis   (Expectations & Context)      │
    │  2. 🔀 Decomposition  (Plan-and-Solve)              │
    │  3. 🔄 Autonomous Loop (per sub-question)           │
    │     ├─ a. ⚙️  Generation   → Cypher query           │
    │     ├─ b. 🛢️  Execution    → Neo4j                  │
    │     ├─ c. ⚖️  Evaluation   → Success / Reject       │
    │     └─ d. 🕵️  Investigation → Diagnostics if failed │
    │  4. 📝 Final Synthesis                              │
    └─────────────────────────────────────────────────────┘
```

### Agent Descriptions

| Agent | File | Role |
|---|---|---|
| 🔍 **Pre-Analyst** | `pre_analyst.py` | Analyzes user intent, establishes business context, determines if an empty result is plausible or an error |
| 🔀 **Decomposer** | `decomposer.py` | Determines if the query requires multiple steps and generates a sequential execution plan *(Plan-and-Solve)* |
| ⚙️ **Request Generator** | `request_generator.py` | Drafts the target Cypher query based on strict IYP schema rules |
| ⚖️ **Evaluator** | `evaluator.py` | Analyzes raw Neo4j results to ensure they actually answer the initial question |
| 🕵️ **Investigator** | `investigator.py` | Generates diagnostic mini-queries to understand failures before attempting a new generation |

---

## 📁 Project Structure

```
cypher_agent/
│
├── agents/                      # Core Multi-Agent Logic
│   ├── decomposer.py            # Plan-and-Solve Agent (arXiv:2312.11242)
│   ├── evaluator.py             # DB feedback validation
│   ├── investigator.py          # Hypothesis testing & diagnostics
│   ├── orchestrator.py          # Main thinking loop & routing
│   ├── pre_analyst.py           # Initial context extraction
│   └── request_generator.py     # Cypher generation
│
├── DataBase/
│   └── IYP_connector.py         # Secure Neo4j driver (read-only)
│
├── docs/
│   └── IYP_doc.md               # Static RAG: Schema & business rules
│
├── utils/
│   ├── helpers.py               # Formatting & file loaders
│   └── llm_caller.py            # Langchain/Gemini wrapper + Langfuse
│
├── run_benchmark.py             # CypherEval benchmark runner
└── parallel_evaluator.py        # Semantic result validator
```

---

## 📦 Prerequisites & Installation

**Requirements:**
- Python 3.9+
- A running Neo4j instance (IYP database)
- Google Gemini API Key *(optimized for `gemini-2.5-flash`)*
- Langfuse account *(highly recommended for debugging and tracing)*

### 1. Clone & Install

```bash
git clone https://github.com/your-org/cypher-agent.git
cd cypher-agent

pip install pydantic neo4j langchain-google-genai langfuse python-dotenv
```

### 2. Configure Environment Variables

Create a `.env` file at the project root:

```env
# ── LLM ───────────────────────────────────────────
GOOGLE_API_KEY=AIzaSy...

# ── Target Database (IYP) ─────────────────────────
IYP_URI=neo4j+s://your-iyp-server.com:7687
IYP_USER=your_user
IYP_PASSWORD=your_password

# ── Observability (Langfuse) ──────────────────────
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 🚀 Usage

Run the **Orchestrator** to process any natural language question through the full pipeline:

```python
import json
from agents.orchestrator import run_autonomous_loop

# Ask your question in natural language
question = "What is the market share of AS 3215 in France?"

# Run the autonomous agent
result = run_autonomous_loop(question)

# Handle the result
if result.get("status") == "SUCCESS":
    print("✅ Final Cypher Query:\n", result["cypher"])
    print("\n📊 Extracted Data:\n", json.dumps(result["data"], indent=2))
else:
    print(f"❌ Failed. Reason: {result.get('reason', 'Max retries reached.')}")
```

The `run_autonomous_loop` function handles the **entire pipeline** automatically:
Pre-analysis → Decomposition → Generation → Execution → Evaluation → Self-Correction → Synthesis.

---

## 🧪 Benchmark & Evaluation

The agent's robustness is tested against **[CypherEval](https://codeberg.org/dimitrios/CypherEval)**, a standardized dataset designed to evaluate LLMs' ability to generate Cypher queries.

The parallel benchmarking scripts (`run_benchmark.py` & `parallel_evaluator.py`) allow you to:

- **Massively run** test prompts of varying difficulty *(Easy, Medium, Hard)*
- **Semantically compare** the agent's output with CypherEval's canonical solutions
- **Generate detailed JSON** performance reports

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](./LICENSE) for details.

