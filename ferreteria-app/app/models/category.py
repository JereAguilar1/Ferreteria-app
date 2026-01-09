"""Category model."""
from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    """Product Category."""
    
    __tablename__ = 'category'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

