"""Medicine CRUD (per-user). Mirrors the Flutter add/list/detail/delete flow."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..alerts import doses_per_day, generate_alerts_for_medicine
from ..database import get_db
from ..deps import get_current_user
from ..models import Medicine, User
from ..schemas import MedicineCreate, MedicineOut

router = APIRouter(prefix="/api/medicines", tags=["medicines"])


def _to_out(m: Medicine) -> MedicineOut:
    out = MedicineOut.model_validate(m)
    out.doses_per_day = doses_per_day(m.interval_hours)
    return out


@router.get("", response_model=list[MedicineOut])
def list_medicines(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Medicine).filter(Medicine.user_id == user.id).order_by(Medicine.created_at).all()
    return [_to_out(m) for m in rows]


@router.post("", response_model=MedicineOut, status_code=status.HTTP_201_CREATED)
def create_medicine(
    payload: MedicineCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Duplicate-name check per user (matches EntryError.NameDuplicate rule).
    exists = (
        db.query(Medicine)
        .filter(Medicine.user_id == user.id, Medicine.name == payload.name)
        .first()
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Medicine name already exists")
    medicine = Medicine(
        user_id=user.id,
        name=payload.name,
        dosage=payload.dosage,
        medicine_type=payload.medicine_type,
        interval_hours=payload.interval_hours,
        start_time=payload.start_time,
    )
    db.add(medicine)
    db.flush()
    generate_alerts_for_medicine(db, medicine)
    db.commit()
    db.refresh(medicine)
    return _to_out(medicine)


@router.get("/{medicine_id}", response_model=MedicineOut)
def get_medicine(
    medicine_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = db.get(Medicine, medicine_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medicine not found")
    return _to_out(m)


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(
    medicine_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = db.get(Medicine, medicine_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medicine not found")
    db.delete(m)  # cascades to alerts
    db.commit()
    return None
