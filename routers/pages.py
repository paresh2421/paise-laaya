from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from database import engine
from models import Account, Category, Transaction

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# main function
@router.get("/")
def read_root(request: Request):
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        categories = session.exec(select(Category)).all()
        transactions = session.exec(
            select(Transaction).order_by(Transaction.id.desc()).limit(10)
        ).all()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "accounts": accounts,
                "categories": categories,
                "transactions": transactions,
                "today": datetime.now().strftime("%Y-%m-%dT%H:%M"),
                "current_month": datetime.now().strftime("%Y-%m"),
            },
        )

# Categories and accounts page
@router.get("/manage/")
def manage_page(request: Request):
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        categories = session.exec(select(Category)).all()

        return templates.TemplateResponse(
            request=request,
            name="manage.html",
            context={"accounts": accounts, "categories": categories},
        )

@router.get("/charts/")
def charts_page(request: Request):
    return templates.TemplateResponse(request=request, name="charts.html", context={})
