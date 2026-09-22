"""
services/document_service.py
Handles document upload, indexing, and vector store lifecycle in Microsoft Foundry.
Supports PDF, DOCX, and TXT files for File Search RAG.
"""

import io
import os
import re
from typing import Any, Dict, Optional
from services.foundry_service import get_foundry_service


class DocumentService:
    """Manages document ingestion, vector store creation, and indexing in Foundry."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(self):
        self.foundry_service = get_foundry_service()

    def validate_file(self, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """Validates file existence, extension, and content size."""
        if not filename or not file_bytes:
            return {"valid": False, "error": "The uploaded file is empty or missing."}

        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return {
                "valid": False,
                "error": f"Unsupported file type '{ext}'. Supported formats: PDF, DOCX, TXT."
            }

        if len(file_bytes) == 0:
            return {"valid": False, "error": "The uploaded file contains 0 bytes."}

        if len(file_bytes) > 25 * 1024 * 1024:
            return {"valid": False, "error": "File exceeds the maximum upload limit of 25MB."}

        return {"valid": True, "error": None, "extension": ext}

    def process_and_index_document(self, uploaded_file) -> Dict[str, Any]:
        """
        Reads an uploaded file from Streamlit, creates a dedicated Vector Store
        in Microsoft Foundry, uploads the file, and polls until ingestion completes.
        
        Returns:
            Dict with vector_store_id, file_id, filename, status, and file_size.
        """
        filename = uploaded_file.name
        file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()

        validation = self.validate_file(filename, file_bytes)
        if not validation["valid"]:
            raise ValueError(validation["error"])

        openai_client = self.foundry_service.get_openai_client()

        # Sanitize store name (alphanumeric, dashes, underscores)
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.splitext(filename)[0])[:40]
        store_name = f"interview_vs_{safe_name}"

        # 1. Create a dedicated vector store
        vector_store = openai_client.vector_stores.create(
            name=store_name
        )
        vector_store_id = vector_store.id

        # 2. Prepare file stream for upload
        safe_filename = re.sub(r'[^\w\.-]', '_', filename)
        file_stream = io.BytesIO(file_bytes)
        file_stream.name = safe_filename

        # 3. Upload file to the vector store and wait for indexing
        vector_store_file = openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store_id,
            file=file_stream
        )

        if vector_store_file.status != "completed":
            error_details = getattr(vector_store_file, "last_error", None)
            raise RuntimeError(
                f"Document indexing failed with status '{vector_store_file.status}'. "
                f"Details: {error_details}"
            )

        return {
            "success": True,
            "filename": filename,
            "file_id": vector_store_file.id,
            "vector_store_id": vector_store_id,
            "status": vector_store_file.status,
            "file_size_kb": round(len(file_bytes) / 1024, 2)
        }

    def cleanup_vector_store(self, vector_store_id: Optional[str], file_id: Optional[str] = None):
        """
        Cleans up the temporary vector store and uploaded file to avoid clutter in Foundry.
        """
        if not vector_store_id:
            return

        openai_client = self.foundry_service.get_openai_client()
        try:
            if file_id:
                try:
                    openai_client.vector_stores.files.delete(
                        vector_store_id=vector_store_id,
                        file_id=file_id
                    )
                except Exception:
                    pass
                try:
                    openai_client.files.delete(file_id=file_id)
                except Exception:
                    pass

            openai_client.vector_stores.delete(vector_store_id=vector_store_id)
        except Exception:
            # Cleanup should be best-effort and never crash the UI
            pass


_doc_service_instance: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    global _doc_service_instance
    if _doc_service_instance is None:
        _doc_service_instance = DocumentService()
    return _doc_service_instance
