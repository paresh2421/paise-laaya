from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from calendar import monthrange
from database import engine
from models import Account, Category, Transaction

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# 1. NEW HOME PAGE (Overview & Analytics)
@router.get("/")
def overview_page(request: Request):
    with Session(engine) as session:
        # Get current month boundaries
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        last_day = monthrange(now.year, now.month)[1]
        end_date = datetime(now.year, now.month, last_day, 23, 59, 59)

        # Fetch this month's transactions
        this_month_txs = session.exec(
            select(Transaction)
            .where(Transaction.transaction_date >= start_date)
            .where(Transaction.transaction_date <= end_date)
        ).all()

        # Calculate Insights (Cash Flow)
        total_income = sum(tx.amount for tx in this_month_txs if tx.type == "income")
        total_expense = sum(tx.amount for tx in this_month_txs if tx.type == "expense")
        net_flow = total_income - total_expense

        # Find top spending category
        category_spending = {}
        for tx in this_month_txs:
            if tx.type == "expense":
                category_spending[tx.category_id] = (
                    category_spending.get(tx.category_id, 0) + tx.amount
                )

        top_category_name = "None"
        top_category_amount = 0
        if category_spending:
            top_cat_id = max(category_spending, key=category_spending.get)
            top_category_amount = category_spending[top_cat_id]
            cat_record = session.get(Category, top_cat_id)
            if cat_record:
                top_category_name = cat_record.name

        return templates.TemplateResponse(
            request=request,
            name="overview.html",  # <-- Make sure to rename charts.html to overview.html!
            context={
                "total_income": total_income,
                "total_expense": total_expense,
                "net_flow": net_flow,
                "top_category_name": top_category_name,
                "top_category_amount": top_category_amount,
                "current_month_name": now.strftime("%B %Y"),
                "current_month_val": now.strftime("%Y-%m"),
                "min_month": f"{now.year - 5}-01",
                "max_month": f"{now.year + 1}-12",
            },
        )


# 2. OLD DASHBOARD (Now the Transactions page)
@router.get("/transactions/")
def transactions_page(request: Request):
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


# 3. MANAGE PAGE (Unchanged)
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


@router.get("/insights/")
def get_insights(request: Request, month: str = None):
    with Session(engine) as session:
        now = datetime.now()
    
        if month:
            year_num, month_num = map(int, month.split("-"))
        else:
            year_num, month_num = now.year, now.month

        start_date = datetime(year_num, month_num, 1)
        last_day = monthrange(year_num, month_num)[1]
        end_date = datetime(year_num, month_num, last_day, 23, 59, 59)

        this_month_txs = session.exec(
            select(Transaction)
            .where(Transaction.transaction_date >= start_date)
            .where(Transaction.transaction_date <= end_date)
        ).all()

        total_income = sum(tx.amount for tx in this_month_txs if tx.type == "income")
        total_expense = sum(tx.amount for tx in this_month_txs if tx.type == "expense")
        net_flow = total_income - total_expense

        category_spending = {}
        for tx in this_month_txs:
            if tx.type == "expense":
                category_spending[tx.category_id] = (
                    category_spending.get(tx.category_id, 0) + tx.amount
                )

        top_category_name = "None"
        top_category_amount = 0
        if category_spending:
            top_cat_id = max(category_spending, key=category_spending.get)
            top_category_amount = category_spending[top_cat_id]
            cat_record = session.get(Category, top_cat_id)
            if cat_record:
                top_category_name = cat_record.name

        return templates.TemplateResponse(
            request=request,
            name="partials/overview_content.html",
            context={
                "total_income": total_income,
                "total_expense": total_expense,
                "net_flow": net_flow,
                "top_category_name": top_category_name,
                "top_category_amount": top_category_amount,
                "current_month_name": start_date.strftime("%B %Y"),
                "current_month_val": start_date.strftime("%Y-%m"),
                "min_month": f"{now.year - 5}-01",
                "max_month": f"{now.year + 1}-12",
            },
        )
