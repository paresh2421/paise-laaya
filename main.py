from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from database import create_db_and_tables, engine
from models import Category, Account
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates

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
        return templates.TemplateResponse(
            request=request, name="dashboard.html",context={"accounts":accounts, "categories":categories} 
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