from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.chat import Chat, ChatParticipant, ChatType
from app.models.leasing import (
    Contract,
    ContractStatus,
    LeaseRequest,
    Payment,
    PaymentSchedule,
    PaymentScheduleStatus,
    PaymentStatus,
    PurchaseContract,
    RequestStatus,
)
from app.models.notification import Notification
from app.models.user import LeaseTerm, User, UserRole
from app.models.vehicle import Vehicle
from app.services.user_display import user_display_name
from app.schemas.leasing import (
    CalculatorRequest,
    CalculatorResponse,
    ContractCreate,
    ContractOut,
    ContractStatusUpdate,
    LeaseRequestCreate,
    LeaseRequestOut,
    LeaseRequestStatusUpdate,
    PaymentCreate,
    PaymentOut,
    PaymentScheduleCreate,
    PaymentScheduleOut,
    PurchaseContractCreate,
    PurchaseContractOut,
)

router = APIRouter(prefix="/leasing", tags=["leasing"])


async def _lease_requests_out_batch(
    db: AsyncSession, reqs: list[LeaseRequest]
) -> list[LeaseRequestOut]:
    if not reqs:
        return []
    v_ids = {r.vehicle_id for r in reqs}
    u_ids = {r.user_id for r in reqs} | {r.lease_company_id for r in reqs}
    vres = await db.execute(select(Vehicle.id, Vehicle.name).where(Vehicle.id.in_(v_ids)))
    vmap = {row[0]: row[1] for row in vres.all()}
    ures = await db.execute(
        select(User)
        .options(
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.company),
        )
        .where(User.id.in_(u_ids))
    )
    umap = {u.id: u for u in ures.scalars().unique().all()}
    out: list[LeaseRequestOut] = []
    for req in reqs:
        lo = LeaseRequestOut.model_validate(req)
        lessee = umap.get(req.user_id)
        lessor = umap.get(req.lease_company_id)
        out.append(
            lo.model_copy(
                update={
                    "vehicle_name": vmap.get(req.vehicle_id),
                    "client_label": user_display_name(lessee),
                    "lease_company_label": user_display_name(lessor),
                }
            )
        )
    return out


# ── Calculator ────────────────────────────────────────────────────────
@router.post("/calculator", response_model=CalculatorResponse)
async def calculate_leasing(data: CalculatorRequest):
    """Аннуитетный расчёт лизинга."""
    principal = data.asset_price - data.prepayment
    if principal <= 0:
        raise HTTPException(status_code=400, detail="Prepayment exceeds asset price")

    monthly_rate = data.interest_rate / 100.0 / 12.0
    n = data.term_months

    if monthly_rate > 0:
        annuity = principal * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
    else:
        annuity = principal / n

    total = annuity * n + data.prepayment
    return CalculatorResponse(
        monthly_payment=round(annuity, 2),
        total_amount=round(total, 2),
        overpayment=round(total - data.asset_price, 2),
    )


