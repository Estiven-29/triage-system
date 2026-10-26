"""Login del personal medico y dependencia para proteger endpoints.

El intake del paciente (chatbot y clasificacion) queda abierto porque se usa
en el puesto de admision. El dashboard, las altas y el WebSocket exponen
datos de todos los pacientes, asi que exigen un token del personal.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..core.security import create_access_token, decode_access_token, verify_password
from ..db.database import get_db
from ..models.models import MedicalStaff
from ..schemas.schemas import LoginRequest, LoginResponse, StaffInfo

router = APIRouter(prefix="/api/auth", tags=["Autenticacion"])

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def staff_from_token(db: Session, token: str | None) -> MedicalStaff | None:
    staff_id = decode_access_token(token) if token else None
    return db.get(MedicalStaff, staff_id) if staff_id is not None else None


def require_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> MedicalStaff:
    if credentials is None:
        raise _unauthorized("Se requiere iniciar sesion")
    staff = staff_from_token(db, credentials.credentials)
    if staff is None:
        raise _unauthorized("Sesion invalida o expirada")
    return staff


def _staff_info(staff: MedicalStaff) -> StaffInfo:
    return StaffInfo(
        id=staff.id, employee_id=staff.employee_id, full_name=staff.full_name, role=staff.role
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    staff = db.query(MedicalStaff).filter(MedicalStaff.employee_id == payload.employee_id).first()
    # Mismo mensaje para usuario inexistente y contrasena incorrecta, para no
    # revelar que numeros de empleado existen.
    if staff is None or not verify_password(payload.password, staff.password_hash):
        raise _unauthorized("Numero de empleado o contrasena incorrectos")
    return LoginResponse(access_token=create_access_token(staff.id), staff=_staff_info(staff))


@router.get("/me", response_model=StaffInfo)
def me(staff: MedicalStaff = Depends(require_staff)):
    return _staff_info(staff)
