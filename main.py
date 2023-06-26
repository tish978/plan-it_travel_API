from fastapi import FastAPI, Request
import connection
from bson import ObjectId
from schematics.models import Model
import pymongo
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import db

app = FastAPI()
database = db['plan-it_travel']
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/sign-up", response_class=HTMLResponse)
async def sign_up(request: Request):
    return templates.TemplateResponse("sign-up.html", {"request": request})


@app.post("/sign-up")
async def handle_sign_up(request: Request):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    # Check if username already exists
    collection = database['users']
    existing_user = collection.find_one({"username": username})
    if existing_user:
        return {"message": "Username already exists"}

    # Insert username and password into the collection
    collection.insert_one({"username": username, "password": password})
    return {"message": "User registered successfully"}


@app.post("/login")
def login(username: str, password: str):
    collection = database['users']

    existing_user = collection.find_one({"username": username, "password": password})
    if existing_user:
        return {"message": "Successful login!"}
    else:
        return{"message": "ERROR: Username or Password is not correct."}
