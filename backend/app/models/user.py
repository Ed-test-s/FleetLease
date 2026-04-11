import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    CLIENT = "client"
    LEASE_MANAGER = "lease_manager"
    SUPPLIER = "supplier"
    ADMIN = "admin"


class UserType(str, enum.Enum):
    INDIVIDUAL = "individual"
    IE = "ie"  # индивидуальный предприниматель
    COMPANY = "company"


class ContactType(str, enum.Enum):
    PHONE = "phone"
    EMAIL = "email"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contacts: Mapped[list["UserContact"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    individual: Mapped["Individual | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    entrepreneur: Mapped["Entrepreneur | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    company: Mapped["Company | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    bank_accounts: Mapped[list["BankAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    lease_terms: Mapped["LeaseTerm | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserContact(Base):
    __tablename__ = "user_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[ContactType] = mapped_column(Enum(ContactType), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="contacts")


class Individual(Base):
    __tablename__ = "individuals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    passport_id: Mapped[str | None] = mapped_column(String(14), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(9), nullable=True)
    issued_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="individual")


class Entrepreneur(Base):
    __tablename__ = "entrepreneurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unp: Mapped[str | None] = mapped_column(String(9), nullable=True)
    legal_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="entrepreneur")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_form: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unp: Mapped[str | None] = mapped_column(String(9), nullable=True)
    okpo: Mapped[str | None] = mapped_column(String(12), nullable=True)
    legal_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    director_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="company")


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    swift: Mapped[str | None] = mapped_column(String(11), nullable=True)
    bic: Mapped[str | None] = mapped_column(String(11), nullable=True)

    user: Mapped["User"] = relationship(back_populates="bank_accounts")


class LeaseTerm(Base):
    """Условия лизинга, которые задаёт лизингодатель для калькулятора."""
    __tablename__ = "lease_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    min_term_months: Mapped[int] = mapped_column(Integer, default=6)
    max_term_months: Mapped[int] = mapped_column(Integer, default=84)
    min_prepayment_pct: Mapped[float] = mapped_column(default=10.0)
    max_prepayment_pct: Mapped[float] = mapped_column(default=49.0)
    min_asset_price: Mapped[float] = mapped_column(default=5000.0)
    max_asset_price: Mapped[float] = mapped_column(default=500000.0)
    interest_rate: Mapped[float] = mapped_column(default=12.0)

    user: Mapped["User"] = relationship(back_populates="lease_terms")
