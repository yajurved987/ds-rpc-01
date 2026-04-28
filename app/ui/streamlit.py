import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


import streamlit as st

from app.services.chat import chat, create_session, reset_session
from app.rag_utils.rag_memory import get_history

st.set_page_config(page_title="RAG Assistant", layout="wide")


st.sidebar.title("Settings")

# session management
if "session_id" not in st.session_state:
    st.session_state.session_id = create_session()

st.sidebar.text_input(
    "Session ID",
    value=st.session_state.session_id,
    disabled=True,
    help="Unique ID for this conversation"
)

if st.sidebar.button("New Session"):
    st.session_state.session_id = create_session()
    st.rerun()

if st.sidebar.button("Clear History"):
    reset_session(st.session_state.session_id)
    st.rerun()

# role selection
st.session_state.role = st.sidebar.selectbox(
    "Your Role",
    options=["hr", "finance", "marketing", "c_level"],
    help="Your access level determines what data you can see"
)

st.title("🤖 Internal RAG Assistant")
st.subheader(f"Role: {st.session_state.role.upper()}")

# display conversation history
history = get_history(st.session_state.session_id)

if history:
    st.divider()
    st.write("**Conversation History**")
    for turn in history:
        if turn["role"] == "user":
            st.write(f"👤 **You:** {turn['content']}")
        else:
            st.write(f"🤖 **Assistant:** {turn['content']}")
    st.divider()
else:
    st.info("No conversation history yet. Start by asking a question.")

# input form
query = st.text_area(
    "Ask a question:",
    placeholder="e.g., What is the current headcount?",
    height=100
)

col1, col2 = st.columns(2)
with col1:
    send_button = st.button("Send", type="primary")
with col2:
    st.write("")


if send_button and query:
    with st.spinner("Thinking..."):
        result = chat(
            session_id=st.session_state.session_id,
            query=query,
            role=st.session_state.role
        )

    st.divider()

    if result["blocked"]:
        st.error(f"**Blocked** — {result['reason']}")
        st.write(result["answer"])
    else:
        st.success("✅ Success")
        st.write(result["answer"])

        # show sources and tokens
        col1, col2 = st.columns(2)
        with col1:
            if result["sources"]:
                st.write("**Sources:**")
                for source in result["sources"]:
                    st.write(f"  • {source}")
        with col2:
            if result["token_usage"]:
                st.write("**Token Usage:**")
                st.write(f"  • Input: {result['token_usage']['prompt_tokens']}")
                st.write(f"  • Output: {result['token_usage']['completion_tokens']}")
                st.write(f"  • Total: {result['token_usage']['total_tokens']}")

    st.rerun()

elif send_button:
    st.warning("Please enter a question.")

#streamlit run app/ui/streamlit.py