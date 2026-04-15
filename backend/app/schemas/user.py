from datetime import date, datetime

import re

from pydantic import BaseModel, Field, field_validator

from app.models.user import ContactType, UserRole, UserType


# ── Auth ──────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Login, phone or email")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Contacts ──────────────────────────────────────────────────────────
class ContactCreate(BaseModel):
    type: ContactType
    value: str
    is_primary: bool = False


class ContactOut(ContactCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Individual ────────────────────────────────────────────────────────
class IndividualCreate(BaseModel):
    full_name: str
    registration_address: str | None = None
    passport_id: str | None = None
    passport_number: str | None = None
    issued_by: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None


class IndividualOut(IndividualCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Entrepreneur ──────────────────────────────────────────────────────
class EntrepreneurCreate(BaseModel):
    full_name: str
    unp: str | None = None
    legal_address: str | None = None
    postal_address: str | None = None


class EntrepreneurOut(EntrepreneurCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Company ───────────────────────────────────────────────────────────
class CompanyCreate(BaseModel):
    company_name: str
    legal_form: str | None = None
    unp: str | None = None
    okpo: str | None = None
    legal_address: str | None = None
    postal_address: str | None = None
    director_name: str | None = None


class CompanyOut(CompanyCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Bank Account ──────────────────────────────────────────────────────
_BANK_CODE_RE = re.compile(r"^[a-zA-Z0-9]+$")


class BankAccountCreate(BaseModel):
    iban: str | None = None
    bank_name: str | None = None
    bank_address: str | None = None
    swift: str | None = None
    bic: str | None = None

    @field_validator("iban", "swift", "bic")
    @classmethod
    def latin_digits_only(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        if not _BANK_CODE_RE.fullmatch(v):
            raise ValueError(
                "Поля IBAN, BIC и SWIFT: только латинские буквы и цифры, без пробелов"
            )
        return v


class BankAccountOut(BankAccountCreate):
    id: int
    model_config = {"from_attributes": True}


# ── Lease Terms ───────────────────────────────────────────────────────
class LeaseTermCreate(BaseModel):
    min_term_months: int = 6
    max_term_months: int = 84
    min_prepayment_pct: float = 10.0
    max_prepayment_pct: float = 49.0
    min_asset_price: float = 5000.0
    max_asset_price: float = 500000.0
    interest_rate: float = 12.0


class LeaseTermOut(LeaseTermCreate):
    id: int
    model_config = {"from_attributes": True}


# ── User ──────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    login: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    role: UserRole
    user_type: UserType
    contacts: list[ContactCreate] = []
    individual: IndividualCreate | None = None
    entrepreneur: EntrepreneurCreate | None = None
    company: CompanyCreate | None = None


class UserOut(BaseModel):
    id: int
    login: str
    role: UserRole
    user_type: UserType
    avatar_url: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime
    contacts: list[ContactOut] = []
    individual: IndividualOut | None = None
    entrepreneur: EntrepreneurOut | None = None
    company: CompanyOut | None = None
    bank_accounts: list[BankAccountOut] = []
    lease_terms: LeaseTermOut | None = None
    rating: float | None = None
    reviews_count: int = 0

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    description: str | None = None
    avatar_url: str | None = None


class UserPublicOut(BaseModel):
    id: int
    login: str
    role: UserRole
    user_type: UserType
    avatar_url: str | None = None
    description: str | None = None
    created_at: datetime
    contacts: list[ContactOut] = []
    individual: IndividualOut | None = None
    entrepreneur: EntrepreneurOut | None = None
    company: CompanyOut | None = None
    lease_terms: LeaseTermOut | None = None
    rating: float | None = None
    reviews_count: int = 0

    model_config = {"from_attributes": True}
