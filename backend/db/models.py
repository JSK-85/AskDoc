from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum, func
from datetime import datetime, timezone
import enum


class Base(DeclarativeBase):
    pass


class DocStatus(str, enum.Enum):
    PENDING = 'pending'
    INGESTING = 'ingesting'
    DONE = 'done'
    FAILED = 'failed'


class Document(Base):
    __tablename__ = 'documents'

    id:           Mapped[int]       = mapped_column(Integer, primary_key=True)
    filename:     Mapped[str]       = mapped_column(String(255))
    status:       Mapped[DocStatus] = mapped_column(Enum(DocStatus), default=DocStatus.PENDING)
    total_chunks: Mapped[int]       = mapped_column(Integer, default=0)
    file_path:    Mapped[str | None] = mapped_column(String(512), nullable=True)
    pinned:       Mapped[bool]      = mapped_column(default=False)
    summary:      Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at:   Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    chunks: Mapped[list['Chunk']]   = relationship(back_populates='document', cascade='all, delete')


class Chunk(Base):
    __tablename__ = 'chunks'

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey('documents.id'))
    faiss_idx:   Mapped[int] = mapped_column(Integer)    # position in the FAISS flat index
    chunk_index: Mapped[int] = mapped_column(Integer)    # 0-based order within document
    page_number: Mapped[int] = mapped_column(Integer)
    text:        Mapped[str] = mapped_column(Text)
    document:    Mapped['Document'] = relationship(back_populates='chunks')


class QueryLog(Base):
    __tablename__ = 'query_logs'

    id:          Mapped[int]        = mapped_column(Integer, primary_key=True)
    question:    Mapped[str]        = mapped_column(Text)
    answer:      Mapped[str]        = mapped_column(Text)
    latency_ms:  Mapped[int]        = mapped_column(Integer)
    created_at:  Mapped[datetime]   = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    feedback:    Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'thumbs_up', 'thumbs_down', or None
