import time
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
    ContractType,
    LeaseRequest,
    Payment,
    PaymentSchedule,
    PaymentScheduleStatus,
    PaymentStatus,
    PurchaseContract,
    RequestStatus,
    SupplierRequest,
    SupplierRequestStatus,
)
from app.models.notification import Notification
from app.models.user import LeaseTerm, User, UserRole
from app.models.vehicle import Vehicle
from app.services.contract_document import (
    generate_la_document,
    generate_psa_document,
    upload_contract_document,
)
from app.services.settings_service import get_vat_rate_percent
from app.services.user_display import user_display_name
from app.schemas.leasing import (
    CalculatorRequest,
    CalculatorResponse,
    ContractConfirmation,
    ContractCreate,
    ContractFieldsUpdate,
    ContractOut,
    ContractStatusUpdate,
    LeaseRequestCreate,
    LeaseRequestOut,
    LeaseRequestStatusUpdate,
    PaymentCreate,
    PaymentOut,
    PaymentScheduleOut,
    PurchaseContractCreate,
    PurchaseContractOut,
    SupplierRequestCreate,
    SupplierRequestOut,
    SupplierRequestStatusUpdate,
)

router = APIRouter(prefix="/leasing", tags=["leasing"])


# ── Helpers ──────────────────────────────────────────────────────────

async def _load_users_map(db: AsyncSession, user_ids: set[int]) -> dict[int, User]:
    if not user_ids:
        return {}
    ures = await db.execute(
        select(User)
        .options(
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.company),
        )
        .where(User.id.in_(user_ids))
    )
    return {u.id: u for u in ures.scalars().unique().all()}


async def _lease_requests_out_batch(
    db: AsyncSession, reqs: list[LeaseRequest]
) -> list[LeaseRequestOut]:
    if not reqs:
        return []
    v_ids = {r.vehicle_id for r in reqs}
    u_ids = {r.user_id for r in reqs} | {r.lease_company_id for r in reqs}
    vres = await db.execute(select(Vehicle.id, Vehicle.name).where(Vehicle.id.in_(v_ids)))
    vmap = {row[0]: row[1] for row in vres.all()}
    umap = await _load_users_map(db, u_ids)
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


async def _supplier_requests_out_batch(
    db: AsyncSession, reqs: list[SupplierRequest]
) -> list[SupplierRequestOut]:
    if not reqs:
        return []
    v_ids = {r.vehicle_id for r in reqs}
    u_ids = {r.lessor_id for r in reqs} | {r.supplier_id for r in reqs}
    vres = await db.execute(select(Vehicle.id, Vehicle.name).where(Vehicle.id.in_(v_ids)))
    vmap = {row[0]: row[1] for row in vres.all()}
    umap = await _load_users_map(db, u_ids)
    out: list[SupplierRequestOut] = []
    for req in reqs:
        so = SupplierRequestOut.model_validate(req)
        out.append(
            so.model_copy(
                update={
                    "vehicle_name": vmap.get(req.vehicle_id),
                    "lessor_label": user_display_name(umap.get(req.lessor_id)),
                    "supplier_label": user_display_name(umap.get(req.supplier_id)),
                }
            )
        )
    return out


async def _contract_out(db: AsyncSession, contract: Contract) -> ContractOut:
    co = ContractOut.model_validate(contract)
    u_ids: set[int] = {contract.lessor_id}
    if contract.lessee_id:
        u_ids.add(contract.lessee_id)
    if contract.supplier_id:
        u_ids.add(contract.supplier_id)
    umap = await _load_users_map(db, u_ids)

    vres = await db.execute(select(Vehicle.name).where(Vehicle.id == contract.vehicle_id))
    vname = vres.scalar_one_or_none()

    return co.model_copy(
        update={
            "vehicle_name": vname,
            "lessee_label": user_display_name(umap.get(contract.lessee_id)) if contract.lessee_id else None,
            "lessor_label": user_display_name(umap.get(contract.lessor_id)),
            "supplier_label": user_display_name(umap.get(contract.supplier_id)) if contract.supplier_id else None,
        }
    )


def _gen_contract_number(prefix: str = "FL") -> str:
    return f"{prefix}-{time.time_ns() // 1_000_000:X}"


def _lease_financed_amount(asset_price: float, prepayment: float) -> float:
    """Часть стоимости техники, распределяемая на срок лизинга (без аванса)."""
    return max(0.0, asset_price - prepayment)


