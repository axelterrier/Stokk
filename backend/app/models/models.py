import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, Float, Integer, ForeignKey, DateTime, Date, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Product(Base):
    __tablename__ = "products"

    barcode: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(1000))
    image_url: Mapped[str | None] = mapped_column(String(1000))
    nutriscore: Mapped[str | None] = mapped_column(String(1))
    energy_kcal: Mapped[float | None] = mapped_column(Float)
    proteins_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    fat_g: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    stock_items: Mapped[list["StockItem"]] = relationship(back_populates="product")


class StockItem(Base):
    __tablename__ = "stock_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_barcode: Mapped[str] = mapped_column(String(30), ForeignKey("products.barcode"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="unité")
    location: Mapped[str | None] = mapped_column(String(100))
    opened: Mapped[bool] = mapped_column(Boolean, default=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="stock_items")
    expiry_date: Mapped["ExpiryDate | None"] = relationship(
    back_populates="stock_item",
    uselist=False,
    cascade="all, delete-orphan"
)


class ExpiryDate(Base):
    __tablename__ = "expiry_dates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stock_items.id"), unique=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    alert_days_before: Mapped[int] = mapped_column(Integer, default=3)
    alerted: Mapped[bool] = mapped_column(Boolean, default=False)

    stock_item: Mapped["StockItem"] = relationship(back_populates="expiry_date")
