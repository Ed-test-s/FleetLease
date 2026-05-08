from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_settings import AppSettings
from app.schemas.about import AboutBlock, AboutHero, AboutPageContent
from app.services import settings_service


def default_about_content() -> AboutPageContent:
    return AboutPageContent(
        hero=AboutHero(
            title="FleetLease",
            subtitle="Платформа для подбора лизинга грузовой техники: лизингополучатели, лизинговые компании и поставщики на одной площадке.",
            image_url=None,
        ),
        blocks=[
            AboutBlock(
                title="Наша миссия",
                body="Мы помогаем бизнесу находить технику и финансовые решения быстрее и прозрачнее.",
                image_url=None,
            ),
            AboutBlock(
                title="Как это работает",
                body=(
                    "Зарегистрируйтесь с нужной ролью, разместите или найдите технику, "
                    "обменивайтесь сообщениями и оформляйте заявки — всё в рамках сервиса FleetLease."
                ),
                image_url=None,
            ),
        ],
    )


def merge_about_from_row(row: AppSettings) -> AboutPageContent:
    if row.about_page_json is None:
        return default_about_content()
    try:
        return AboutPageContent.model_validate(row.about_page_json)
    except ValidationError:
        return default_about_content()


async def get_about_content(db: AsyncSession) -> AboutPageContent:
    row = await settings_service.ensure_app_settings_row(db)
    return merge_about_from_row(row)


async def save_about_content(db: AsyncSession, content: AboutPageContent) -> AboutPageContent:
    row = await settings_service.ensure_app_settings_row(db)
    row.about_page_json = content.model_dump(mode="json")
    await db.flush()
    return content
