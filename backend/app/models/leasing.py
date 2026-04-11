import enum
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RequestStatus(str, enum.Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class PaymentScheduleStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class PurchaseContractStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeaseRequest(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lease_company_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    lease_term: Mapped[int] = mapped_column(Integer, nullable=False)
    prepayment: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    lease_company: Mapped["User"] = relationship("User", foreign_keys=[lease_company_id])
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    lessee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lessor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)

    contract_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    prepayment: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped["LeaseRequest"] = relationship("LeaseRequest")
    lessee: Mapped["User"] = relationship("User", foreign_keys=[lessee_id])
    lessor: Mapped["User"] = relationship("User", foreign_keys=[lessor_id])
    supplier: Mapped["User | None"] = relationship("User", foreign_keys=[supplier_id])
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")
    schedule: Mapped[list["PaymentSchedule"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="contract", cascade="all, delete-orphan")


class PaymentSchedule(Base):
    __tablename__ = "payment_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)

    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    principal_amount: Mapped[float] = mapped_column(Float, nullable=False)
    interest_amount: Mapped[float] = mapped_column(Float, nullable=False)
    vat_amount: Mapped[float] = mapped_column(Float, default=0.0)
    remaining_debt: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[PaymentScheduleStatus] = mapped_column(
        Enum(PaymentScheduleStatus), default=PaymentScheduleStatus.PENDING
    )

    contract: Mapped["Contract"] = relationship(back_populates="schedule")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    payment_schedule_id: Mapped[int | None] = mapped_column(ForeignKey("payment_schedule.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.SUCCESS)

    contract: Mapped["Contract"] = relationship(back_populates="payments")
    schedule_item: Mapped["PaymentSchedule | None"] = relationship("PaymentSchedule")


class PurchaseContract(Base):
    __tablename__ = "purchase_contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[PurchaseContractStatus] = mapped_column(
        Enum(PurchaseContractStatus), default=PurchaseContractStatus.PENDING
    )

    contract: Mapped["Contract"] = relationship("Contract")
    supplier: Mapped["User"] = relationship("User")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")
