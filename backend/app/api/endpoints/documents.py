import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.dms import Document, DocumentVersion
from backend.app.models.user import User
from backend.app.schemas.dms import DocumentRead, DocumentUpdate
from backend.app.services.audit_service import log_event

router = APIRouter()
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "documents")


def _load(db: Session, tid: int, did: int) -> Document:
    doc = db.query(Document).options(joinedload(Document.versions)).filter(
        Document.id == did, Document.tenant_id == tid
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def _save_file(file: UploadFile) -> tuple[str, int]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    safe = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, safe)
    data = file.file.read()
    with open(path, "wb") as f:
        f.write(data)
    return path, len(data)


@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    request: Request,
    title: str = Form(...),
    description: str | None = Form(None),
    category: str | None = Form(None),
    tags: str | None = Form(None),
    file: UploadFile = File(...),
    change_notes: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    """Upload a new document — creates v1."""
    path, size = _save_file(file)

    doc = Document(
        tenant_id=current_user.tenant_id,
        title=title, description=description,
        category=category, tags=tags,
        current_version=1, created_by=current_user.id,
    )
    db.add(doc); db.flush()

    ver = DocumentVersion(
        document_id=doc.id, version_number=1,
        filename=file.filename or "file", storage_path=path,
        file_size=size, mime_type=file.content_type,
        change_notes=change_notes, uploaded_by=current_user.id,
    )
    db.add(ver); db.commit()

    log_event(
        db, current_user, "CREATE", "document", doc.id,
        f"Uploaded document '{title}' v1",
        ip_address=request.client.host if request.client else None,
    )
    return _load(db, current_user.tenant_id, doc.id)


@router.post("/{did}/versions", response_model=DocumentRead)
def upload_new_version(
    did: int,
    request: Request,
    file: UploadFile = File(...),
    change_notes: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    """Upload a new version of an existing document."""
    doc = _load(db, current_user.tenant_id, did)
    path, size = _save_file(file)
    new_ver_num = doc.current_version + 1

    ver = DocumentVersion(
        document_id=doc.id, version_number=new_ver_num,
        filename=file.filename or "file", storage_path=path,
        file_size=size, mime_type=file.content_type,
        change_notes=change_notes, uploaded_by=current_user.id,
    )
    db.add(ver)
    doc.current_version = new_ver_num
    db.commit()

    log_event(
        db, current_user, "VERSION", "document", doc.id,
        f"Uploaded v{new_ver_num} of '{doc.title}'",
        ip_address=request.client.host if request.client else None,
    )
    return _load(db, current_user.tenant_id, doc.id)


@router.get("/", response_model=list[DocumentRead])
def list_documents(
    category: str | None = None,
    archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Document).options(joinedload(Document.versions)).filter(
        Document.tenant_id == current_user.tenant_id,
        Document.is_archived == archived,
    )
    if category:
        q = q.filter(Document.category == category)
    return q.order_by(Document.created_at.desc()).all()


@router.get("/{did}", response_model=DocumentRead)
def get_document(did: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return _load(db, current_user.tenant_id, did)


@router.get("/{did}/versions/{ver}/download")
def download_version(did: int, ver: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    doc = _load(db, current_user.tenant_id, did)
    version = next((v for v in doc.versions if v.version_number == ver), None)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    if not os.path.exists(version.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing on disk")
    return FileResponse(
        version.storage_path, filename=version.filename,
        media_type=version.mime_type or "application/octet-stream",
    )


@router.put("/{did}", response_model=DocumentRead)
def update_document(
    did: int, payload: DocumentUpdate, request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    doc = _load(db, current_user.tenant_id, did)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(doc, f, v)
    db.commit()
    log_event(db, current_user, "UPDATE", "document", doc.id,
              f"Updated metadata of '{doc.title}'",
              ip_address=request.client.host if request.client else None)
    return _load(db, current_user.tenant_id, did)


@router.delete("/{did}")
def delete_document(did: int, request: Request, db: Session = Depends(get_db),
                    current_user: User = Depends(require_write)):
    doc = _load(db, current_user.tenant_id, did)
    title = doc.title
    # Delete physical files
    for v in doc.versions:
        try:
            if v.storage_path and os.path.exists(v.storage_path):
                os.remove(v.storage_path)
        except Exception:
            pass
    db.delete(doc); db.commit()
    log_event(db, current_user, "DELETE", "document", did,
              f"Deleted document '{title}'",
              ip_address=request.client.host if request.client else None)
    return {"message": "Document deleted"}
