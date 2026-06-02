from sqlmodel import SQLModel, Field
from datetime import datetime


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)  # bank name
    balance: float = Field(default=0.0)


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    amount: float
    type: str
    note: str | None = None
    transaction_date: datetime = Field(default_factory=datetime.now)

    # foreign keys to account and category table
    account_id: int | None = Field(default=None, foreign_key="account.id")
    category_id: int | None = Field(default=None, foreign_key="category.id")
