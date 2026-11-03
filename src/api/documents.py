"""Document upload and listing for the web frontend."""
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf.errors import PdfReadError

from src.db.connection import connect_db
from src.rag.ingest import ingest_document

router = APIRouter()


@router.get("/documents")
def list_documents():
    try:
        with connect_db() as connection:
            rows = connection.execute(
                "SELECT d.id, d.filename, d.created_at, count(c.id) "
                "FROM documents d LEFT JOIN document_chunks c ON c.document_id=d.id "
                "GROUP BY d.id ORDER BY d.created_at DESC"
            ).fetchall()
        return [{"id": str(row[0]), "filename": row[1], "created_at": row[2].isoformat(),
                 "chunk_count": row[3]} for row in rows]
    except (psycopg.Error, ValueError):
        raise HTTPException(503, "Document storage is unavailable. Check database configuration.") from None


@router.post("/ingest")
def upload_document(file: UploadFile = File(...)):
    filename = Path((file.filename or "").replace("\\", "/")).name
    if Path(filename).suffix.lower() not in {".pdf", ".txt"}:
        raise HTTPException(422, "Choose a PDF or UTF-8 text file.")
    try:
        with TemporaryDirectory() as directory:
            path = Path(directory) / filename
            size = 0
            with path.open("wb") as target:
                while block := file.file.read(1024 * 1024):
                    size += len(block)
                    if size > 10 * 1024 * 1024:
                        raise HTTPException(413, "The maximum document size is 10 MB.")
                    target.write(block)
            if not size:
                raise HTTPException(422, "The document is empty.")
            document_id, count, created = ingest_document(path)
        return {"id": document_id, "filename": filename, "chunk_count": count, "created": created}
    except (ValueError, PdfReadError):
        raise HTTPException(422, "Could not read this document. Use an unlocked, text-based PDF or UTF-8 text file.") from None
    except psycopg.Error:
        raise HTTPException(503, "Document storage is unavailable. Check database setup.") from None
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from None
    except OSError:
        raise HTTPException(500, "Could not process the uploaded document.") from None
    finally:
        file.file.close()
