"""Billing ledger APIs. Online payment confirmation must come from a verified provider webhook in a later integration."""

from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import ROLE_ADMIN, ROLE_BILLING_OFFICER, CurrentUser, require_roles
from app.repositories import store
from app.schemas.billing import InvoiceCreate, PaymentCreate

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/invoices", response_model=list[dict[str, Any]])
def list_invoices(user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_BILLING_OFFICER))]) -> list[dict[str, Any]]:
    return store.list_invoices()


@router.get("/payments", response_model=list[dict[str, Any]])
def list_payments(user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_BILLING_OFFICER))]) -> list[dict[str, Any]]:
    return store.list_payments()


@router.post("/invoices", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_invoice(body: InvoiceCreate, user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_BILLING_OFFICER))]) -> dict[str, Any]:
    row = store.create_invoice(body.model_dump(), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return row


@router.post("/payments", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def record_pending_payment(body: PaymentCreate, user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_BILLING_OFFICER))]) -> dict[str, Any]:
    row = store.record_pending_payment(body.model_dump(), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice is not open or was not found")
    return row


@router.post("/payments/{payment_id}/confirm", response_model=dict[str, Any])
def confirm_payment(payment_id: str, user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))]) -> dict[str, Any]:
    row = store.confirm_payment(payment_id, user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment is not pending or was not found")
    return row
