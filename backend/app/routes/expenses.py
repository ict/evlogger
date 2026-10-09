from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from app.core.db import AsyncIOMotorClient, get_database
from app.models.expenses import Expense, ExpenseCategory, ExpenseInDb, ExpenseKind
from app.models.users import UserInDb
from app.operations.expenses import ExpenseCrudOp
from app.util.auth import get_current_active_user

router = APIRouter()

DBDepend = Depends(get_database)
UserDepends = Depends(get_current_active_user)


@router.get('/')
async def list_expenses(
    limit: int = 100,
    offset: int = 0,
    car_id: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    category: ExpenseCategory | None = None,
    kind: ExpenseKind | None = None,
    db: AsyncIOMotorClient = DBDepend,
    user: UserInDb = UserDepends,
) -> list[ExpenseInDb]:
    return await ExpenseCrudOp.list(db, limit, offset, user.id, from_date, to_date, car_id, category, kind)


@router.post('/', status_code=HTTP_201_CREATED)
async def create_expense(
    expense: Expense, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> ExpenseInDb:
    try:
        return await ExpenseCrudOp.create(db, expense, user.id)
    except ValueError as err:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(err)) from None


@router.get('/{id}')
async def get_expense_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends) -> ExpenseInDb:
    expense = await ExpenseCrudOp.get_by_id(db, id, user.id)
    if not expense:
        raise HTTPException(404, 'Not found')
    return expense


@router.delete('/{id}', status_code=HTTP_204_NO_CONTENT)
async def delete_expense_by_id(id: str, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends):
    success = await ExpenseCrudOp.delete_by_id(db, id, user.id)
    if not success:
        raise HTTPException(404, 'Not found')


@router.put('/{id}')
async def update_expense_by_id(
    id: str, expense: Expense, db: AsyncIOMotorClient = DBDepend, user: UserInDb = UserDepends
) -> ExpenseInDb:
    try:
        new_expense = await ExpenseCrudOp.update_by_id(db, id, expense, user.id)
    except ValueError as err:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(err)) from None
    if not new_expense:
        raise HTTPException(404, 'Not found')
    return new_expense
