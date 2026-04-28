# DS RPC-01: Internal RAG Chatbot with Role-Based Access Control

A secure, production-ready internal chatbot that answers questions using company data with fine-grained role-based access control (RBAC).

---

## 📋 Project Overview

This project implements an internal company chatbot built on LangGraph that:
- ✅ Answers questions using company private data (RAG)
- ✅ Enforces role-based access control (RBAC)
- ✅ Maintains conversation history per session
- ✅ Includes guardrails to block sensitive queries
- ✅ Redacts PII from responses
- ✅ Tracks token usage for cost monitoring

### Supported Roles

| Role | Access |
|------|--------|
| `hr` | HR data + general docs |
| `finance` | Finance data + general docs |
| `marketing` | Marketing data + general docs |
| `c_level` | All company data (unrestricted) |
| `general` | General docs only |

---

## 🏗️ Architecture
User Request
│
▼
Streamlit UI
│
▼
services/chat.py ──────────── orchestrates pipeline + memory
│
├─→ rag_memory.py ──── retrieves conversation history
│
└─→ rag_pipeline.py (LangGraph) ──── guards + retrieval + LLM
│
├─→ node_validate    ──── role check + out-of-scope detection
│
├─→ node_retrieve    ──── RBAC-filtered doc retrieval
│
├─→ node_check_context ──── validates docs found
│
├─→ node_generate    ──── Groq API call
│
└─→ node_redact      ──── PII redaction

---

## ✨ Features Implemented

### 1. **RAG Pipeline (LangGraph)**
- State machine with 6 nodes for clean, inspectable flow
- Typed state (`RAGState`) for type safety
- Conditional routing based on guardrail checks

### 2. **Guardrails**
| Guard | Blocks | Example |
|-------|--------|---------|
| Role Validation | Invalid roles | `role="intern"` |
| Out-of-Scope | Unrelated queries | "bitcoin price", "hack the system" |
| Empty Context | No matching docs | Generic queries with no company data |
| PII Redaction | Sensitive data in output | SSN, email, credit card, employee IDs |

### 3. **Role-Based Access Control (RBAC)**
- Documents ingested with role metadata
- Retriever filters by role + general docs
- C-level bypass (sees all data)
- Works via Chroma metadata filters

### 4. **Memory System**
- Per-session conversation history (UUID-based)
- Enriches queries with past turns
- Supports multi-turn conversations
- Simple in-memory store (swappable for Redis/DB)

### 5. **User Interface**
- Streamlit web app with role selector
- Session management (New/Clear buttons)
- Conversation history display
- Token usage & sources shown
- Blocked query feedback

### 6. **Testing**
All test files use plain Python (no pytest/mock):
- `test_ingestion.py` — data loading by role
- `test_rag_pipeline.py` — guards + generation
- `test_chat_service.py` — RBAC + memory

---

---

## 🛡️ Guardrails in Action

### Guard 1: Role Validation
```python
if role not in VALID_ROLES:
    return "Unknown role 'intern'. Valid roles: hr, finance, ..."
```

### Guard 2: Out-of-Scope Detection
```python
OUT_OF_SCOPE_KEYWORDS = [
    "bitcoin", "invest", "hack", "password", ...
]
```

### Guard 3: Context Relevance
```python
if no documents retrieved:
    return "I couldn't find relevant information..."
```

### Guard 4: PII Redaction
```python
Redacts: SSN (123-45-6789), Email, Phone, Credit Cards, Employee IDs
```

---