def _lease_contract_total_amount(asset_price: float, prepayment: float, interest_rate_pct: float) -> float:
    """Полная сумма договора: аванс + финансируемая часть × (1 + ставка%)."""
    f = _lease_financed_amount(asset_price, prepayment)
    return prepayment + f * (1.0 + interest_rate_pct / 100.0)


def _lease_monthly_payment(
    asset_price: float, prepayment: float, interest_rate_pct: float, term_months: int
) -> float:
    """Сумма ежемесячных платежей (без аванса) / срок — равными долями."""
    f = _lease_financed_amount(asset_price, prepayment)
    if f <= 0 or term_months <= 0:
        return 0.0
    financed_repay = f * (1.0 + interest_rate_pct / 100.0)
    return financed_repay / term_months


# ── Calculator ────────────────────────────────────────────────────────
@router.post("/calculator", response_model=CalculatorResponse)
async def calculate_leasing(data: CalculatorRequest):
    if data.term_months < 1:
        raise HTTPException(status_code=400, detail="Term months must be at least 1")

    principal = data.asset_price - data.prepayment
    if principal <= 0:
        raise HTTPException(status_code=400, detail="Prepayment exceeds asset price")

    total = _lease_contract_total_amount(data.asset_price, data.prepayment, data.interest_rate)
    monthly = _lease_monthly_payment(
        data.asset_price, data.prepayment, data.interest_rate, data.term_months
    )
    return CalculatorResponse(
        monthly_payment=round(monthly, 2),
        total_amount=round(total, 2),
        overpayment=round(total - data.asset_price, 2),
    )


