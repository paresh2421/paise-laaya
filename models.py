from sqlmodel import SQLModel, Field
from datetime import date

class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True) #bank name
    balance: float = Field(default=0.0)

class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    amount: float
    type: str
    note: str
    transaction_date: date = Field(default_factory=date.today)

    #foreign keys to account and category table
    account_id: int | None = Field(default=None, foreign_key="account.id")
    category_id: int | None = Field(default=None, foreign_key="category.id")
