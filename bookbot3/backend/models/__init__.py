"""
Database models for BookBot application.

This module contains all SQLAlchemy models for the BookBot database.
The design uses JSON props fields for flexibility and future extensibility.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid
import json
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import tuple_

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

db = SQLAlchemy()


def utcnow():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class User(db.Model):
    """User model for storing user information."""
    
    __tablename__ = 'users'
    
    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    props = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            'user_id': self.user_id,
            'props': self.props,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def id(self):
        """Alias for user_id for test compatibility."""
        return self.user_id


class Book(db.Model):
    """Book model for storing book information."""
    
    __tablename__ = 'books'
    
    book_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    props = Column(JSON, nullable=False, default=dict)
    is_locked = Column(Boolean, default=False)
    job = Column(String(36), nullable=True)  # Remove ForeignKey to avoid circular reference
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    user = relationship("User", back_populates="books")
    chunks = relationship("Chunk", back_populates="book", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="book", cascade="all, delete-orphan", foreign_keys="Job.book_id")
    output_files = relationship("OutputFile", back_populates="book", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_book_user_id', 'user_id'),
    )
    
    def to_dict(self, include_stats: bool = False) -> Dict[str, Any]:
        """Convert book to dictionary."""
        result = {
            'book_id': self.book_id,
            'user_id': self.user_id,
            'props': self.props,
            'is_locked': self.is_locked,
            'job': self.job,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats:
            # Calculate book statistics
            latest_chunks = [c for c in self.chunks if c.is_latest and not c.is_deleted]
            result['chunk_count'] = len(latest_chunks)
            result['word_count'] = sum(c.word_count or 0 for c in latest_chunks)
        
        return result
    
    @property
    def id(self):
        """Alias for book_id for test compatibility."""
        return self.book_id


class Chunk(db.Model):
    """Chunk model for storing book content chunks with versioning."""
    
    __tablename__ = 'chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(String(36), ForeignKey('books.book_id'), nullable=False)
    chunk_id = Column(String(36), nullable=False, default=generate_uuid)
    version = Column(Integer, nullable=False, default=1)
    is_latest = Column(Boolean, default=True)
    props = Column(JSON, nullable=False, default=dict)
    text = Column(Text, nullable=True)
    type = Column(String(50), nullable=True)
    is_locked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    job = Column(String(36), nullable=True)  # Remove ForeignKey to avoid circular reference
    _order = Column('order', Float, nullable=True)
    chapter = Column(Integer, nullable=True)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    book = relationship("Book", back_populates="chunks")

    def __init__(self, **kwargs):
        # Handle 'order' parameter by mapping it to '_order'
        if 'order' in kwargs:
            kwargs['_order'] = kwargs.pop('order')
        super().__init__(**kwargs)
    
    # replace order with hybrid property for correct DB sorting
    @hybrid_property
    def order(self):
        return self._order

    @order.expression
    def order(cls):
        # Just return the order column for queries
        return cls._order

    @order.setter
    def order(self, value):
        self._order = value

    # Indexes
    __table_args__ = (
        Index('idx_chunk_book_id', 'book_id'),
        Index('idx_chunk_chunk_id', 'chunk_id'),
        Index('idx_chunk_is_latest', 'is_latest'),
        Index('idx_chunk_is_deleted', 'is_deleted'),
        Index('idx_chunk_chapter', 'chapter'),
    )
    
    def to_dict(self, include_text: bool = False) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        result = {
            'id': self.id,
            'book_id': self.book_id,
            'chunk_id': self.chunk_id,
            'version': self.version,
            'is_latest': self.is_latest,
            'props': self.props,
            'type': self.type,
            'is_locked': self.is_locked,
            'is_deleted': self.is_deleted,
            'job': self.job,
            'order': self.order,
            'chapter': self.chapter,
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_text:
            result['text'] = self.text
        
        return result
    
    @staticmethod
    def count_words(text: Optional[str]) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(text.split())


class OutputFile(db.Model):
    """OutputFile model for storing exported book files."""
    
    __tablename__ = 'output_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(String(36), ForeignKey('books.book_id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    props = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utcnow)
    
    # Relationships
    book = relationship("Book", back_populates="output_files")
    
    # Indexes
    __table_args__ = (
        Index('idx_output_file_book_id', 'book_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert output file to dictionary."""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'props': self.props,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Job(db.Model):
    """Job model for storing background job information."""
    
    __tablename__ = 'jobs'
    
    job_id = Column(String(36), primary_key=True, default=generate_uuid)
    book_id = Column(String(36), ForeignKey('books.book_id'), nullable=False)
    job_type = Column(String(50), nullable=False)
    props = Column(JSON, nullable=False, default=dict)
    state = Column(String(20), nullable=False, default='waiting')  # waiting, running, complete, error, cancelled
    created_at = Column(DateTime, default=utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    book = relationship("Book", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_book_id', 'book_id'),
        Index('idx_job_state', 'state'),
        Index('idx_job_type', 'job_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            'job_id': self.job_id,
            'book_id': self.book_id,
            'job_type': self.job_type,
            'props': self.props,
            'state': self.state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class JobLog(db.Model):
    """JobLog model for storing job execution logs."""
    
    __tablename__ = 'job_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey('jobs.job_id'), nullable=False)
    log_entry = Column(Text, nullable=False)
    log_level = Column(String(10), default='INFO')
    created_at = Column(DateTime, default=utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_log_job_id', 'job_id'),
        Index('idx_job_log_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job log to dictionary."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'log_entry': self.log_entry,
            'log_level': self.log_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
