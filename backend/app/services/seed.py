"""Сидинг справочников/админа и отдельный full-seed для демо-данных."""

from datetime import date

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.app_settings import AppSettings
from app.models.chat import Chat, ChatParticipant, Message
from app.models.favorite import Favorite
from app.models.leasing import (
    Contract,
    LeaseRequest,
    Payment,
    PaymentSchedule,
    PurchaseContract,
    SupplierRequest,
)
from app.models.notification import Notification
from app.models.reference import City, Colour, Region, VehicleBrand, VehicleModel
from app.models.review import Review
from app.models.user import (
    BankAccount,
    Company,
    ContactType,
    Individual,
    LeaseTerm,
    User,
    UserContact,
    UserRole,
    UserType,
)
from app.models.vehicle import Vehicle, VehicleCondition, VehicleImage

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


FULL_SEED_TABLES = (
    "messages",
    "chat_participants",
    "chats",
    "notifications",
    "favorites",
    "reviews",
    "purchase_contracts",
    "payments",
    "payment_schedule",
    "contracts",
    "supplier_requests",
    "requests",
    "vehicle_images",
    "vehicles",
    "bank_accounts",
    "lease_terms",
    "user_contacts",
    "individuals",
    "entrepreneurs",
    "companies",
    "users",
    "app_settings",
    "cities",
    "regions",
    "vehicle_models",
    "vehicle_brands",
    "colours",
)


async def _truncate_for_full_seed(db: AsyncSession) -> None:
    tables_sql = ", ".join(FULL_SEED_TABLES)
    await db.execute(text(f"TRUNCATE TABLE {tables_sql} RESTART IDENTITY CASCADE"))
    await db.commit()


async def _create_demo_users(db: AsyncSession) -> tuple[User, User, User]:
    password_hash = hash_password("qqqqqq")

    supplier = User(
        login="supplier1",
        password_hash=password_hash,
        role=UserRole.SUPPLIER,
        user_type=UserType.COMPANY,
        description="Поставщик грузовой техники и самосвалов.",
    )
    lessor = User(
        login="lease_company",
        password_hash=password_hash,
        role=UserRole.LEASE_MANAGER,
        user_type=UserType.COMPANY,
        description="Лизинговая компания для корпоративных клиентов.",
    )
    lessee = User(
        login="test_user",
        password_hash=password_hash,
        role=UserRole.CLIENT,
        user_type=UserType.INDIVIDUAL,
        description="Покупатель техники через лизинг.",
    )
    db.add_all([supplier, lessor, lessee])
    await db.flush()

    db.add_all(
        [
            Company(
                user_id=supplier.id,
                company_name="ГрузовичкОФФ",
                legal_form="ООО",
                unp="193456781",
                okpo="102938475601",
                legal_address="220030, г. Минск, ул. Кальварийская, 27",
                postal_address="220030, г. Минск, а/я 112",
                director_name="Кузнецов Игорь Павлович",
            ),
            Company(
                user_id=lessor.id,
                company_name="АстраЛизинг",
                legal_form="ОАО",
                unp="192345678",
                okpo="564738291045",
                legal_address="220004, г. Минск, пр-т Победителей, 51/2",
                postal_address="220004, г. Минск, пр-т Победителей, 51/2",
                director_name="Астапенко Сергей Николаевич",
            ),
            Individual(
                user_id=lessee.id,
                full_name="Чернецов Владимир Андреевич",
                passport_id="MC",
                passport_number="1234567",
                issued_by="Октябрьский РУВД г. Минска",
                issue_date=date(2019, 6, 14),
                expiry_date=date(2029, 6, 14),
                registration_address="220116, г. Минск, ул. Есенина, 74-15",
            ),
        ]
    )

    db.add_all(
        [
            UserContact(user_id=supplier.id, type=ContactType.PHONE, value="+375291110001", is_primary=True),
            UserContact(user_id=supplier.id, type=ContactType.EMAIL, value="sales@gruzovichkoff.by", is_primary=False),
            UserContact(user_id=lessor.id, type=ContactType.PHONE, value="+375291110002", is_primary=True),
            UserContact(user_id=lessor.id, type=ContactType.EMAIL, value="leasing@astralizing.by", is_primary=False),
            UserContact(user_id=lessee.id, type=ContactType.PHONE, value="+375291110003", is_primary=True),
            UserContact(user_id=lessee.id, type=ContactType.EMAIL, value="chernetsov.va@mail.by", is_primary=False),
        ]
    )

    db.add_all(
        [
            BankAccount(
                user_id=supplier.id,
                iban="BY40ALFA30120000000100000000",
                bank_name='ЗАО "Альфа-Банк"',
                bank_address="г. Минск, ул. Сурганова, 43",
                swift="ALFABY2X",
            ),
            BankAccount(
                user_id=lessor.id,
                iban="BY53BLBB30120000000200000000",
                bank_name='ОАО "Белинвестбанк"',
                bank_address="г. Минск, пр-т Машерова, 29",
                swift="BLBBBY2X",
            ),
            BankAccount(
                user_id=lessee.id,
                iban="BY89BPSB30120000000300000000",
                bank_name='ОАО "БПС-Сбербанк"',
                bank_address="г. Минск, б-р Мулявина, 6",
                swift="BPSBBY2X",
            ),
        ]
    )

    db.add(
        LeaseTerm(
            user_id=lessor.id,
            min_term_months=12,
            max_term_months=60,
            min_prepayment_pct=15.0,
            max_prepayment_pct=45.0,
            min_asset_price=100000.0,
            max_asset_price=900000.0,
            interest_rate=13.5,
        )
    )

    await db.flush()
    return supplier, lessor, lessee


