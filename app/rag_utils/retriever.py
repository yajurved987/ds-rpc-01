from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.settings import settings


def get_vectorstore():
    embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL_NAME)

    return Chroma(
        persist_directory=settings.VECTORSTORE_DIR,
        embedding_function=embeddings
    )


def build_filter(role: str):
    """
    Role-based filter. Users see:
    - Their own role documents
    - 'general' or 'shared' documents (accessible to all)
    
    c_level bypasses filter (sees everything)
    """
    if role == "c_level":
        return None  # no filter — see everything

    return {
        "$or": [
            {"role": role},
            {"role": "general"},
            {"role": "shared"},
        ]
    }



def retrieve_docs(query: str, role: str, top_k: int = 5):
    vectordb = get_vectorstore()
    search_kwargs = {"k": top_k}

    role_filter = build_filter(role)
    if role_filter:
        search_kwargs["filter"] = role_filter

    retriever = vectordb.as_retriever(search_kwargs=search_kwargs)

    docs = retriever.invoke(query)
    return docs