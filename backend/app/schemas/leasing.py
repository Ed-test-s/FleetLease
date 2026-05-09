from datetime import date, datetime

from pydantic import BaseModel

from app.models.leasing import (
    ContractStatus,
    ContractType,
    PaymentScheduleStatus,
    PaymentStatus,
    PurchaseContractStatus,
    RequestStatus,
    SupplierRequestStatus,
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
    vehicle_name: str | None = None
    client_label: str | None = None
    lease_company_label: str | None = None
    model_config = {"from_attributes": True}


class LeaseRequestStatusUpdate(BaseModel):
    status: RequestStatus


# ── Supplier Request ──────────────────────────────────────────────────
class SupplierRequestCreate(BaseModel):
    lease_request_id: int
    vehicle_id: int
    quantity: int = 1


class SupplierRequestOut(BaseModel):
    id: int
    lease_request_id: int
    lessor_id: int
    supplier_id: int
    vehicle_id: int
    quantity: int
    status: SupplierRequestStatus
    created_at: datetime
    vehicle_name: str | None = None
    lessor_label: str | None = None
    supplier_label: str | None = None
    model_config = {"from_attributes": True}


class SupplierRequestStatusUpdate(BaseModel):
    status: SupplierRequestStatus


# ── Contract ──────────────────────────────────────────────────────────
class ContractCreate(BaseModel):
    request_id: int | None = None
    supplier_request_id: int | None = None
    lessee_id: int | None = None
    lessor_id: int
    supplier_id: int | None = None
    vehicle_id: int
    contract_type: ContractType = ContractType.LEASE
    contract_number: str
    start_date: date | None = None
    end_date: date | None = None
    total_amount: float
    prepayment: float
    interest_rate: float
    quantity: int = 1


class ContractOut(BaseModel):
    id: int
    request_id: int | None = None
    supplier_request_id: int | None = None
    lessee_id: int | None = None
    lessor_id: int
    supplier_id: int | None = None
    vehicle_id: int
    contract_type: ContractType
    contract_number: str
    start_date: date | None = None
    end_date: date | None = None
    total_amount: float
    prepayment: float
    interest_rate: float
    signing_date: date | None = None
    signing_city: str | None = None
    currency: str | None = None
    vat_rate: float | None = None
    tech_passport_number: str | None = None
    tech_passport_date: date | None = None
    quantity: int = 1
    lessee_confirmed: bool = False
    lessor_confirmed: bool = False
    supplier_confirmed: bool = False
    all_confirmed: bool = False
    psa_doc_url: str | None = None
    la_doc_url: str | None = None
    status: ContractStatus
    created_at: datetime
    vehicle_name: str | None = None
    lessee_label: str | None = None
    lessor_label: str | None = None
    supplier_label: str | None = None
    linked_purchase_contract_id: int | None = None
    linked_purchase_contract_number: str | None = None
    linked_purchase_status: ContractStatus | None = None
    linked_lease_contract_id: int | None = None
    linked_lease_contract_number: str | None = None
    model_config = {"from_attributes": True}


class ContractStatusUpdate(BaseModel):
    status: ContractStatus


class ContractFieldsUpdate(BaseModel):
    signing_date: date | None = None
    signing_city: str | None = None
    currency: str | None = None
    tech_passport_number: str | None = None
    tech_passport_date: date | None = None


class ContractConfirmation(BaseModel):
    confirmed: bool


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
class PaymentPrepareOut(BaseModel):
    sender_iban: str | None = None
    sender_swift: str | None = None
    receiver_iban: str | None = None
    receiver_swift: str | None = None
    amount: float
    currency: str
    receiver_name: str
    contract_number: str


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
