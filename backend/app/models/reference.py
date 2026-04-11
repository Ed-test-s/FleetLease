from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VehicleBrand(Base):
    __tablename__ = "vehicle_brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    models: Mapped[list["VehicleModel"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan", order_by="VehicleModel.name"
    )


class VehicleModel(Base):
    __tablename__ = "vehicle_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("vehicle_brands.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    brand: Mapped["VehicleBrand"] = relationship(back_populates="models")


class Colour(Base):
    __tablename__ = "colours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    cities: Mapped[list["City"]] = relationship(
        back_populates="region", cascade="all, delete-orphan", order_by="City.name"
    )


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    region: Mapped["Region"] = relationship(back_populates="cities")
