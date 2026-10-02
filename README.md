# CollabAI — Documentation Set

Build documentation for the final-year major project **CollabAI: An Agentic Collaborative Workspace with Shared Retrieval-Augmented Memory**.

These files are written to be fed to **Antigravity** (or any agentic IDE) as project context. Read them in order.

| # | File | What it is | Who reads it |
|---|------|-----------|--------------|
| 00 | `00-PROJECT-DESCRIPTION.md` | Problem, solution, novelty, academic framing | You + faculty + Antigravity |
| 01 | `01-PROMPT.md` | Copy-paste prompts for Antigravity, phase by phase | Antigravity |
| 02 | `02-ARCHITECTURE.md` | System architecture, request flows, agent pipeline | Antigravity |
| 03 | `03-DATA-MODEL.md` | MongoDB collections, fields, indexes | Antigravity |
| 04 | `04-API-SPEC.md` | Every REST + WebSocket endpoint | Antigravity |
| 05 | `05-AGENTS-AND-RAG.md` | LangGraph graph, agent prompts, RAG pipeline, LLM fallback | Antigravity |
| 06 | `06-FRONTEND-SPEC.md` | Screens, components, states, design tokens | Antigravity |
| 07 | `07-BUILD-PLAN.md` | Ordered tasks with acceptance criteria | Antigravity |
| 08 | `08-SETUP-AND-ENV.md` | Repo layout, env vars, install and run | You |

## Locked decisions

- **Vectors live in MongoDB Atlas**, in a `chunks` collection queried with `$vectorSearch`. There is no separate vector database.
- **Embeddings via `fastembed` / `bge-small-en-v1.5`** (384-dim, local, ONNX). Not sentence-transformers — torch is 2 GB and will OOM a small instance.
- **Groq primary, Mistral fallback**, behind one wrapper. Nothing calls an LLM SDK directly.
- **The critic loop is capped at one revision.** Uncapped, it empties the daily quota in a single turn.

## Scope note

Everything here describes the **Basic Version (V1)** — the thing that must run on your laptop for the demo. Anything marked `[MVP+]` is deliberately out of scope for V1 and listed only so the architecture doesn't block it later.

## The one-line pitch

A single workspace where a team's chat, documents, and AI agents share one memory — so the agents answer from the team's own material instead of generic knowledge, and no one has to re-explain the project to a chatbot ever again.
