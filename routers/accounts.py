from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from database import engine
from models import Account, Category

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/accounts/")
def create_account(account: Account):
    with Session(engine) as session:
        session.add(account)
        session.commit()
        session.refresh(account)
        return account


@router.post("/categories/")
def create_category(category: Category):
    with Session(engine) as session:
        session.add(category)
        session.commit()
        session.refresh(category)
        return category


@router.get("/accounts/")
def get_accounts():
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        return accounts


@router.get("/categories/")
def get_categories():
    with Session(engine) as session:
        categories = session.exec(select(Category)).all()
        return categories


@router.get("/balances/")
def get_balances(request: Request):
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        return templates.TemplateResponse(
            request=request,
            name="partials/balance_card.html",
            context={"accounts": accounts},
        )


@router.post("/add_account/")
def add_account(name: str = Form(...), balance: float = Form(0.0)):
    with Session(engine) as session:
        new_account = Account(name=name, balance=balance)
        session.add(new_account)
        session.commit()
        return RedirectResponse(url="/manage/", status_code=303)


@router.post("/add_category/")
def add_category(name: str = Form(...)):
    with Session(engine) as session:
        new_category = Category(name=name)
        session.add(new_category)
        session.commit()
        return RedirectResponse(url="/manage/", status_code=303)
