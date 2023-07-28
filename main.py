from fastapi import FastAPI, Request, Form
import connection
from bson import ObjectId
from schematics.models import Model
import pymongo
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles


from database import db

app = FastAPI()

# Mount the "static" directory as "/static" for serving static files
app.mount("/static", StaticFiles(directory="static"), name="static")

database = db['plan-it_travel']
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return FileResponse("templates/login.html")

@app.post("/home")
def home():
    #return HTMLResponse(content="Welcome to the Home page!")
    return FileResponse("templates/home.html")

@app.get("/sign-up", response_class=HTMLResponse)
async def sign_up(request: Request):
    return templates.TemplateResponse("sign-up.html", {"request": request})



@app.get("/my_endpoint")
def my_endpoint():
    return {"message": "Sign-out successful"}

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
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    collection = database['users']

    existing_user = collection.find_one({"username": username, "password": password})
    if existing_user:
        print({"message": "Successful login!"})
        return RedirectResponse(url="/home")
    else:
        print({"message": "ERROR: Username or Password is not correct."})
        return HTMLResponse(content="Invalid username or password", status_code=401)
