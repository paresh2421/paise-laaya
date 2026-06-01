from fastapi import FastAPI, Request, Form
from contextlib import asynccontextmanager
from database import create_db_and_tables, engine
from models import Category, Account, Transaction
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import date

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to the Database...")
    create_db_and_tables()
    yield
    print("Safely shutting down...")

app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root(request: Request):
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        categories = session.exec(select(Category)).all()
        transactions = session.exec(select(Transaction).order_by(Transaction.id.desc()))
        return templates.TemplateResponse(
            request=request, 
            name="dashboard.html",
            context={
                "accounts":accounts, 
                "categories":categories, 
                "transactions":transactions,
                "today":date.today()
                }
        )

@app.post("/accounts/")
def create_account(account: Account):
    with Session(engine) as session:
        session.add(account)
        session.commit()
        session.refresh(account)
        return account

@app.post("/categories/")
def create_category(category: Category):
    with Session(engine) as session:
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    
@app.get("/accounts/")
def get_accounts():
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        return accounts

@app.get("/categories/")
def get_categories():
    with Session(engine) as session:
        categories = session.exec(select(Category)).all()
        return categories

@app.post("/add_transaction/")
def add_transaction(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    account_id: int = Form(...),
    category_id: int = Form(...),
    transaction_date: date = Form(...),
    note: str = Form(None),

):
    with Session(engine) as session:
        new_transaction = Transaction(
            type=type,
            amount=amount,
            account_id=account_id,
            category_id=category_id,
            transaction_date=transaction_date,
            note=note
        )

        session.add(new_transaction)

        account = session.get(Account, account_id)

        if type == "income":
            account.balance += amount
        elif type == "expense":
            account.balance -= amount

        session.add(account)

        session.commit()

        html_response = templates.TemplateResponse(
            request=request,
            name="partials/transaction_row.html",
            context={"tx": new_transaction}
        )
        
        # 2. Fire the invisible flare!
        html_response.headers["HX-Trigger"] = "update-balances"
        
        return html_response
    
@app.get("/balances/")
def get_balances(request: Request):
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        return templates.TemplateResponse(
            request=request,
            name="partials/balance_card.html",
            context={"accounts": accounts}
        )
        
# --- MANAGEMENT PORTAL ROUTES ---

@app.get("/manage/")
def manage_page(request: Request):
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        categories = session.exec(select(Category)).all()
        
        return templates.TemplateResponse(
            request=request, 
            name="manage.html", 
            context={"accounts": accounts, "categories": categories}
        )

@app.post("/add_account/")
def add_account(name: str = Form(...), balance: float = Form(0.0)):
    with Session(engine) as session:
        new_account = Account(name=name, balance=balance)
        session.add(new_account)
        session.commit()
        return RedirectResponse(url="/manage/", status_code=303)

@app.post("/add_category/")
def add_category(name: str = Form(...)):
    with Session(engine) as session:
        new_category = Category(name=name)
        session.add(new_category)
        session.commit()
        return RedirectResponse(url="/manage/", status_code=303)