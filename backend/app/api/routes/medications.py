from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import ROLE_ADMIN, ROLE_NURSE, ROLE_PHARMACIST, CurrentUser, require_roles
from app.repositories import store
from app.schemas.medications import MedicationAdministrationCreate, MedicationDispenseCreate

router = APIRouter(prefix="/medications", tags=["medication administration"])


@router.post("/order-items/{order_item_id}/dispenses", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def dispense_medication(
    order_item_id: str,
    body: MedicationDispenseCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_PHARMACIST))],
) -> dict[str, Any]:
    row = store.dispense_medication(order_item_id, body.model_dump(exclude_none=True), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Medication order item is inactive or was not found")
    return row


@router.post("/order-items/{order_item_id}/administrations", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def administer_medication(
    order_item_id: str,
    body: MedicationAdministrationCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_NURSE))],
) -> dict[str, Any]:
    row = store.record_medication_administration(order_item_id, body.model_dump(exclude_none=True), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Medication order item, linked dispense, or active admission was not found")
    return row


@router.get("/order-items/{order_item_id}/administrations", response_model=list[dict[str, Any]])
def list_administrations(
    order_item_id: str,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_NURSE, ROLE_PHARMACIST))],
) -> list[dict[str, Any]]:
    return store.list_medication_administrations(order_item_id)
