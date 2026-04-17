from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.chat import Chat, ChatParticipant, Message
from app.models.leasing import LeaseRequest, SupplierRequest
from app.models.notification import Notification
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.chat import ChatCreate, ChatOut, ChatPartnerOut, MessageCreate, MessageOut
from app.services.storage import storage_service
from app.services.user_display import user_display_name

router = APIRouter(prefix="/chats", tags=["chats"])

# In-memory WebSocket connections: {chat_id: {user_id: WebSocket}}
active_connections: dict[int, dict[int, WebSocket]] = {}


async def _chat_out_with_partner(
    db: AsyncSession, chat: Chat, current_user_id: int
) -> ChatOut:
    co = ChatOut.model_validate(chat)
    co.last_message = MessageOut.model_validate(chat.messages[-1]) if chat.messages else None
    other_ids = [p.user_id for p in chat.participants if p.user_id != current_user_id]
    if not other_ids:
        co.partner = None
    else:
        ures = await db.execute(
            select(User)
            .options(
                selectinload(User.individual),
                selectinload(User.entrepreneur),
                selectinload(User.company),
            )
            .where(User.id == other_ids[0])
        )
        pu = ures.scalar_one_or_none()
        if pu:
            name = user_display_name(pu) or pu.login
            co.partner = ChatPartnerOut(id=pu.id, display_name=name, avatar_url=pu.avatar_url)
        else:
            co.partner = None

    vehicle_id = None
    if chat.request_id:
        lr_res = await db.execute(select(LeaseRequest.vehicle_id).where(LeaseRequest.id == chat.request_id))
        vehicle_id = lr_res.scalar_one_or_none()
    elif chat.supplier_request_id:
        sr_res = await db.execute(select(SupplierRequest.vehicle_id).where(SupplierRequest.id == chat.supplier_request_id))
        vehicle_id = sr_res.scalar_one_or_none()

    if vehicle_id:
        vres = await db.execute(select(Vehicle.name).where(Vehicle.id == vehicle_id))
        co.vehicle_name = vres.scalar_one_or_none()

    return co


@router.get("/", response_model=list[ChatOut])
async def list_chats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Chat)
        .join(ChatParticipant)
        .options(selectinload(Chat.participants), selectinload(Chat.messages))
        .where(ChatParticipant.user_id == user.id)
        .order_by(Chat.created_at.desc())
    )
    result = await db.execute(q)
    chats = result.scalars().unique().all()

    out = []
    for chat in chats:
        out.append(await _chat_out_with_partner(db, chat, user.id))
    return out


@router.get("/{chat_id}", response_model=ChatOut)
async def get_chat(
    chat_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.participants), selectinload(Chat.messages))
        .where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    participant_ids = [p.user_id for p in chat.participants]
    if user.id not in participant_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    return await _chat_out_with_partner(db, chat, user.id)


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
async def get_messages(
    chat_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    part_check = await db.execute(
        select(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id, ChatParticipant.user_id == user.id
        )
    )
    if not part_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def _assert_chat_participant(db: AsyncSession, chat_id: int, user_id: int) -> None:
    part_check = await db.execute(
        select(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id, ChatParticipant.user_id == user_id
        )
    )
    if not part_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")


async def _send_message_and_notify(
    db: AsyncSession,
    chat_id: int,
    user: User,
    message_text: str,
    file_url: str | None,
) -> Message:
    msg = Message(chat_id=chat_id, sender_id=user.id, message_text=message_text, file_url=file_url)
    db.add(msg)
    await db.flush()

    parts_result = await db.execute(
        select(ChatParticipant).where(ChatParticipant.chat_id == chat_id, ChatParticipant.user_id != user.id)
    )
    for part in parts_result.scalars().all():
        db.add(Notification(
            user_id=part.user_id,
            title="Новое сообщение",
            text=f"Вам пришло новое сообщение в чате #{chat_id}.",
        ))

    await db.flush()

    if chat_id in active_connections:
        for uid, ws in active_connections[chat_id].items():
            if uid != user.id:
                try:
                    await ws.send_json(MessageOut.model_validate(msg).model_dump(mode="json"))
                except Exception:
                    pass

    return msg


@router.post("/{chat_id}/messages/attachment", response_model=MessageOut, status_code=201)
async def send_message_with_attachment(
    chat_id: int,
    message_text: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_participant(db, chat_id, user.id)
    file_url = await storage_service.upload_file(file, folder=f"chat_files/{chat_id}")
    return await _send_message_and_notify(db, chat_id, user, message_text, file_url)


@router.post("/{chat_id}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    chat_id: int,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_participant(db, chat_id, user.id)
    return await _send_message_and_notify(db, chat_id, user, data.message_text, None)


@router.websocket("/{chat_id}/ws")
async def websocket_chat(websocket: WebSocket, chat_id: int):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001)
        return
    user_id = int(payload["sub"])

    await websocket.accept()

    if chat_id not in active_connections:
        active_connections[chat_id] = {}
    active_connections[chat_id][user_id] = websocket

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[chat_id].pop(user_id, None)
        if not active_connections[chat_id]:
            del active_connections[chat_id]
