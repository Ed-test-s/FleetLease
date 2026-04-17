"""Заполнение справочников и создание администратора при первом запуске."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.app_settings import AppSettings
from app.models.reference import City, Colour, Region, VehicleBrand, VehicleModel
from app.models.user import Individual, User, UserRole, UserType

BRANDS_AND_MODELS: dict[str, list[str]] = {
    "Sitrak": ["C7H", "G7", "G7S"],
    "Shacman": ["X3000", "X5000", "F3000", "H3000"],
    "Scania": ["R500", "S730", "G410", "P280", "R450"],
    "МАЗ": ["5440", "6430", "6501", "5550"],
    "MAN": ["TGX", "TGS", "TGM", "TGL"],
    "DAF": ["XF", "XG", "XG+", "CF", "LF"],
    "Volvo": ["FH", "FH16", "FM", "FMX", "FE"],
    "Mercedes-Benz": ["Actros", "Arocs", "Atego", "Axor"],
    "Howo": ["A7", "T5G", "T7H", "ZZ4257"],
    "КАМАЗ": ["5490", "65115", "65201", "43118"],
    "Урал": ["4320", "63685", "Next"],
    "ГАЗ": ["ГАЗон NEXT", "ГАЗель NEXT", "Валдай NEXT"],
    "FAW": ["J6P", "J7", "Tiger V"],
    "SAIC": ["Hongyan C6", "Hongyan Genlyon"],
    "Iveco": ["S-Way", "Eurocargo", "Daily", "T-Way"],
    "Renault": ["T High", "T", "C", "D", "D Wide"],
    "Dongfeng": ["KX", "KR", "KL"],
}

COLOURS = [
    "Белый", "Чёрный", "Серый", "Серебристый", "Синий", "Голубой",
    "Красный", "Бордовый", "Зелёный", "Жёлтый", "Оранжевый",
    "Коричневый", "Бежевый", "Фиолетовый",
]

REGIONS_AND_CITIES: dict[str, list[str]] = {
    "Брестская": ["Брест", "Барановичи", "Пинск", "Кобрин"],
    "Витебская": ["Витебск", "Орша", "Новополоцк", "Полоцк"],
    "Гомельская": ["Гомель", "Мозырь", "Жлобин", "Светлогорск", "Речица", "Калинковичи"],
    "Гродненская": ["Гродно", "Лида", "Волковыск", "Слоним", "Новогрудок"],
    "Минская": ["Минск", "Борисов", "Солигорск", "Молодечно", "Жодино", "Слуцк", "Дзержинск"],
    "Могилёвская": ["Могилёв", "Бобруйск", "Осиповичи", "Горки"],
}


async def seed_reference_data(db: AsyncSession):
    """Заполняет справочники, если они пусты."""
    existing_brands = (await db.execute(select(VehicleBrand))).scalars().first()
    if not existing_brands:
        for brand_name, models in BRANDS_AND_MODELS.items():
            brand = VehicleBrand(name=brand_name)
            db.add(brand)
            await db.flush()
            for model_name in models:
                db.add(VehicleModel(brand_id=brand.id, name=model_name))

    existing_colours = (await db.execute(select(Colour))).scalars().first()
    if not existing_colours:
        for c in COLOURS:
            db.add(Colour(name=c))

    existing_regions = (await db.execute(select(Region))).scalars().first()
    if not existing_regions:
        for region_name, cities in REGIONS_AND_CITIES.items():
            region = Region(name=region_name)
            db.add(region)
            await db.flush()
            for city_name in cities:
                db.add(City(region_id=region.id, name=city_name))

    await db.commit()


async def seed_app_settings(db: AsyncSession):
    """Создаёт строку настроек с НДС по умолчанию из конфига, если её ещё нет."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    if result.scalar_one_or_none():
        return
    db.add(AppSettings(id=1, vat_rate_percent=settings.VAT_RATE_PERCENT))
    await db.commit()


async def seed_admin(db: AsyncSession):
    """Создаёт администратора admin/admin, если его ещё нет."""
    result = await db.execute(select(User).where(User.login == "admin"))
    if result.scalar_one_or_none():
        return

    admin = User(
        login="admin",
        password_hash=hash_password("admin"),
        role=UserRole.ADMIN,
        user_type=UserType.INDIVIDUAL,
    )
    db.add(admin)
    await db.flush()
    db.add(Individual(user_id=admin.id, full_name="Администратор"))
    await db.commit()
