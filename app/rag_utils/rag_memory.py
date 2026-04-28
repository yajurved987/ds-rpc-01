
from collections import defaultdict

# { session_id: [ {role, content}, ... ] }
store: dict[str, list[dict]] = defaultdict(list)


def save_turn(session_id: str, query: str, answer: str) -> None:
    store[session_id].append({"role": "user",      "content": query})
    store[session_id].append({"role": "assistant", "content": answer})


def get_history(session_id: str, last_n: int = 10) -> list[dict]:
    return store[session_id][-last_n:]


def clear_session(session_id: str) -> None:
    store[session_id] = []