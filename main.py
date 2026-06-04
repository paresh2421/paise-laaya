from fastapi import FastAPI, Request, Form, Response
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import create_db_and_tables, engine
from models import Category, Account, Transaction
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import datetime
from calendar import monthrange
from routers import pages, accounts, transactions

# lifespan function which runs before server takes requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to the Database...")
    create_db_and_tables()
    yield
    print("Safely shutting down...")


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
