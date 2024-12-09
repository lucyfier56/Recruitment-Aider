import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStoreManager:
    def __init__(self, embedding_model="all-MiniLM-L6-v2", storage_dir=None):
        """
        Initialize vector store using FAISS and SentenceTransformers
        
        Args:
            embedding_model (str): Embedding model to use
            storage_dir (str, optional): Directory to store document chunks
        """
        self.model = SentenceTransformer(embedding_model)
        self.documents = []
        self.document_ids = []
        self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
        
        # Set default storage directory if not provided
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'document_chunks')
        
        # Create storage directory if it doesn't exist
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        print(f"Saving documents to: {self.storage_dir}")
    
    def add_document(self, doc_id, text, metadata=None):
        """
        Add a document to the vector store and save its chunk locally
        
        Args:
            doc_id (str): Unique identifier for the document
            text (str): Document text
            metadata (dict, optional): Additional document metadata
        """
        try:
            # Sanitize doc_id to create a valid filename
            safe_doc_id = "".join(x for x in doc_id if x.isalnum() or x in "._- ").rstrip()
            if not safe_doc_id:
                safe_doc_id = "unnamed_document"
            
            # Generate embedding
            embedding = self.model.encode([text])[0]
            
            # Convert to numpy float32
            embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
            
            # Add to FAISS index
            self.index.add(embedding)
            
            # Store document details
            self.documents.append(text)
            self.document_ids.append(doc_id)
            
            # Prepare full file paths
            chunk_filename = os.path.join(self.storage_dir, f"{safe_doc_id}.txt")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(chunk_filename), exist_ok=True)
            
            # Save document chunk
            with open(chunk_filename, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Verify file was written
            if os.path.exists(chunk_filename):
                print(f"Document saved successfully: {chunk_filename}")
            else:
                print(f"Failed to save document: {chunk_filename}")
            
            # Optional: Save metadata if provided
            if metadata:
                import json
                metadata_filename = os.path.join(self.storage_dir, f"{safe_doc_id}_metadata.json")
                with open(metadata_filename, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        except Exception as e:
            print(f"Error adding document: {e}")
            import traceback
            traceback.print_exc()

    def list_saved_documents(self):
        """
        List all saved document chunks
        
        Returns:
            List of saved document filenames
        """
        return [f for f in os.listdir(self.storage_dir) if f.endswith('.txt')]