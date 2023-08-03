from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bson import json_util


from database import db

app = FastAPI()

# Mount the "static" directory as "/static" for serving static files
app.mount("/static", StaticFiles(directory="static"), name="static")

database = db['plan-it_travel']
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return FileResponse("templates/login.html")

@app.get("/plan-trip", response_class=HTMLResponse)
async def plan_trip(request: Request):
    return templates.TemplateResponse("plan-trip.html", {"request": request})

@app.post("/query", response_class=JSONResponse)
async def query_destinations(q1: list = Form(...), q2: list = Form(...), q3: list = Form(...)):

    collection = database['destinations']
    # Debugging: Log form input values
    print("q1:", q1)
    print("q2:", q2)
    print("q3:", q3)

    # Convert q2 to a list of integers
    q2_int = [int(value) for value in q2]

    # Build the MongoDB query based on the form input
    query = {
        "continent": {"$in": q1},
        "weather": {"$in": q2_int},
        "language": {"$in": q3},
    }

    # Debugging: Log constructed query
    print("Query:", query)

    # Perform the query
    try:
        results = list(collection.find(query))
        new_results = json_util.dumps(results)
        print(new_results)
        return {"results": new_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error querying the database")

@app.get("/plan-trip-p2")
def plan_trip_p2():
    return FileResponse("templates/plan-trip-p2.html")

@app.get('/plan-trip-p3')
def plan_trip_p3():
    return FileResponse("templates/plan-trip-p3.html")


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
