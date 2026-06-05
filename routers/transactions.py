from fastapi import APIRouter, Request, Form, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from calendar import monthrange
from database import engine
from models import Transaction, Account, Category

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/add_transaction/")
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


@router.delete("/delete_transaction/{tx_id}")
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


@router.get("/edit_transaction_form/{tx_id}")
def get_edit_form(tx_id: int, request: Request):
    with Session(engine) as session:
        tx = session.get(Transaction, tx_id)
        return templates.TemplateResponse(
            request=request,
            name="partials/transaction_edit_row.html",
            context={"tx": tx},
        )


@router.get("/cancel_edit/{tx_id}")
def cancel_edit(tx_id: int, request: Request):
    with Session(engine) as session:
        tx = session.get(Transaction, tx_id)
        return templates.TemplateResponse(
            request=request, name="partials/transaction_row.html", context={"tx": tx}
        )


@router.post("/update_transaction/{tx_id}")
def update_transaction(
    tx_id: int,
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    account_id: int = Form(...),
    category_id: int = Form(...),
    transaction_date: datetime = Form(...),
    note: str = Form(None),
):
    with Session(engine) as session:
        tx = session.get(Transaction, tx_id)
        account = session.get(Account, tx.account_id)

        # 1. UNDO the old math
        if tx.type == "income":
            account.balance -= tx.amount
        elif tx.type == "expense":
            account.balance += tx.amount

        # 2. UPDATE the transaction data
        tx.type = type
        tx.amount = amount
        tx.transaction_date = transaction_date
        tx.note = note

        # 3. APPLY the new math
        if tx.type == "income":
            account.balance += tx.amount
        elif tx.type == "expense":
            account.balance -= tx.amount

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

@router.get("/api/expenses-by-category")
def expenses_by_category(month: str = None):
    with Session(engine) as session:
        query = select(Transaction).where(Transaction.type == "expense")
        
        # 1. Apply the Month Filter if provided
        if month:
            year_num, month_num = map(int, month.split("-"))
        else:
            now = datetime.now()
            year_num, month_num = now.year, now.month
            
        start_date = datetime(year_num, month_num, 1)
        last_day = monthrange(year_num, month_num)[1]
        end_date = datetime(year_num, month_num, last_day, 23, 59, 59)
        
        query = query.where(Transaction.transaction_date >= start_date)
        query = query.where(Transaction.transaction_date <= end_date)
        
        # 2. Fetch and group the data
        expenses = session.exec(query).all()
        categories = session.exec(select(Category)).all()
        cat_map = {c.id: c.name for c in categories}
        
        data = {}
        for exp in expenses:
            c_name = cat_map.get(exp.category_id, "Uncategorized")
            data[c_name] = data.get(c_name, 0) + exp.amount
            
        return {"labels": list(data.keys()), "values": list(data.values())}


# --- FILTER ROUTE ---


@router.get("/filter_transactions/")
def filter_transactions(request: Request, month: str = None):
    with Session(engine) as session:
        # Start with a base query
        query = select(Transaction).order_by(Transaction.id.desc())

        # If the user selected a month, apply the boundaries!
        if month:
            # Parse the "YYYY-MM" string from the HTML input
            year_num, month_num = map(int, month.split("-"))

            # Find the very first and very last second of that month
            start_date = datetime(year_num, month_num, 1)
            last_day = monthrange(year_num, month_num)[1]
            end_date = datetime(year_num, month_num, last_day, 23, 59, 59)

            # Apply the filter to the database query
            query = query.where(Transaction.transaction_date >= start_date)
            query = query.where(Transaction.transaction_date <= end_date)

        # Execute the query and return ONLY the tiny list partial
        filtered_txs = session.exec(query).all()

        return templates.TemplateResponse(
            request=request,
            name="partials/transaction_list.html",
            context={"transactions": filtered_txs},
        )
