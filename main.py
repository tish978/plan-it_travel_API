from fastapi import FastAPI
import connection
from bson import ObjectId
from schematics.models import Model
import pymongo

from database import db

app = FastAPI()
database = db['plan-it_travel']


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/test")
async def list_users():

    col = database['users']

    user_list = []
    for x in col.find({}, {}):
        user_list.append(x)

    print(user_list)

    return "Success"


@app.post("/sign-up")
def sign_up(username: str, password: str):
    collection = database['users']

    existing_user = collection.find_one({"username": username})
    if existing_user:
        return {"message": "Username already exists"}

    # Create a document to insert
    user_doc = {
        "username": username,
        "password": password
    }

    collection.insert_one(user_doc)

    return {"message": "User created successfully."}

@app.post("/login")
def login(username: str, password: str):
    collection = database['users']

    existing_user = collection.find_one({"username": username, "password": password})
    if existing_user:
        return {"message": "Successful login!"}
    else:
        return{"message": "ERROR: Username or Password is not correct."}
