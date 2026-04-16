from app.rag_utils.ingestion import load_data
from pathlib import Path


DATA_DIR = Path("resources/data")
def main():
    print("Starting RAG Ingestion Process")
    
    all_documents=[]
    for folder in DATA_DIR.iterdir():
        if folder.is_dir():
            for file in folder.iterdir():
                print("processing file:", file)
                documents= load_data(file, "user")
                if documents:
                    all_documents.extend(documents)

    print(f"Loaded {len(all_documents)} documents")
    for doc in all_documents:
        print(doc.metadata)



if __name__ == "__main__":
    main()
    

# E:\Portfolio\RAG_BASED_ASSISTANT\ds-rpc-01>python -m app.tests.test_ingestion