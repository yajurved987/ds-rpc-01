
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from groq import Groq
import re

from app.rag_utils.retriever import retrieve_docs
from app.settings import settings

#State Schema
class RAGState(TypedDict):
    query:      str
    role:       str
    docs:       list
    context:    str
    sources:    list[str]
    answer:     str
    blocked:    bool
    reason:     Optional[str]  # invalid_role, out_of_scope, no_context, llm_error, None


VALID_ROLES = {"hr", "finance", "marketing", "c_level"}

OUT_OF_SCOPE_KEYWORDS = [
    "stock price", "invest", "crypto", "bitcoin",
    "personal advice", "legal advice", "medical",
    "competitor secret", "hack", "password",
    "who should i vote", "politics",
]

PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",                                        # SSN
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",         # Email
    r"\b(?:\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b",  # Phone
    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b",            # Credit card
    r"\b\d{9}\b",                                                     # 9-digit IDs
]

SYSTEM_PROMPT = """
You are a secure internal company assistant.
Answer ONLY using the provided context.
If the answer is not in the context, say: "I don't have enough information to answer that."

Rules:
- Never reveal raw employee IDs, SSNs, or account numbers.
- Do not speculate beyond the given context.
- Be concise and professional.
"""

def call_groq(system_prompt: str, user_message: str) -> tuple[str, dict]:
    """Direct Groq API call. Returns (answer, token_usage)."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    response = client.chat.completions.create(
        model=settings.CHAT_MODEL_NAME,
        temperature=settings.CHAT_MODEL_TEMPERATURE,
        max_tokens=settings.CHAT_MODEL_MAX_TOKENS,
        top_p=settings.CHAT_MODEL_TOP_P,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )

    usage = {
        "prompt_tokens":     response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens":      response.usage.total_tokens,
    }

    return response.choices[0].message.content, usage

def redact_pii(text: str) -> str:
    """Replace any PII found in text with [REDACTED]."""
    for pattern in PII_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text



def node_validate(state: RAGState) -> RAGState:
    """
    Guard 1 — Reject unknown roles.
    Guard 2 — Reject out-of-scope questions.
    """
    role  = state["role"].lower()
    query = state["query"].lower()

    if role not in VALID_ROLES:
        return {
            **state,
            "blocked": True,
            "reason":  "invalid_role",
            "answer":  f"Unknown role '{state['role']}'. Valid roles: {', '.join(VALID_ROLES)}.",
        }

    for keyword in OUT_OF_SCOPE_KEYWORDS:
        if keyword in query:
            return {
                **state,
                "blocked": True,
                "reason":  "out_of_scope",
                "answer":  "This question is outside the scope of the internal knowledge base.",
            }

    return {**state, "blocked": False, "reason": None}


def node_retrieve(state: RAGState) -> RAGState:
    """
    RBAC-aware retrieval.
    Chroma filters docs by role metadata. c_level bypasses the filter (handled in retriever).
    """
    docs = retrieve_docs(
        query=state["query"],
        role=state["role"].lower(),
        top_k=5,
    )
    return {**state, "docs": docs}


def node_check_context(state: RAGState) -> RAGState:
    """Guard 3 — Block if no relevant documents were retrieved."""
    if not state["docs"]:
        return {
            **state,
            "blocked": True,
            "reason":  "no_context",
            "answer":  "I couldn't find relevant information. Please rephrase or contact your admin.",
        }
    return {**state, "blocked": False}


def node_generate(state: RAGState) -> RAGState:
    """Build context from retrieved docs and call Groq."""
    context = "\n\n".join(doc.page_content for doc in state["docs"])
    sources = list({doc.metadata.get("source", "unknown") for doc in state["docs"]})

    user_message = f"Context:\n{context}\n\nQuestion: {state['query']}"

    try:
        answer, usage = call_groq(SYSTEM_PROMPT, user_message)
        return {
            **state,
            "context": context,
            "sources": sources,
            "answer":  answer,
            "blocked": False,
            "reason":  None,
            "token_usage": usage,
        }
    except Exception as e:
        return {
            **state,
            "context": context,
            "sources": sources,
            "blocked": False,
            "reason":  f"llm_error: {str(e)}",
            "answer":  "An error occurred while generating a response.",
        }


def node_redact(state: RAGState) -> RAGState:
    """Guard 4 — Scrub PII from the final answer before it reaches the user."""
    return {**state, "answer": redact_pii(state["answer"])}


def node_blocked_response(state: RAGState) -> RAGState:
    """Terminal node for all blocked paths. Answer already set upstream."""
    return state




def route_after_validate(state: RAGState) -> str:
    return "blocked_response" if state["blocked"] else "retrieve"


def route_after_context_check(state: RAGState) -> str:
    return "blocked_response" if state["blocked"] else "generate"




def build_rag_graph():
    graph = StateGraph(RAGState)

   
    graph.add_node("validate",         node_validate)
    graph.add_node("retrieve",         node_retrieve)
    graph.add_node("check_context",    node_check_context)
    graph.add_node("generate",         node_generate)
    graph.add_node("redact",           node_redact)
    graph.add_node("blocked_response", node_blocked_response)

    graph.set_entry_point("validate")

    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "blocked_response": "blocked_response", 
            "retrieve":         "retrieve",
        }
    )
    graph.add_edge("retrieve", "check_context")
    graph.add_conditional_edges(
        "check_context",
        route_after_context_check,
        {
            "blocked_response": "blocked_response",
            "generate":         "generate",
        }
    )
    graph.add_edge("generate",         "redact")
    graph.add_edge("redact",           END)
    graph.add_edge("blocked_response", END)

    return graph.compile()


rag_graph = build_rag_graph()



def run_rag_pipeline(query: str, role: str) -> dict:
    """
    Called by services/chat.py or main.py.

    Returns:
        {
            "answer":      str,
            "sources":     list[str],
            "blocked":     bool,
            "reason":      str | None,
            "token_usage": dict | None
        }
    """
    initial_state: RAGState = {
        "query":       query,
        "role":        role,
        "docs":        [],
        "context":     "",
        "sources":     [],
        "answer":      "",
        "blocked":     False,
        "reason":      None,
        "token_usage": None,
    }

    final_state = rag_graph.invoke(initial_state)

    return {
        "answer":      final_state["answer"],
        "sources":     final_state.get("sources", []),
        "blocked":     final_state["blocked"],
        "reason":      final_state.get("reason"),
        "token_usage": final_state.get("token_usage"),
    }