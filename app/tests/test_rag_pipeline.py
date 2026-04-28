

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from app.settings import settings
from app.rag_utils.rag_pipeline import run_rag_pipeline


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

#role validation

def test_role_validation():
    print("\n[ Guard 1 — Role Validation ]")

    result = run_rag_pipeline(query="what is the headcount?", role="intern")
    check("invalid role is blocked",        result["blocked"] is True)
    check("reason is invalid_role",         result["reason"] == "invalid_role")
    check("answer mentions valid roles",    "Valid roles" in result["answer"])

    for role in ["hr", "finance", "marketing", "c_level"]:
        result = run_rag_pipeline(query="test query", role=role)
        check(f"valid role passes — {role}", result["reason"] != "invalid_role")


#out of scope

def test_out_of_scope():
    print("\n[ Guard 2 — Out of Scope ]")

    oos_queries = [
        "what is the bitcoin price?",
        "give me investment advice",
        "who should i vote for?",
        "how do i hack the system?",
        "give me medical advice",
    ]

    for query in oos_queries:
        result = run_rag_pipeline(query=query, role="hr")
        check(f"blocked — '{query[:30]}...'", result["blocked"] is True)
        check(f"reason is out_of_scope",      result["reason"] == "out_of_scope")


#no context 

def test_empty_context():
    print("\n[ Guard 3 — Empty Context ]")

   
    result = run_rag_pipeline(
        query="zxqy random gibberish that matches nothing",
        role="hr"
    )
    check("not blocked by role or scope",   result["reason"] not in ("invalid_role", "out_of_scope"))
    check("reason is no_context",           result["reason"] == "no_context")
    check("answer is not empty",            result["answer"] != "")




def test_happy_path():
    print("\n[ Happy Path — Real Retrieval + Groq ]")

    result = run_rag_pipeline(query="what is the headcount?", role="hr")

    print(f"     answer   : {result['answer'][:80]}...")
    print(f"     sources  : {result['sources']}")
    print(f"     usage    : {result['token_usage']}")

    check("not blocked",                result["blocked"] is False)
    check("has answer",                 len(result["answer"]) > 0)
    check("token usage returned",       result["token_usage"] is not None)
    check("prompt_tokens > 0",          result["token_usage"]["prompt_tokens"] > 0)
    check("completion_tokens > 0",      result["token_usage"]["completion_tokens"] > 0)


#PII Redaction

def test_pii_redaction():
    print("\n[ Guard 4 — PII Redaction ]")

    
    from app.rag_utils.rag_pipeline import redact_pii

    ssn_text   = "Employee SSN is 123-45-6789."
    email_text = "Contact john.doe@company.com for info."
    clean_text = "The Q3 budget is $500,000."

    check("SSN redacted",           "123-45-6789"          not in redact_pii(ssn_text))
    check("[REDACTED] in SSN",      "[REDACTED]"           in     redact_pii(ssn_text))
    check("email redacted",         "john.doe@company.com" not in redact_pii(email_text))
    check("[REDACTED] in email",    "[REDACTED]"           in     redact_pii(email_text))
    check("clean text untouched",   "[REDACTED]"           not in redact_pii(clean_text))



def main():
  
    print("  RAG PIPELINE TEST")
   
    test_role_validation()
    test_out_of_scope()
    test_empty_context()
    test_pii_redaction()
  #  test_happy_path()       



    print(f"  Results: {passed} passed, {failed} failed")
  


if __name__ == "__main__":
    main()



#(ds-rpc-01) E:\Portfolio\RAG_BASED_ASSISTANT\ds-rpc-01>python -m app.tests.test_rag_pipeline