from fastapi import FastAPI, Request, Form, Response
from contextlib import asynccontextmanager
from database import create_db_and_tables, engine
from models import Category, Account, Transaction
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import datetime


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
                "accounts": accounts,
                "categories": categories,
                "transactions": transactions,
                "today": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            },
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
    transaction_date: datetime = Form(...),
    note: str = Form(None),
):
    with Session(engine) as session:
        new_transaction = Transaction(
            type=type,
            amount=amount,
            account_id=account_id,
            category_id=category_id,
            transaction_date=transaction_date,
            note=note,
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
            context={"tx": new_transaction},
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
            context={"accounts": accounts},
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
            context={"accounts": accounts, "categories": categories},
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


@app.delete("/delete_transaction/{tx_id}")
def delete_transaction(tx_id: int):
    with Session(engine) as session:
        tx = session.get(Transaction, tx_id)
        if not tx:
            return Response(status_code=404)

        account = session.get(Account, tx.account_id)
        if tx.type == "income":
            account.balance -= tx.amount
        elif tx.type == "expense":
            account.balance += tx.amount

        session.add(account)
        session.delete(tx)
        session.commit()

        response = Response(content="")
        response.headers["HX-Trigger"] = "update-balances"
        return response

# --- INLINE EDIT ROUTES ---

@app.get("/edit_transaction_form/{tx_id}")
def get_edit_form(tx_id: int, request: Request):
    with Session(engine) as session:
        tx = session.get(Transaction, tx_id)
        return templates.TemplateResponse(request=request, name="partials/transaction_edit_row.html", context={"tx": tx})

@app.get("/cancel_edit/{tx_id}")
def cancel_edit(tx_id: int, request: Request):
    with Session(engine) as session:
        tx = session.get(Transaction, tx_id)
        return templates.TemplateResponse(request=request, name="partials/transaction_row.html", context={"tx": tx})

@app.post("/update_transaction/{tx_id}")
def update_transaction(
    tx_id: int, request: Request,
    type: str = Form(...), amount: float = Form(...),
    account_id: int = Form(...), category_id: int = Form(...),
    transaction_date: datetime = Form(...), note: str = Form(None)
):
    with Session(engine) as session:
        tx = session.get(Transaction, tx_id)
        account = session.get(Account, tx.account_id)
        
        # 1. UNDO the old math
        if tx.type == "income": account.balance -= tx.amount
        elif tx.type == "expense": account.balance += tx.amount
            
        # 2. UPDATE the transaction data
        tx.type = type
        tx.amount = amount
        tx.transaction_date = transaction_date
        tx.note = note
        
        # 3. APPLY the new math
        if tx.type == "income": account.balance += tx.amount
        elif tx.type == "expense": account.balance -= tx.amount
            
        session.add(account)
        session.add(tx)
        session.commit()
        
        # 4. Return the standard read-only row, and fire the update-balances flare!
        html_response = templates.TemplateResponse(
            request=request, name="partials/transaction_row.html", context={"tx": tx}
        )
        html_response.headers["HX-Trigger"] = "update-balances"
        return html_response
    
# --- CHART DATA ROUTE ---

@app.get("/api/expenses-by-category")
def expenses_by_category():
    with Session(engine) as session:
        # 1. Get all expenses and all categories
        expenses = session.exec(select(Transaction).where(Transaction.type == "expense")).all()
        categories = session.exec(select(Category)).all()
        
        # 2. Map category IDs to their actual Names
        cat_map = {c.id: c.name for c in categories}
        
        # 3. Add up the amounts for each category
        data = {}
        for exp in expenses:
            c_name = cat_map.get(exp.category_id, "Uncategorized")
            data[c_name] = data.get(c_name, 0) + exp.amount
            
        # 4. Return it exactly how Chart.js expects it (Lists of labels and values)
        return {
            "labels": list(data.keys()), 
            "values": list(data.values())
        }