# 🧠 Autonomous Cypher Agent
### *for Neo4j · Internet Yellow Pages (IYP)*

> Translate natural language into precise, executable Cypher queries —
> autonomously, accurately, and with self-correcting capabilities.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini_2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](./LICENSE)
[![CypherEval](https://img.shields.io/badge/Benchmark-CypherEval-a855f7?style=flat-square)](https://codeberg.org/dimitrios/CypherEval)

---

## 📖 Overview

The **Autonomous Cypher Agent** is an advanced, self-healing pipeline that bridges the gap between natural language and complex Neo4j graph database queries. It was built specifically for the **Internet Yellow Pages (IYP)** (https://github.com/InternetHealthReport/internet-yellow-pages) knowledge graph — a large-scale graph database mapping AS numbers, IP prefixes, domain names, IXPs, countries, rankings, and their interconnections across the global internet infrastructure.

Unlike standard Text-to-Cypher generators, this agent:

- 🔍 **Grounds every query in a verified schema** (`IYP_doc.md`) to prevent hallucinated nodes, relationships, or properties
- 🧩 **Decomposes complex questions** into sequential sub-tasks using a Plan-and-Solve strategy (inspired by [arXiv:2312.11242](https://arxiv.org/pdf/2312.11242))
- 🧪 **Tests its own queries** against the live database before returning any result
- 🔧 **Auto-corrects errors** based on real Neo4j feedback through a dedicated Investigator agent
- 🔭 **Traces every reasoning step** end-to-end via native Langfuse integration

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎯 **Schema-Grounded Generation** | Every query is generated using a strict schema reference (`IYP_doc.md`) — no hallucinated labels, relationships, or property names |
| 🧩 **Plan-and-Solve Decomposition** | Complex multi-hop questions are automatically broken into ordered sub-tasks, with intermediate results passed as context |
| 🔧 **Self-Healing Loop** | Neo4j syntax or logic errors trigger an autonomous Investigator that runs diagnostic mini-queries and produces a factual correction report |
| 🔍 **RAG-Augmented Generation** | A vector database (Neo4j local instance) stores semantically indexed Cypher examples — retrieved at inference time to guide the generator |
| 🔒 **Strict Output Typing** | All LLM outputs are validated through Pydantic schemas with Gemini Structured Outputs — no fragile string parsing |
| 🔭 **Full Observability** | Native Langfuse integration for tracing reasoning steps, LLM calls, token costs, and execution time per agent |
| ⚡ **Parallel Benchmarking** | Multi-threaded benchmark runner and semantic evaluator allow large-scale evaluation runs with real-time score updates |

---

## 🏗️ Multi-Agent Architecture

The system orchestrates five specialized agents in a dynamic loop:

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUERY                           │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
               ┌───────────────────────┐
               │ LangGraph State Graph │
               └──────────┬────────────┘
                          │
    ┌─────────────────────▼───────────────────────────────┐
    │  1. 🔍 Pre-Analysis   (Context & expectations)      │
    │  2. 🔍 RAG Retrieval  (Similar past examples)       │
    │  3. 🔀 Decomposition  (Plan-and-Solve)              │
    │  4. 🔄 Autonomous Loop (per sub-question)           │
    │     ├─ a. ⚙️  Generation   → Cypher query           │
    │     ├─ b. 🛢️  Execution    → Live Neo4j             │
    │     ├─ c. ⚖️  Evaluation   → Success / Reject       │
    │     └─ d. 🕵️  Investigation → Diagnostics if failed │
    │  5. 📝 Final Synthesis                              │
    └─────────────────────────────────────────────────────┘
```

### Agent Roles

| Agent | File | Role |
|---|---|---|
| 🔍 **Pre-Analyst** | `agents/pre_analyst.py` | Establishes real-world context, expected output type, plausibility of empty results, and a dense technical translation for RAG search |
| 🔀 **Decomposer** | `agents/decomposer.py` | Decides if the question requires multiple steps; if so, generates an ordered execution plan with typed inter-step outputs |
| ⚙️ **Request Generator** | `agents/request_generator.py` | Drafts the Cypher query based on the IYP schema, RAG context, and all previous failed attempts |
| ⚖️ **Evaluator** | `agents/evaluator.py` | Analyzes the raw Neo4j output to verify it genuinely answers the question; returns a typed verdict with correction hints |
| 🕵️ **Investigator** | `agents/investigator.py` | On failure, generates and executes diagnostic mini-queries to produce a factual report for the next generation attempt |

---

## 📁 Project Structure

```
cypher_agent/
│
├── agents/
│   ├── graph_orchestrator.py    # Main LangGraph entry point & routing logic
│   ├── nodes.py                 # LangGraph nodes wrapping agent functions
│   ├── state.py                 # Pydantic/TypedDict state definitions
│   ├── decomposer.py            # Plan-and-Solve decomposition
│   ├── evaluator.py             # Result validation agent
│   ├── investigator.py          # Diagnostic & correction agent
│   ├── pre_analyst.py           # Context extraction agent
│   ├── request_generator.py     # Cypher generation agent
│   └── orchestrator.py          # (Legacy) Procedural loop orchestrator
│
├── DataBase/
│   ├── IYP_connector.py         # Secure Neo4j driver (read-only, traced)
│   ├── rag_retriever.py         # Vector search over RAG database
│   └── rag_db/
│       ├── build_rag_dataset.py # Generates annotated Cypher examples (LLM)
│       ├── setup_rag_db.py      # Embeds and indexes examples into Neo4j
│       └── docker-compose.yml   # Local Neo4j instance for RAG
│
├── docs/
│   ├── IYP_doc.md               # Master schema reference (nodes, relationships, properties)
│   ├── few_shot_examples-variation-A.json      # synthetic augmented data for the RAG
│   └── few_shot_examples-variation-A.json      # synthetic augmented data for the RAG
│
├── utils/
│   ├── helpers.py               # Formatting & file utilities
│   └── llm_caller.py            # LangChain/Gemini wrapper with Langfuse tracing
│
├── run_benchmark.py             # Parallel benchmark runner (CypherEval)
└── parallel_evaluator.py        # Semantic equivalence evaluator
```

---

## 🧪 Benchmark Results

The agent was evaluated against **[CypherEval](https://codeberg.org/dimitrios/CypherEval)**, a standardized dataset containing hundreds of real-world natural language prompts mapped to canonical Cypher solutions for the IYP graph. Queries are categorized into six difficulty levels combining technical precision and general phrasing.

### Evaluation Methodology

Inspired by the functional correctness evaluation pipeline presented in the **[Pythia: Facilitating Access to Internet Data Using LLMs and IYP](https://www.iijlab.net/en/members/romain/pdf/dimitrios_lcn2025.pdf)** paper, we implemented an automated **Semantic Evaluator**. A highly capable LLM-judge executes both the agent's generated query and the canonical solution against the live Neo4j database. It then compares the factual results to determine a match, disregarding structural differences or extra explanatory columns.

The pipeline runs one strict, bottom-line metric:

> 🎯 **Semantic Equivalence Rate** — The executed query returned the exact same factual data as the canonical reference solution.

---

### 1. The Impact of Agentic RAG (Ablation Study)

To prove the efficacy of retrieving contextually similar queries, we ran the benchmark across both CypherEval variations **with and without** the local Neo4j Vector RAG enabled.

Results show that injecting few-shot RAG examples into the context dramatically reduces semantic hallucinations, boosting the equivalence score by **up to 14.7%**.

| Dataset | Setup | Semantic Equivalence Rate | RAG Impact |
|---|---|---|---|
| Variation A | No RAG | 56.9% (94 / 165) | — |
| Variation A | With RAG (Var B) | 66.1% (107 / 162) | **+ 9.2 %** |
| Variation B | No RAG | 49.1% (80 / 163) | — |
| Variation B | With RAG (Var A) | 63.8% (104 / 163) | **+ 14.7 %** |

---

### 2. Detailed Performance by Difficulty (Best Run: Var-A with RAG)

This details the **66.1% global semantic score**.

| Difficulty Level | Semantic Equivalence |
|---|---|
| 🟢 Easy Technical | 90.6% (29 / 32) |
| 🟢 Easy General | 87.5% (28 / 32) |
| 🟡 Medium Technical | 53.1% (17 / 32) |
| 🟡 Medium General | 51.5% (17 / 33) |
| 🔴 Hard Technical | 53.3% (8 / 15) |
| 🔴 Hard General | 44.4% (8 / 18) |

---

### 3. Comparison with the "Pythia" State-of-the-Art

In the original study, models like CodeLlama, DeepSeek, and Qwen were evaluated using the `pass@k` metric, which estimates the probability of finding at least one correct query among *k* generated samples. The dedicated Pythia system (utilizing static few-shot prompting) achieved roughly **75% `pass@20`** for easy general prompts, near **50%** for medium prompts, and around **25% `pass@k`** for hard prompts.

Our Autonomous Agent fundamentally shifts this paradigm: because our system incorporates a self-healing LangGraph loop (the Investigator agent), it operates from the user's perspective at an effective **`pass@1`**. The user asks once, and the agent iterates internally to deliver a single final answer.

- **Easy Prompts:** Our agent reaches **~87–90% Semantic Equivalence** on its single final output, beating Pythia's highly sampled `pass@20`.
- **Hard Prompts:** Our agent achieves **44%–53% Semantic Equivalence**, nearly doubling Pythia's heavily sampled `pass@k` performance (~25%). This highlights the superiority of autonomous diagnostic testing over blind LLM sampling.

---

### Key Observations & Limitations

1. **Schema Grounding Triumphs** — Easy queries are handled with near-perfect reliability (~90%), demonstrating that strict schema injection and RAG retrieval prevent basic syntax errors and hallucinated labels.

2. **The "Semantic Drift" Challenge** — When the agent fails on medium/hard queries, it is rarely due to a database crash or syntax error. Instead, it suffers from *semantic drift*: the agent successfully writes and validates a complex Neo4j query, but explores a plausible yet incorrect graph traversal path compared to the canonical solution (e.g., misinterpreting vague ranking requests or complex multi-hop DNS resolutions).

3. **Implicit Intent** — Hard general queries remain the ultimate challenge. They require the agent to infer deeply technical graph strategies from extremely vague natural language, without explicit node or relationship hints.

## 📦 Prerequisites & Installation

**Requirements:**
- Python 3.9+
- A running Neo4j instance with the IYP database
- Google Gemini API Key *(optimized for `gemini-2.5-flash`)*
- Langfuse account *(required for prompt management and tracing)*
- Docker *(optional, for the local RAG Neo4j instance)*

### 1. Clone & Install

```bash
git clone https://github.com/your-org/cypher-agent.git
cd cypher-agent
pip install pydantic neo4j langchain-google-genai langfuse langchain-core python-dotenv langgraph
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

# ── RAG Database (local) ──────────────────────────
RAG_URI=bolt://localhost:7688
RAG_USER=neo4j
RAG_PASSWORD=password

# ── Observability (Langfuse) ──────────────────────
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. (Optional) Start the RAG Database

```bash
cd DataBase/rag_db
docker compose up -d
python setup_rag_db.py
```

---

## 🚀 Usage

### Single Query

```python
import json
from agents.graph_orchestrator import run_graph_agent

question = "What is the market share of AS 3215 in France?"

# Launches the LangGraph pipeline
result = run_graph_agent(question, use_rag=True)

if result.get("status") == "SUCCESS":
    print("✅ Final Cypher Query:\n", result["cypher"])
    print("\n📊 Results:\n", json.dumps(result["data"], indent=2))
else:
    print(f"❌ Failed after {result['iterations']} attempts.")
```

The `run_autonomous_loop` function drives the **entire pipeline automatically**: Pre-analysis → RAG Retrieval → Decomposition → Generation → Execution → Evaluation → Self-Correction → Synthesis.

| Parameter | Type | Description |
|---|---|---|
| `question` | `str` | Natural language question |
| `max_retries` | `int` | Maximum correction attempts per sub-question (default: 4) |
| `use_rag` | `bool` | Enable RAG retrieval for similar examples (default: False) |
| `session_id` | `str` | Optional Langfuse session identifier |

### Run the Full Benchmark

```bash
python run_benchmark.py
```

This launches a parallel evaluation on `variation-B.csv` with 12 concurrent workers. Progress and scores are printed in real time. Results are saved incrementally to a JSON report.

### Run Semantic Post-Evaluation

```bash
python parallel_evaluator.py
```

Takes an existing benchmark JSON (with generated Cypher queries), executes both generated and canonical queries against the live database in parallel, and uses an LLM judge to determine semantic equivalence.

---

## 🔍 How the RAG System Works

The RAG pipeline enriches query generation with validated examples from a local vector database:

1. **Dataset Building** (`build_rag_dataset.py`): For each entry in a reference CSV, an LLM annotates the canonical Cypher query with an `abstract_intent` (generalized version of the question) and a `methodology` (graph traversal strategy using exact node/relationship labels).

2. **Indexing** (`setup_rag_db.py`): Each annotated example is embedded with `gemini-embedding-001` and stored as a `CypherExample` node in a local Neo4j instance with a cosine vector index.

3. **Retrieval** (`rag_retriever.py`): At inference time, the Pre-Analyst's `technical_translation` is embedded and used to query the vector index for the top-k most similar examples, which are formatted and injected into the Generator and Decomposer prompts.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](./LICENSE) for details.
