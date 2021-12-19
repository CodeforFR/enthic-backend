from sqlalchemy import Column, Float, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Bundle(Base):

    __tablename__ = "bundle"

    siren = Column(type_=Integer, nullable=False, primary_key=True)
    declaration = Column(type_=Integer, nullable=False, primary_key=True)
    accountability = Column(type_=Integer, nullable=False, primary_key=True)
    bundle = Column(type_=Integer, nullable=False, primary_key=True)
    amount = Column(type_=Float, nullable=False)
