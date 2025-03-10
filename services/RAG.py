import os
import faiss
import numpy as np
import fitz  # PyMuPDF
import docx
import openai
from dotenv import load_dotenv

load_dotenv()

class RAG:
    def __init__(self, directory, oai_client, chunk_size=1000, overlap=25):
        self.directory = directory  # Directory to store the FAISS index and metadata
        self.index_path = os.path.join(directory, "vectorized_db.bin")
        self.meta_path = os.path.join(directory, "vectorized_db_meta.txt")
        self._client = oai_client  # OpenAI client instance
        self._docs = []
        self._index = None
        self.dimension = None
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        if os.path.exists(self.index_path):
            self._index = faiss.read_index(self.index_path)
            self.dimension = self._index.d  # Ensure correct dimensionality

        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("|", 1)
                    if len(parts) == 2:
                        self._docs.append({"path": parts[0], "text": parts[1]})

    def get_embedding(self, text):
        """Gets embedding for a given text using OpenAI's latest text-embedding model."""
        response = self._client.embeddings.create(
            input=[text],
            model="text-embedding-3-large"
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def extract_text_from_pdf(self, pdf_path):
        """Extracts text from a PDF file."""
        doc = fitz.open(pdf_path)
        return "\n".join([page.get_text() for page in doc])

    def extract_text_from_docx(self, docx_path):
        """Extracts text from a Word document."""
        doc = docx.Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def extract_text_from_txt(self, txt_path):
        """Extracts text from a TXT file."""
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def chunk_text(self, text):
        """Splits text into overlapping chunks for better retrieval."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.overlap  # Move forward with overlap
        return chunks

    def extract_text_from_files(self, file_paths):
        """Extracts text from files and chunks them into manageable pieces."""
        documents = []
        for file_path in file_paths:
            ext = file_path.lower().split('.')[-1]
            if ext == 'pdf':
                text = self.extract_text_from_pdf(file_path)
            elif ext == 'docx':
                text = self.extract_text_from_docx(file_path)
            elif ext == 'txt':
                text = self.extract_text_from_txt(file_path)
            else:
                print(f"Unsupported file type: {file_path}")
                continue

            chunks = self.chunk_text(text)
            for chunk in chunks:
                documents.append({"path": file_path, "text": chunk})

        return documents

    def create_faiss_index(self, file_paths):
        """Creates a FAISS index from the extracted text and saves it to the specified directory."""
        documents = self.extract_text_from_files(file_paths)
        if not documents:
            print("No valid documents found.")
            return

        embeddings = np.array([self.get_embedding(doc["text"]) for doc in documents], dtype=np.float32)
        dimension = embeddings.shape[1]
        self._index = faiss.IndexFlatL2(dimension)
        self._index.add(embeddings)
        self.dimension = dimension

        faiss.write_index(self._index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            for doc in documents:
                f.write(f"{doc['path']}|{doc['text'].replace('\n', ' ')}\n")

        print(f"FAISS index saved to {self.index_path}")

    def query(self, query: str, k: int = 1) -> str:
        """Queries FAISS and returns the most relevant document chunk."""
        embed = self.get_embedding(query).reshape(1, -1)
        if self.dimension is None:
            return "No Vectorized Database Found"
        if embed.shape[1] != self.dimension:
            return f"Embedding dimension mismatch: expected {self.dimension}, got {embed.shape[1]}"

        distances, indices = self._index.search(embed, k)

        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx != -1 and idx < len(self._docs):
                doc = self._docs[idx]
                results.append(f"{i+1}. Most Relevant Chunk:\n{doc['text']}\n")

        return "".join(results) if results else "No relevant documents found."
