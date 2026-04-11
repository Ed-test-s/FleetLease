from datetime import date, datetime

from pydantic import BaseModel

from app.models.leasing import (
    ContractStatus,
    PaymentScheduleStatus,
    PaymentStatus,
    PurchaseContractStatus,
    RequestStatus,
)


# ── Request ───────────────────────────────────────────────────────────
class LeaseRequestCreate(BaseModel):
    lease_company_id: int
    vehicle_id: int
    lease_term: int
    prepayment: float
    comment: str | None = None


class LeaseRequestOut(BaseModel):
    id: int
    user_id: int
    lease_company_id: int
    vehicle_id: int
    lease_term: int
    prepayment: float
    comment: str | None = None
    status: RequestStatus
    created_at: datetime
    model_config = {"from_attributes": True}


class LeaseRequestStatusUpdate(BaseModel):
    status: RequestStatus


# ── Contract ──────────────────────────────────────────────────────────
class ContractCreate(BaseModel):
    request_id: int
    lessee_id: int
    lessor_id: int
    supplier_id: int | None = None
    vehicle_id: int
    contract_number: str
    start_date: date | None = None
    end_date: date | None = None
    total_amount: float
    prepayment: float
    interest_rate: float


class ContractOut(BaseModel):
    id: int
    request_id: int
    lessee_id: int
    lessor_id: int
    supplier_id: int | None = None
    vehicle_id: int
    contract_number: str
    start_date: date | None = None
    end_date: date | None = None
    total_amount: float
    prepayment: float
    interest_rate: float
    status: ContractStatus
    created_at: datetime
    model_config = {"from_attributes": True}


class ContractStatusUpdate(BaseModel):
    status: ContractStatus


# ── Payment Schedule ──────────────────────────────────────────────────
class PaymentScheduleCreate(BaseModel):
    contract_id: int
    payment_date: date
    total_amount: float
    principal_amount: float
    interest_amount: float
    vat_amount: float = 0.0
    remaining_debt: float


class PaymentScheduleOut(BaseModel):
    id: int
    contract_id: int
    payment_date: date
    total_amount: float
    principal_amount: float
    interest_amount: float
    vat_amount: float
    remaining_debt: float
    status: PaymentScheduleStatus
    model_config = {"from_attributes": True}


# ── Payment ───────────────────────────────────────────────────────────
class PaymentCreate(BaseModel):
    contract_id: int
    payment_schedule_id: int | None = None
    amount: float
    payment_method: str | None = None


class PaymentOut(BaseModel):
    id: int
    contract_id: int
    payment_schedule_id: int | None = None
    amount: float
    payment_date: date
    payment_method: str | None = None
    status: PaymentStatus
    model_config = {"from_attributes": True}


# ── Purchase Contract ─────────────────────────────────────────────────
class PurchaseContractCreate(BaseModel):
    contract_id: int
    supplier_id: int
    vehicle_id: int
    purchase_price: float


class PurchaseContractOut(BaseModel):
    id: int
    contract_id: int
    supplier_id: int
    vehicle_id: int
    purchase_price: float
    purchase_date: date | None = None
    status: PurchaseContractStatus
    model_config = {"from_attributes": True}


# ── Calculator ────────────────────────────────────────────────────────
class CalculatorRequest(BaseModel):
    asset_price: float
    prepayment: float
    term_months: int
    interest_rate: float


class CalculatorResponse(BaseModel):
    monthly_payment: float
    total_amount: float
    overpayment: float
