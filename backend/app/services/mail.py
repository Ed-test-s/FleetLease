"""Отправка писем через fastapi-mail."""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings


def is_mail_configured() -> bool:
    return bool(settings.MAIL_SERVER and settings.MAIL_SERVER.strip() and settings.MAIL_FROM and settings.MAIL_FROM.strip())


def _connection_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
        VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS,
    )


async def send_temporary_password_email(to_email: str, temp_password: str) -> None:
    """Письмо с временным паролем для входа и рекомендацией сменить пароль в профиле."""
    body = (
        "Здравствуйте!\n\n"
        f"Ваш временный пароль для входа в систему FleetLease:\n{temp_password}\n\n"
        "Этот пароль является временным. Рекомендуем как можно скорее сменить его "
        "на постоянный в разделе «Мой профиль» после входа в систему.\n\n"
        "Если вы не запрашивали восстановление доступа, проигнорируйте это письмо.\n"
    )
    message = MessageSchema(
        subject="FleetLease — восстановление доступа",
        recipients=[to_email],
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(_connection_config())
    await fm.send_message(message)
