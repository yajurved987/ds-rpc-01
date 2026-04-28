# app/tests/test_ingestion.py
# app/tests/test_ingestion.py

from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.rag_utils.ingestion import load_data, get_embeddings_model, split_documents
from app.rag_utils.vector_store import create_vectorstore


DATA_DIR = Path("resources/data")

ROLE_MAP = {
    "hr":        "hr",
    "finance":   "finance",
    "marketing": "marketing",
    "executive": "c_level",
    "general":   "general",
}


def main():
    print("=" * 60)
    print("  RAG INGESTION")
    print("=" * 60)
    
    all_documents = []
    role_count = {}
    
    for folder in DATA_DIR.iterdir():
        if folder.is_dir():
            folder_name = folder.name.lower()
            
            # get role from folder name
            role = ROLE_MAP.get(folder_name, "general")
            
            print(f"\n[ {folder_name.upper()} ] → role: {role}")
            
            for file in folder.iterdir():
                if file.is_file():
                    print(f"  • {file.name}")
                    documents = load_data(file, role)
                    if documents:
                        all_documents.extend(documents)
                        role_count[role] = role_count.get(role, 0) + len(documents)

    print(f"\n" + "=" * 60)
    print(f"  TOTAL: {len(all_documents)} documents loaded")
    print(f"=" * 60)
    
    print("\nDocuments by role:")
    for role, count in role_count.items():
        print(f"  • {role:12s}: {count} docs")

    # split documents
    print(f"\n[ Splitting documents ]")
    split_docs = split_documents(all_documents)
    print(f"  Chunks created: {len(split_docs)}")

    # embed and store
    print(f"\n[ Embedding & storing ]")
    embeddings = get_embeddings_model()
    create_vectorstore(split_docs, embeddings)
    print(f"Vectorstore updated")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()




# E:\Portfolio\RAG_BASED_ASSISTANT\ds-rpc-01>python -m app.tests.test_ingestion