from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import ROLE_ADMIN, ROLE_DOCTOR, ROLE_LAB_SCIENTIST, ROLE_NURSE, ROLE_PHARMACIST, CurrentUser, require_roles
from app.repositories import store
from app.schemas.orders import ClinicalOrderCreate, OrderItemResultCreate, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["clinical orders"])
ORDER_FULFILMENT_ROLES = (ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, ROLE_PHARMACIST, ROLE_LAB_SCIENTIST)


@router.get("/patient/{patient_id}", response_model=list[dict[str, Any]])
def list_patient_orders(
    patient_id: str,
    _user: Annotated[CurrentUser, Depends(require_roles(*ORDER_FULFILMENT_ROLES))],
) -> list[dict[str, Any]]:
    return store.list_clinical_orders(patient_id)


@router.get("/worklist/{order_type}", response_model=list[dict[str, Any]])
def order_worklist(
    order_type: str,
    _user: Annotated[CurrentUser, Depends(require_roles(*ORDER_FULFILMENT_ROLES))],
) -> list[dict[str, Any]]:
    if order_type not in {"laboratory", "imaging", "procedure", "medication"}:
        raise HTTPException(status_code=422, detail="Unsupported order type")
    return store.list_order_worklist(order_type)


@router.post("", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_order(
    body: ClinicalOrderCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR))],
) -> dict[str, Any]:
    row = store.create_clinical_order(body.model_dump(), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient or encounter was not found")
    return row


@router.patch("/{order_id}/status", response_model=dict[str, Any])
def update_order_status(
    order_id: str,
    body: OrderStatusUpdate,
    user: Annotated[CurrentUser, Depends(require_roles(*ORDER_FULFILMENT_ROLES))],
) -> dict[str, Any]:
    row = store.update_clinical_order_status(order_id, body.model_dump(exclude_none=True), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is not active or was not found")
    return row


@router.post("/items/{item_id}/result", response_model=dict[str, Any])
def record_item_result(
    item_id: str,
    body: OrderItemResultCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_LAB_SCIENTIST))],
) -> dict[str, Any]:
    row = store.record_order_item_result(item_id, body.model_dump(exclude_none=True), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order item is inactive or was not found")
    return row
