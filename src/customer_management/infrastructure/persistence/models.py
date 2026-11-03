from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Text, text
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SubscriberModel(Base):
    __tablename__ = "subscribers"
    __table_args__ = (
        UniqueConstraint(
            "document_type",
            "document_number",
            name="uq_subscribers_document_identity",
        ),
        CheckConstraint(
            "document_type IN ('NATIONAL_ID', 'PASSPORT')",
            name="ck_subscribers_document_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    document_number: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    citizenship: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    accounts: Mapped[list["SubscriberAccountModel"]] = relationship(
        back_populates="subscriber",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by=lambda: (
            SubscriberAccountModel.created_at,
            SubscriberAccountModel.id,
        ),
    )


class SubscriberAccountModel(Base):
    __tablename__ = "subscriber_accounts"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_code",
            name="uq_subscriber_accounts_subscriber_code",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'TERMINATED')",
            name="ck_subscriber_accounts_status",
        ),
        CheckConstraint(
            "(status = 'ACTIVE' AND terminated_at IS NULL) OR "
            "(status = 'TERMINATED' AND terminated_at IS NOT NULL)",
            name="ck_subscriber_accounts_termination_state",
        ),
        Index(
            "uq_subscriber_accounts_active_service_address",
            "service_address_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
        Index("ix_subscriber_accounts_subscriber_id", "subscriber_id"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    subscriber_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscriber_code: Mapped[str] = mapped_column(Text, nullable=False)
    service_address_id: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    terminated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    subscriber: Mapped[SubscriberModel] = relationship(back_populates="accounts")

