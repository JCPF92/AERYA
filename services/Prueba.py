from RAG import RAG
import os
import openai

client = openai.OpenAI(api_key= os.getenv("OPENAI_API_KEY"))

# Example usage:
file_list = ["Avior_Politica_Cancelacion_Reservacion.pdf",
            "Avior_Airlines_Info.txt",
            "OTA_API_Documentation (1).docx"]
rag = RAG("./services/faiss_storage", client)

rag.create_faiss_index(file_list)

rag = RAG("./services/faiss_storage", client)
print(rag.query("What is the policy for canceling a reservation?", 1)   )

