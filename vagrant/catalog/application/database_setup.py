import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    image = Column(String(250))
    active = Column(Integer)


class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    text = Column(String(500))
    category_id = Column("category_id", Integer, ForeignKey('categories.id'))
    user_id = Column("user_id", Integer, ForeignKey('users.id'))


class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)

# Seed Categories
engine.execute("""
	DELETE FROM Categories where 1 = 1;
""")
engine.execute("""
    INSERT INTO Categories (name) values
        ("Music"),
        ("Sports"),
        ("Entertainment"),
        ("Dining"),
        ("Funny")
""")
