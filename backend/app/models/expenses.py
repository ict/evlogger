import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.helpers import DbIdMixin


class ExpenseCategory(str, Enum):
    insurance = 'insurance'
    tax = 'tax'
    tires = 'tires'
    tolls_parking = 'tolls_parking'
    cleaning = 'cleaning'
    maintenance = 'maintenance'
    accessories = 'accessories'
    subscriptions = 'subscriptions'
    other = 'other'


class ExpenseKind(str, Enum):
    expense = 'expense'
    income = 'income'  # money back, e.g. selling old tires or a refund; reduces cost of ownership


class Expense(BaseModel):
    date: datetime.datetime
    car_id: str
    car_name: str | None = None
    category: ExpenseCategory
    kind: ExpenseKind = ExpenseKind.expense
    amount: int = Field(..., gt=0, description='Amount in 1/100s of currency (e.g. cents)')
    note: str | None = None


class ExpenseInDb(Expense, DbIdMixin):
    owner_id: str
