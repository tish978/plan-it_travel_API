from fastapi import FastAPI
import connection
from bson import ObjectId
from schematics.models import Model
import pymongo

from database import db

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/test")
async def list_users():
    database = db['plan-it_travel']
    col = database['users']

    user_list = []
    for x in col.find({}, {}):
        user_list.append(x)

    print(user_list)

    return "Success"


