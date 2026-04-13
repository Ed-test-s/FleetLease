"""Отображаемые имена пользователей для списков и заявок."""

from app.models.user import User


def user_display_name(user: User | None) -> str | None:
    if user is None:
        return None
    if user.individual and user.individual.full_name:
        return user.individual.full_name
    if user.entrepreneur and user.entrepreneur.full_name:
        return user.entrepreneur.full_name
    if user.company and user.company.company_name:
        lf = (user.company.legal_form or "").strip()
        return f'{lf} «{user.company.company_name}»'.strip() if lf else f'«{user.company.company_name}»'
    return user.login