async def _create_demo_vehicles(db: AsyncSession, supplier: User) -> list[Vehicle]:
    vehicles = [
        Vehicle(
            supplier_id=supplier.id,
            name="Dongfeng KC 6х4 - DFH3250",
            brand="Dongfenf",
            model="KC",
            vehicle_type="Самосвал",
            condition=VehicleCondition.NEW,
            price=400000,
            count=2,
            release_year=2025,
            mileage=0,
            colour="Белый",
            location="г. Минск",
            transmission="Механическая",
            drive_type="6x4",
            fuel_type="Дизель",
            hp=450,
            description="Новый самосвал для карьерных и строительных работ.",
            is_visible=True,
        ),
        Vehicle(
            supplier_id=supplier.id,
            name="Shacman X3000 6x4 SX3258",
            brand="Shacman",
            model="X3000",
            vehicle_type="Самосвал",
            condition=VehicleCondition.NEW,
            price=365000,
            count=1,
            release_year=2025,
            mileage=0,
            colour="Красный",
            location="г. Гомель",
            transmission="Механическая",
            drive_type="6x4",
            fuel_type="Дизель",
            hp=430,
            description="Надежный самосвал для региональных стройплощадок.",
            is_visible=True,
        ),
    ]
    db.add_all(vehicles)
    await db.flush()

    return vehicles


async def reset_and_seed_demo_data(db: AsyncSession) -> dict[str, int]:
    """Полностью очищает БД и заполняет демо-набором сущностей."""
    await _truncate_for_full_seed(db)
    await seed_reference_data(db)
    await seed_app_settings(db)
    await seed_admin(db)

    supplier, lessor, lessee = await _create_demo_users(db)
    vehicles = await _create_demo_vehicles(db, supplier)
    await db.commit()

    stats = {
        "supplier_id": supplier.id,
        "lessor_id": lessor.id,
        "lessee_id": lessee.id,
        "vehicles_count": len(vehicles),
    }

    counts = [
        User,
        Company,
        Individual,
        BankAccount,
        UserContact,
        LeaseTerm,
        Vehicle,
        VehicleImage,
        LeaseRequest,
        SupplierRequest,
        Contract,
        PaymentSchedule,
        Payment,
        PurchaseContract,
        Chat,
        ChatParticipant,
        Message,
        Notification,
        Favorite,
        Review,
    ]
    for model in counts:
        result = await db.execute(select(func.count()).select_from(model))
        stats[f"{model.__tablename__}_count"] = int(result.scalar_one())
    return stats
