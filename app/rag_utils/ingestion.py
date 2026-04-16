from pathlib import Path
import os
import pandas as pd
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader



DATA_DIR = Path("../../resources/data")

#Function to load the data from the data folder

def load_data(file_path, role):
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".csv":
            df1 = pd.read_csv(file_path)
            documents = []
            for row in df1.to_dict(orient="records"):
                content = "\n".join(f"{key}:{value}" for key, value in row.items())
                documents.append(
                Document(
                page_content=content,
                metadata={
                    "role": role.lower(),
                    "source": Path(file_path).name
                })
                )
            return documents
        elif ext == ".md":
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                return [
                    Document(
                        page_content=content,
                        metadata={
                            "role": role.lower(),
                            "source": Path(file_path).name
                        }
                    )
                ]
        else: 
            return None
    
    except Exception as e:
        print(f"Failed to process {file_path}:{e}")
        return None
    
    

        
