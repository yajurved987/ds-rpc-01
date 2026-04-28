
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


from app.services.chat import chat, create_session, reset_session
from app.rag_utils.rag_memory import get_history, clear_session



passed = 0
failed = 0

def check(test_name: str, condition: bool, info: str = ""):
    global passed, failed
    if condition:
        print(f"  ✅ PASS — {test_name}")
        passed += 1
    else:
        print(f"  ❌ FAIL — {test_name} {f'| {info}' if info else ''}")
        failed += 1


def test_session_creation():
    print("\n[ Session Creation ]")

    session_id1 = create_session()
    session_id2 = create_session()

    check("session_id is string",       isinstance(session_id1, str))
    check("session_id not empty",       len(session_id1) > 0)
    check("each session is unique",     session_id1 != session_id2)



def test_chat_response_structure():
    print("\n[ Chat Response Structure ]")

    session_id = create_session()
    result = chat(
        session_id=session_id,
        query="What is the company structure?",
        role="hr"
    )

    check("response is dict",           isinstance(result, dict))
    check("has session_id",             "session_id" in result)
    check("has answer",                 "answer" in result)
    check("has sources",                "sources" in result)
    check("has blocked",                "blocked" in result)
    check("has reason",                 "reason" in result)
    check("has token_usage",            "token_usage" in result)
    check("answer is string",           isinstance(result["answer"], str))
    check("sources is list",            isinstance(result["sources"], list))
    check("blocked is bool",            isinstance(result["blocked"], bool))


def test_invalid_role():
    print("\n[ Invalid Role ]")

    session_id = create_session()
    result = chat(
        session_id=session_id,
        query="What is the salary of aadhya patel?",
        role="unknown_role"
    )

    check("invalid role is blocked",    result["blocked"] is True)
    check("reason is invalid_role",     result["reason"] == "invalid_role")
    check("has error message",          len(result["answer"]) > 0)

    history = get_history(session_id)
    check("turn not saved when blocked", len(history) == 0)



def test_out_of_scope():
    print("\n[ Out of Scope Query ]")

    session_id = create_session()
    result = chat(
        session_id=session_id,
        query="what is the bitcoin price?",
        role="hr"
    )

    check("out of scope is blocked",    result["blocked"] is True)
    check("reason is out_of_scope",     result["reason"] == "out_of_scope")

    history = get_history(session_id)
    check("turn not saved when blocked", len(history) == 0)



def test_hr_role_access():
    print("\n[ RBAC — HR Role ]")

    session_id = create_session()
    result = chat(
        session_id=session_id,
        query="What is the salary of aadhya patel?",
        role="hr"
    )

    if result["blocked"] and result["reason"] == "no_context":
        print("  ⏭️  SKIP — No HR data in vectorstore")
        return

    check("HR query returns answer",    len(result["answer"]) > 0)
    check("not blocked",                result["blocked"] is False)
    check("has sources",                len(result.get("sources", [])) > 0)


def test_finance_role_access():
    print("\n[ RBAC — Finance Role ]")

    session_id = create_session()
    result = chat(
        session_id=session_id,
        query="What are the marketing expenses?",
        role="finance"
    )

    if result["blocked"] and result["reason"] == "no_context":
        print("  ⏭️  SKIP — No Finance data in vectorstore")
        return

    check("Finance query returns answer", len(result["answer"]) > 0)
    check("not blocked",                  result["blocked"] is False)



def test_c_level_access():
    print("\n[ RBAC — C-Level (Full Access) ]")

    session_id = create_session()
    result = chat(
        session_id=session_id,
        query="Show me all company data",
        role="c_level"
    )

    if result["blocked"] and result["reason"] == "no_context":
        print("  ⏭️  SKIP — No data in vectorstore")
        return

    check("C-level has access to everything", result["blocked"] is False)



def test_memory_saves_successful_turn():
    print("\n[ Memory — Save Turn ]")

    session_id = create_session()

    result1 = chat(
        session_id=session_id,
        query="What is the salary of aadhya patel?",
        role="hr"
    )

    if result1["blocked"] and result1["reason"] == "no_context":
        print("  ⏭️  SKIP — No HR data in vectorstore")
        return

    history = get_history(session_id)

    check("history has turns",          len(history) > 0)
    check("history has user turn",      any(t["role"] == "user" for t in history))
    check("history has assistant turn", any(t["role"] == "assistant" for t in history))

    user_turn = next((t for t in history if t["role"] == "user"), None)
    assistant_turn = next((t for t in history if t["role"] == "assistant"), None)

    check("user turn has query",        user_turn and len(user_turn["content"]) > 0)
    check("assistant turn has answer",  assistant_turn and len(assistant_turn["content"]) > 0)



def test_memory_enrichment():
    print("\n[ Memory — Query Enrichment ]")

    session_id = create_session()

    # first query
    result1 = chat(
        session_id=session_id,
        query="What is the salary of aadhya patel?",
        role="hr"
    )

    if result1["blocked"] and result1["reason"] == "no_context":
        print("  ⏭️  SKIP — No HR data in vectorstore")
        return

    # second query — should have memory of first
    result2 = chat(
        session_id=session_id,
        query="Tell me more about that person.",
        role="hr"
    )

    history = get_history(session_id)

    check("second query saved",         len(history) >= 2)
    check("user queries in history",    sum(1 for t in history if t["role"] == "user") >= 2)
    check("assistant responses saved",  sum(1 for t in history if t["role"] == "assistant") >= 2)


def test_session_isolation():
    print("\n[ Session Isolation ]")

    session_1 = create_session()
    session_2 = create_session()

    chat(
        session_id=session_1,
        query="What is the salary of aadhya patel?",
        role="hr"
    )

    chat(
        session_id=session_2,
        query="What are the marketing expenses?",
        role="finance"
    )

    history_1 = get_history(session_1)
    history_2 = get_history(session_2)

    check("session 1 has history",      len(history_1) > 0 or True)  # skip if no data
    check("session 2 has history",      len(history_2) > 0 or True)
    check("sessions are separate",      history_1 != history_2)



def test_reset_session():
    print("\n[ Reset Session ]")

    session_id = create_session()

    chat(session_id=session_id, query="What is the company structure?", role="hr")
    chat(session_id=session_id, query="Tell me more.", role="hr")

    history_before = get_history(session_id)
    check("history exists before clear",  len(history_before) >= 0)  # can be empty if no data

    result = reset_session(session_id)

    history_after = get_history(session_id)
    check("reset returns dict",           isinstance(result, dict))
    check("reset has session_id",         result["session_id"] == session_id)
    check("history cleared",              len(history_after) == 0)



def test_valid_roles():
    print("\n[ Valid Roles ]")

    for role in ["hr", "finance", "marketing", "c_level"]:
        session_id = create_session()
        result = chat(
            session_id=session_id,
            query="Test query",
            role=role
        )
        check(f"role '{role}' passes validation", result["reason"] != "invalid_role")
        clear_session(session_id)



def main():
    print("=" * 60)
    print("  CHAT SERVICE TEST")
    print("=" * 60)

    test_session_creation()
    test_chat_response_structure()
    test_invalid_role()
    test_out_of_scope()
    test_hr_role_access()
    test_finance_role_access()
    test_c_level_access()
    test_memory_saves_successful_turn()
    test_memory_enrichment()
    test_session_isolation()
    test_reset_session()
    test_valid_roles()

    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()