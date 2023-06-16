from fastapi import FastAPI
import connection
from bson import ObjectId
from schematics.models import Model

from database import db

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/test")
async def list_students():
    database = db['sample_airbnb']
    collections = database.list_collection_names()
    return collections