# ── Lease Requests (лизингополучатель -> лизингодатель) ───────────────
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
        pass
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

    if data.status == RequestStatus.APPROVED:
        vehicle = await db.get(Vehicle, req.vehicle_id)
        lt_res = await db.execute(select(LeaseTerm).where(LeaseTerm.user_id == req.lease_company_id))
        lt = lt_res.scalar_one_or_none()
        interest_rate = lt.interest_rate if lt else 12.0
        price = vehicle.price if vehicle else 0
        total_amount = round(
            _lease_contract_total_amount(price, req.prepayment, interest_rate), 2
        )

        contract = Contract(
            request_id=req.id,
            lessee_id=req.user_id,
            lessor_id=req.lease_company_id,
            supplier_id=vehicle.supplier_id if vehicle else None,
            vehicle_id=req.vehicle_id,
            contract_type=ContractType.LEASE,
            contract_number=_gen_contract_number("LA"),
            total_amount=total_amount,
            prepayment=req.prepayment,
            interest_rate=interest_rate,
            quantity=1,
        )
        db.add(contract)
        await db.flush()

        chat_res = await db.execute(
            select(Chat).where(Chat.request_id == req.id, Chat.chat_type == ChatType.REQUEST)
        )
        chat = chat_res.scalar_one_or_none()
        if chat:
            chat.contract_id = contract.id

        db.add(Notification(
            user_id=req.user_id,
            title="Заявка одобрена",
            text=f"Ваша заявка #{req.id} одобрена. Сформирован договор лизинга #{contract.contract_number}.",
        ))
    else:
        status_labels = {
            RequestStatus.IN_REVIEW: "взята в работу",
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


# ── Supplier Requests (лизингодатель -> поставщик) ────────────────────
@router.post("/supplier-requests", response_model=SupplierRequestOut, status_code=201)
async def create_supplier_request(
    data: SupplierRequestCreate,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await db.get(Vehicle, data.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    lease_req = await db.get(LeaseRequest, data.lease_request_id)
    if not lease_req:
        raise HTTPException(status_code=404, detail="Lease request not found")

    sr = SupplierRequest(
        lease_request_id=data.lease_request_id,
        lessor_id=user.id,
        supplier_id=vehicle.supplier_id,
        vehicle_id=data.vehicle_id,
        quantity=data.quantity,
    )
    db.add(sr)
    await db.flush()

    chat = Chat(chat_type=ChatType.SUPPLIER, supplier_request_id=sr.id)
    db.add(chat)
    await db.flush()
    db.add(ChatParticipant(chat_id=chat.id, user_id=user.id))
    db.add(ChatParticipant(chat_id=chat.id, user_id=vehicle.supplier_id))

    db.add(Notification(
        user_id=vehicle.supplier_id,
        title="Новая заявка на покупку техники",
        text=f"Лизинговая компания хочет приобрести технику (заявка #{sr.id}).",
    ))

    await db.flush()
    enriched = await _supplier_requests_out_batch(db, [sr])
    return enriched[0]


@router.get("/supplier-requests", response_model=list[SupplierRequestOut])
async def list_supplier_requests(
    status: SupplierRequestStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(SupplierRequest)
    if user.role == UserRole.SUPPLIER:
        q = q.where(SupplierRequest.supplier_id == user.id)
    elif user.role == UserRole.LEASE_MANAGER:
        q = q.where(SupplierRequest.lessor_id == user.id)
    elif user.role == UserRole.ADMIN:
        pass
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    if status:
        q = q.where(SupplierRequest.status == status)
    q = q.order_by(SupplierRequest.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return await _supplier_requests_out_batch(db, list(rows))


@router.get("/supplier-requests/{sr_id}", response_model=SupplierRequestOut)
async def get_supplier_request(
    sr_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SupplierRequest).where(SupplierRequest.id == sr_id))
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Supplier request not found")
    if user.role == UserRole.SUPPLIER and sr.supplier_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if user.role == UserRole.LEASE_MANAGER and sr.lessor_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    enriched = await _supplier_requests_out_batch(db, [sr])
    return enriched[0]


@router.patch("/supplier-requests/{sr_id}/status", response_model=SupplierRequestOut)
async def update_supplier_request_status(
    sr_id: int,
    data: SupplierRequestStatusUpdate,
    user: User = Depends(require_role(UserRole.SUPPLIER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SupplierRequest)
        .options(selectinload(SupplierRequest.lease_request))
        .where(SupplierRequest.id == sr_id)
    )
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Supplier request not found")
    if user.role == UserRole.SUPPLIER and sr.supplier_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    sr.status = data.status
    await db.flush()

    if data.status == SupplierRequestStatus.APPROVED:
        vehicle = await db.get(Vehicle, sr.vehicle_id)
        price = vehicle.price if vehicle else 0

        psa_contract = Contract(
            supplier_request_id=sr.id,
            request_id=sr.lease_request_id,
            lessee_id=sr.lease_request.user_id if sr.lease_request else None,
            lessor_id=sr.lessor_id,
            supplier_id=sr.supplier_id,
            vehicle_id=sr.vehicle_id,
            contract_type=ContractType.PURCHASE_SALE,
            contract_number=_gen_contract_number("PSA"),
            total_amount=round(price * sr.quantity, 2),
            prepayment=0,
            interest_rate=0,
            quantity=sr.quantity,
            status=ContractStatus.ACTIVE,
        )
        db.add(psa_contract)
        await db.flush()

        chat_res = await db.execute(
            select(Chat).where(Chat.supplier_request_id == sr.id, Chat.chat_type == ChatType.SUPPLIER)
        )
        chat = chat_res.scalar_one_or_none()
        if chat:
            chat.contract_id = psa_contract.id

        db.add(Notification(
            user_id=sr.lessor_id,
            title="Заявка на покупку одобрена",
            text=f"Поставщик одобрил заявку #{sr.id}. Сформирован договор купли-продажи #{psa_contract.contract_number}.",
        ))
    else:
        status_labels = {
            SupplierRequestStatus.IN_REVIEW: "взята в работу",
            SupplierRequestStatus.REJECTED: "отклонена",
        }
        db.add(Notification(
            user_id=sr.lessor_id,
            title="Статус заявки на покупку обновлён",
            text=f"Заявка на покупку #{sr.id} {status_labels.get(data.status, 'обновлена')}.",
        ))

    await db.flush()
    enriched = await _supplier_requests_out_batch(db, [sr])
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

    if data.lessee_id:
        db.add(Notification(
            user_id=data.lessee_id,
            title="Новый договор",
            text=f"Сформирован договор #{data.contract_number}.",
        ))
    await db.flush()
    return await _contract_out(db, contract)


@router.get("/contracts", response_model=list[ContractOut])
async def list_contracts(
    status: ContractStatus | None = None,
    contract_type: ContractType | None = None,
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
        q = q.where(Contract.supplier_id == user.id, Contract.contract_type == ContractType.PURCHASE_SALE)
    if status:
        q = q.where(Contract.status == status)
    if contract_type:
        q = q.where(Contract.contract_type == contract_type)
    q = q.order_by(Contract.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    contracts = result.scalars().all()
    out = []
    for c in contracts:
        out.append(await _contract_out(db, c))
    return out


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
    if user.role == UserRole.SUPPLIER and contract.contract_type != ContractType.PURCHASE_SALE:
        raise HTTPException(status_code=403, detail="Access denied")
    return await _contract_out(db, contract)


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

    notify_ids: set[int] = set()
    if contract.lessee_id:
        notify_ids.add(contract.lessee_id)
    if contract.supplier_id:
        notify_ids.add(contract.supplier_id)
    notify_ids.discard(user.id)
    for uid in notify_ids:
        db.add(Notification(
            user_id=uid,
            title="Статус договора обновлён",
            text=f"Договор #{contract.contract_number} получил статус: {data.status.value}.",
        ))
    await db.flush()
    return await _contract_out(db, contract)


@router.patch("/contracts/{contract_id}/fields", response_model=ContractOut)
async def update_contract_fields(
    contract_id: int,
    data: ContractFieldsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.all_confirmed:
        raise HTTPException(status_code=400, detail="Все стороны уже подтвердили данные. Редактирование невозможно.")

    is_lessor = user.role in (UserRole.LEASE_MANAGER, UserRole.ADMIN) and contract.lessor_id == user.id
    is_supplier = (
        user.role == UserRole.SUPPLIER
        and contract.supplier_id == user.id
        and contract.contract_type == ContractType.PURCHASE_SALE
    )

    if is_lessor:
        if data.signing_date is not None:
            contract.signing_date = data.signing_date
        if data.signing_city is not None:
            contract.signing_city = data.signing_city
        if data.currency is not None:
            contract.currency = data.currency
    elif is_supplier:
        if data.tech_passport_number is not None:
            contract.tech_passport_number = data.tech_passport_number
        if data.tech_passport_date is not None:
            contract.tech_passport_date = data.tech_passport_date
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    contract.lessee_confirmed = False
    contract.lessor_confirmed = False
    contract.supplier_confirmed = False
    contract.all_confirmed = False

    await db.flush()
    return await _contract_out(db, contract)


@router.post("/contracts/{contract_id}/confirm", response_model=ContractOut)
async def confirm_contract(
    contract_id: int,
    data: ContractConfirmation,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.all_confirmed:
        raise HTTPException(status_code=400, detail="Все стороны уже подтвердили данные.")

    is_lease = contract.contract_type == ContractType.LEASE

    if user.id == contract.lessor_id:
        contract.lessor_confirmed = data.confirmed
    elif user.id == contract.lessee_id:
        contract.lessee_confirmed = data.confirmed
    elif user.id == contract.supplier_id and not is_lease:
        contract.supplier_confirmed = data.confirmed
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    need_lessee = contract.lessee_id is not None
    need_supplier = contract.supplier_id is not None and not is_lease
    all_ok = contract.lessor_confirmed
    if need_lessee:
        all_ok = all_ok and contract.lessee_confirmed
    if need_supplier:
        all_ok = all_ok and contract.supplier_confirmed

    if all_ok:
        contract.all_confirmed = True
        vat_rate = await get_vat_rate_percent(db)
        contract.vat_rate = vat_rate

        if contract.signing_date and contract.request_id:
            lease_req_res = await db.execute(
                select(LeaseRequest).where(LeaseRequest.id == contract.request_id)
            )
            lease_req = lease_req_res.scalar_one_or_none()
            if lease_req:
                contract.start_date = contract.signing_date
                contract.end_date = contract.signing_date + timedelta(days=30 * lease_req.lease_term)

    await db.flush()
    return await _contract_out(db, contract)


# ── Payment Schedule ──────────────────────────────────────────────────
@router.post("/contracts/{contract_id}/schedule", response_model=list[PaymentScheduleOut])
async def generate_schedule(
    contract_id: int,
    user: User = Depends(require_role(UserRole.LEASE_MANAGER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    existing = await db.execute(
        select(PaymentSchedule).where(PaymentSchedule.contract_id == contract_id)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="График платежей уже сформирован")

    req_result = await db.execute(select(LeaseRequest).where(LeaseRequest.id == contract.request_id))
    req = req_result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=400, detail="Связанная заявка не найдена")

    vehicle = await db.get(Vehicle, contract.vehicle_id)
    price = float(vehicle.price) if vehicle else 0.0
    prepayment = float(contract.prepayment)
    r_pct = float(contract.interest_rate)
    f = _lease_financed_amount(price, prepayment)
    financed_repay = f * (1.0 + r_pct / 100.0)
    n = req.lease_term
    if n < 1:
        raise HTTPException(status_code=400, detail="Срок лизинга в заявке не задан")

    start = contract.start_date or contract.signing_date or date.today()
    vat_rate = contract.vat_rate or await get_vat_rate_percent(db)
    vat_fraction = vat_rate / 100.0
    items = []

    sum_pay = 0.0
    sum_princ = 0.0

    for i in range(1, n + 1):
        is_last = i == n
        if f <= 0:
            pay = 0.0
            principal_part = 0.0
            interest_part = 0.0
        elif is_last:
            pay = round(financed_repay - sum_pay, 2)
            principal_part = round(f - sum_princ, 2)
            interest_part = round(pay - principal_part, 2)
        else:
            pay = round(financed_repay / n, 2)
            principal_part = round(f / n, 2)
            interest_part = round(pay - principal_part, 2)
        sum_pay += pay
        sum_princ += principal_part
        remaining_after = round(financed_repay - sum_pay, 2)

        payment_date = start + timedelta(days=30 * i)

        ps = PaymentSchedule(
            contract_id=contract.id,
            payment_date=payment_date,
            total_amount=round(pay, 2),
            principal_amount=round(principal_part, 2),
            interest_amount=round(interest_part, 2),
            vat_amount=round(pay * vat_fraction, 2),
            remaining_debt=round(max(remaining_after, 0), 2),
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


# ── Document Generation ──────────────────────────────────────────────
@router.post("/contracts/{contract_id}/generate-documents", response_model=ContractOut)
async def generate_documents(
    contract_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not contract.all_confirmed:
        raise HTTPException(status_code=400, detail="Все стороны должны подтвердить данные перед генерацией документов")

    vehicle = await db.get(Vehicle, contract.vehicle_id)

    lessor = await db.execute(
        select(User)
        .options(
            selectinload(User.company),
            selectinload(User.individual),
            selectinload(User.entrepreneur),
            selectinload(User.bank_accounts),
            selectinload(User.contacts),
        )
        .where(User.id == contract.lessor_id)
    )
    lessor_user = lessor.scalar_one_or_none()

    lessee_user = None
    if contract.lessee_id:
        lessee = await db.execute(
            select(User)
            .options(
                selectinload(User.company),
                selectinload(User.individual),
                selectinload(User.entrepreneur),
                selectinload(User.bank_accounts),
                selectinload(User.contacts),
            )
            .where(User.id == contract.lessee_id)
        )
        lessee_user = lessee.scalar_one_or_none()

    supplier_user = None
    if contract.supplier_id:
        supplier = await db.execute(
            select(User)
            .options(
                selectinload(User.company),
                selectinload(User.individual),
                selectinload(User.entrepreneur),
                selectinload(User.bank_accounts),
                selectinload(User.contacts),
            )
            .where(User.id == contract.supplier_id)
        )
        supplier_user = supplier.scalar_one_or_none()

    try:
        if contract.contract_type == ContractType.PURCHASE_SALE:
            buf = generate_psa_document(contract, vehicle, supplier_user, lessor_user, lessee_user)
            url = upload_contract_document(buf, f"contracts/psa/{contract.id}", "contract.docx")
            contract.psa_doc_url = url
        elif contract.contract_type == ContractType.LEASE:
            buf = generate_la_document(contract, vehicle, lessor_user, lessee_user, supplier_user)
            url = upload_contract_document(buf, f"contracts/la/{contract.id}", "contract.docx")
            contract.la_doc_url = url
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Шаблон документа не найден на сервере")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации документа: {exc}")

    await db.flush()
    return await _contract_out(db, contract)


@router.get("/contracts/{contract_id}/documents")
async def get_contract_documents(
    contract_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {
        "psa_doc_url": contract.psa_doc_url,
        "la_doc_url": contract.la_doc_url,
    }


# ── Purchase Contracts (legacy) ──────────────────────────────────────
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
        text="Лизинговая компания хочет приобрести технику. Проверьте чат.",
    ))
    await db.flush()
    return pc
