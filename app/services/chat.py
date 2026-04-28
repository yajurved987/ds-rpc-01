from uuid import uuid4
from app.rag_utils.rag_pipeline import run_rag_pipeline
from app.rag_utils.rag_memory import save_turn, get_history, clear_session


def create_session() -> str:
    return str(uuid4())


def chat(session_id: str, query: str, role: str) -> dict:
    
    history = get_history(session_id)

    enriched_query = query
    if history:
        history_text = "\n".join(
            f"{turn['role'].capitalize()}: {turn['content']}"
            for turn in history
        )
        enriched_query = f"Previous conversation:\n{history_text}\n\nUser: {query}"

    
    result = run_rag_pipeline(query=enriched_query, role=role)

    
    if not result["blocked"]:
        save_turn(session_id, query, result["answer"])

    return {
        "session_id":  session_id,
        "answer":      result["answer"],
        "sources":     result.get("sources", []),
        "blocked":     result["blocked"],
        "reason":      result.get("reason"),
        "token_usage": result.get("token_usage"),
    }


def reset_session(session_id: str) -> dict:
    clear_session(session_id)
    return {"session_id": session_id, "message": "Session cleared."}