# ── Requests ──────────────────────────────────────────────────────────
@router.post("/requests", response_model=LeaseRequestOut, status_code=201)
async def create_request(
    data: LeaseRequestCreate,
    user: User = Depends(require_role(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await db.get(Vehicle, data.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    lt_result = await db.execute(select(LeaseTerm).where(LeaseTerm.user_id == data.lease_company_id))
    lt = lt_result.scalar_one_or_none()
    if lt:
        if vehicle.price < lt.min_asset_price or vehicle.price > lt.max_asset_price:
            raise HTTPException(
                status_code=400,
                detail="Стоимость техники не входит в допустимый для выбранного лизингодателя диапазон",
            )
        if data.lease_term < lt.min_term_months or data.lease_term > lt.max_term_months:
            raise HTTPException(
                status_code=400,
                detail="Срок лизинга вне допустимого диапазона для выбранного лизингодателя",
            )
        min_prep = vehicle.price * lt.min_prepayment_pct / 100.0
        max_prep = vehicle.price * lt.max_prepayment_pct / 100.0
        if data.prepayment < min_prep - 0.01 or data.prepayment > max_prep + 0.01:
            raise HTTPException(
                status_code=400,
                detail="Первоначальный взнос вне допустимого диапазона для выбранного лизингодателя",
            )

    req = LeaseRequest(user_id=user.id, **data.model_dump())
    db.add(req)
    await db.flush()

    chat = Chat(chat_type=ChatType.REQUEST, request_id=req.id)
    db.add(chat)
    await db.flush()
    db.add(ChatParticipant(chat_id=chat.id, user_id=user.id))
    db.add(ChatParticipant(chat_id=chat.id, user_id=data.lease_company_id))

    db.add(Notification(
        user_id=data.lease_company_id,
        title="Новая заявка на лизинг",
        text=f"Поступила новая заявка #{req.id} на лизинг техники.",
    ))

    await db.flush()
    enriched = await _lease_requests_out_batch(db, [req])
    return enriched[0]


@router.get("/requests", response_model=list[LeaseRequestOut])
async def list_requests(
    status: RequestStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(LeaseRequest)
    if user.role == UserRole.CLIENT:
        q = q.where(LeaseRequest.user_id == user.id)
    elif user.role == UserRole.LEASE_MANAGER:
        q = q.where(LeaseRequest.lease_company_id == user.id)
    elif user.role == UserRole.ADMIN:
        pass  # all requests
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    if status:
        q = q.where(LeaseRequest.status == status)
    q = q.order_by(LeaseRequest.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return await _lease_requests_out_batch(db, list(rows))


@router.get("/requests/{request_id}", response_model=LeaseRequestOut)
async def get_request(
    request_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LeaseRequest).where(LeaseRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role == UserRole.CLIENT and req.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if user.role == UserRole.LEASE_MANAGER and req.lease_company_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    enriched = await _lease_requests_out_batch(db, [req])
    return enriched[0]


@router.patch("/requests/{request_id}/status", response_model=LeaseRequestOut)
async def update_request_status(
    request_id: int,
    data: LeaseRequestStatusUpdate,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LeaseRequest).where(LeaseRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role == UserRole.LEASE_MANAGER and req.lease_company_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    req.status = data.status
    await db.flush()

    status_labels = {
        RequestStatus.IN_REVIEW: "взята в работу",
        RequestStatus.APPROVED: "одобрена",
        RequestStatus.REJECTED: "отклонена",
    }
    db.add(Notification(
        user_id=req.user_id,
        title="Статус заявки обновлён",
        text=f"Ваша заявка #{req.id} {status_labels.get(data.status, 'обновлена')}.",
    ))
    await db.flush()
    enriched = await _lease_requests_out_batch(db, [req])
    return enriched[0]


# ── Contracts ─────────────────────────────────────────────────────────
@router.post("/contracts", response_model=ContractOut, status_code=201)
async def create_contract(
    data: ContractCreate,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    contract = Contract(**data.model_dump())
    db.add(contract)
    await db.flush()

    db.add(Notification(
        user_id=data.lessee_id,
        title="Новый договор лизинга",
        text=f"Сформирован договор #{data.contract_number}.",
    ))
    await db.flush()
    return contract


@router.get("/contracts", response_model=list[ContractOut])
async def list_contracts(
    status: ContractStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Contract)
    if user.role == UserRole.CLIENT:
        q = q.where(Contract.lessee_id == user.id)
    elif user.role == UserRole.LEASE_MANAGER:
        q = q.where(Contract.lessor_id == user.id)
    elif user.role == UserRole.SUPPLIER:
        q = q.where(Contract.supplier_id == user.id)
    if status:
        q = q.where(Contract.status == status)
    q = q.order_by(Contract.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/contracts/{contract_id}", response_model=ContractOut)
async def get_contract(
    contract_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.patch("/contracts/{contract_id}/status", response_model=ContractOut)
async def update_contract_status(
    contract_id: int,
    data: ContractStatusUpdate,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract.status = data.status
    await db.flush()

    db.add(Notification(
        user_id=contract.lessee_id,
        title="Статус договора обновлён",
        text=f"Договор #{contract.contract_number} получил статус: {data.status.value}.",
    ))
    await db.flush()
    return contract


# ── Payment Schedule ──────────────────────────────────────────────────
@router.post("/contracts/{contract_id}/schedule", response_model=list[PaymentScheduleOut])
async def generate_schedule(
    contract_id: int,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Автоматическая генерация графика платежей на основе данных договора."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    req_result = await db.execute(select(LeaseRequest).where(LeaseRequest.id == contract.request_id))
    req = req_result.scalar_one()

    principal = contract.total_amount - contract.prepayment
    monthly_rate = contract.interest_rate / 100.0 / 12.0
    n = req.lease_term

    if monthly_rate > 0:
        annuity = principal * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
    else:
        annuity = principal / n

    start = contract.start_date or date.today()
    remaining = principal
    items = []

    for i in range(1, n + 1):
        interest = remaining * monthly_rate
        principal_part = annuity - interest
        remaining -= principal_part
        payment_date = start + timedelta(days=30 * i)

        ps = PaymentSchedule(
            contract_id=contract.id,
            payment_date=payment_date,
            total_amount=round(annuity, 2),
            principal_amount=round(principal_part, 2),
            interest_amount=round(interest, 2),
            vat_amount=round(annuity * 0.20, 2),
            remaining_debt=round(max(remaining, 0), 2),
        )
        db.add(ps)
        items.append(ps)

    await db.flush()
    return items


@router.get("/contracts/{contract_id}/schedule", response_model=list[PaymentScheduleOut])
async def get_schedule(
    contract_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PaymentSchedule)
        .where(PaymentSchedule.contract_id == contract_id)
        .order_by(PaymentSchedule.payment_date)
    )
    return result.scalars().all()


# ── Payments ──────────────────────────────────────────────────────────
@router.post("/payments", response_model=PaymentOut, status_code=201)
async def make_payment(
    data: PaymentCreate,
    user: User = Depends(require_role(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db),
):
    payment = Payment(
        contract_id=data.contract_id,
        payment_schedule_id=data.payment_schedule_id,
        amount=data.amount,
        payment_date=date.today(),
        payment_method=data.payment_method or "online",
        status=PaymentStatus.SUCCESS,
    )
    db.add(payment)

    if data.payment_schedule_id:
        ps_result = await db.execute(
            select(PaymentSchedule).where(PaymentSchedule.id == data.payment_schedule_id)
        )
        ps = ps_result.scalar_one_or_none()
        if ps:
            ps.status = PaymentScheduleStatus.PAID

    await db.flush()
    return payment


# ── Purchase Contracts ────────────────────────────────────────────────
@router.post("/purchase-contracts", response_model=PurchaseContractOut, status_code=201)
async def create_purchase_contract(
    data: PurchaseContractCreate,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    pc = PurchaseContract(**data.model_dump())
    db.add(pc)
    await db.flush()

    chat = Chat(chat_type=ChatType.SUPPLIER, contract_id=data.contract_id)
    db.add(chat)
    await db.flush()
    db.add(ChatParticipant(chat_id=chat.id, user_id=user.id))
    db.add(ChatParticipant(chat_id=chat.id, user_id=data.supplier_id))

    db.add(Notification(
        user_id=data.supplier_id,
        title="Запрос на покупку техники",
        text=f"Лизинговая компания хочет приобрести технику. Проверьте чат.",
    ))
    await db.flush()
    return pc
