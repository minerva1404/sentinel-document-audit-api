from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_or_404(
    document_id: int,
    current_user: User,
    db: Session,
) -> Document:
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Admins and auditors can read every document.
    # Editors and viewers can access only their own documents.
    if (
        current_user.role not in ("Admin", "Auditor")
        and document.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this document",
        )

    return document


def record_audit(
    db: Session,
    user_id: int,
    action: str,
    document_id: int,
    details: dict,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type="document",
            resource_id=document_id,
            details=details,
        )
    )


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("Admin", "Editor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins and Editors can create documents",
        )

    document = Document(
        title=request.title,
        content=request.content,
        owner_id=current_user.id,
    )

    try:
        db.add(document)
        db.flush()

        record_audit(
            db,
            current_user.id,
            "document.created",
            document.id,
            {"title": document.title, "owner_id": document.owner_id},
        )

        db.commit()
        db.refresh(document)
        return document
    except Exception:
        db.rollback()
        raise


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Document).order_by(Document.id)

    if current_user.role not in ("Admin", "Auditor"):
        query = query.where(Document.owner_id == current_user.id)

    return list(db.scalars(query).all())


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_document_or_404(document_id, current_user, db)


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    request: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("Admin", "Editor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins and Editors can update documents",
        )

    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if current_user.role != "Admin" and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editors can update only their own documents",
        )

    changes = request.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update",
        )

    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )
        setattr(document, field, value)

    try:
        db.flush()

        record_audit(
            db,
            current_user.id,
            "document.updated",
            document.id,
            {"changed_fields": list(changes.keys())},
        )

        db.commit()
        db.refresh(document)
        return document
    except Exception:
        db.rollback()
        raise


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("Admin", "Editor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins and Editors can delete documents",
        )

    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if current_user.role != "Admin" and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editors can delete only their own documents",
        )

    document_id = document.id
    title = document.title

    try:
        db.delete(document)

        record_audit(
            db,
            current_user.id,
            "document.deleted",
            document_id,
            {"title": title},
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=status.HTTP_204_NO_CONTENT)