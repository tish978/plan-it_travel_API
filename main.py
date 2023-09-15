from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bson import json_util, ObjectId
import json, datetime, pytz

from database import db

app = FastAPI()

# Mount the "static" directory as "/static" for serving static files
app.mount("/static", StaticFiles(directory="static"), name="static")

database = db['plan-it_travel']
templates = Jinja2Templates(directory="templates")

pst = pytz.timezone('US/Pacific')

@app.get("/")
async def root():
    return FileResponse("templates/login.html")

@app.get("/plan-trip", response_class=HTMLResponse)
async def plan_trip(request: Request):
    return templates.TemplateResponse("plan-trip.html", {"request": request})

@app.get("/generate-report", response_class=HTMLResponse)
async def generate_report(request: Request):
    return templates.TemplateResponse("make-report.html", {"request": request})

@app.post("/query", response_class=HTMLResponse)
async def query_destinations(request: Request, q1: list = Form(...), q2: list = Form(...), q3: list = Form(...)):

    collection = database['destinations']
    reports_collection = database['reports']
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

    # Perform query to create reports collection entry
    try:
        results = list(collection.find(query))
        location_ids = []  # List to store _ids
        for result in results:
            _id = result.pop('_id', None)  # Remove the _id field from the result dictionary
            if _id:
                location_ids.append(str(_id))  # Convert ObjectId to string and store in the list

        # Create a new entry in the reports collection
        current_time_pst = datetime.datetime.now(pst)
        current_time_pst = current_time_pst.strftime('%Y-%m-%d %H:%M:%S')
        new_report = {'user_id': curr_userID,'location_ids': location_ids, 'timestamp': current_time_pst}
        reports_collection.insert_one(new_report)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error querying the database")




    # Perform the query for output on page
    try:
        results = list(collection.find(query))

        # Convert and return each individual result as separate JSON responses
        response_list = []
        for result in results:
            stripped_result = json.loads(json_util.dumps(result))
            response_list.append(stripped_result)
        return templates.TemplateResponse("plan-trip-results.html", {"request": request, "results": response_list})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error querying the database")



@app.post("/make-report")
async def make_report(request: Request):
    reports_collection = database['reports']
    destination_collection = database['destinations']

    query = {
        "user_id": curr_userID
    }

    # Debugging: Log constructed query
    print("Query:", query)

    try:
        results = list(reports_collection.find(query))
        response_list = []

        for result in results:
            stripped_result = json.loads(json_util.dumps(result))

            # Extract location_ids from the result
            location_ids = stripped_result.get("location_ids", [])

            # Retrieve location_name for each location_id
            locations_info = []
            location_ids_oid = [ObjectId(location_id) for location_id in location_ids]

            for location_id in location_ids_oid:
                location_query = {
                    "_id": location_id
                }

                print("location_query: ", location_query)

                location_name_results = list(destination_collection.find(location_query))
                location_name = [result['location_name'] for result in location_name_results]

                location_name_str = ", ".join([str(item) for item in location_name])

                print("location: " + str(location_name_str))
                locations_info.append(str(location_name_str))

            stripped_result["locations_info"] = locations_info
            print(stripped_result)
            response_list.append(stripped_result)

        return templates.TemplateResponse("report-results.html", {"request": request, "results": response_list})
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
        global curr_userID
        curr_userID = existing_user['_id']
        print(f"The _id value of the curr_userID is: {curr_userID}")
        print({"message": "Successful login!"})
        return RedirectResponse(url="/home")
    else:
        print({"message": "ERROR: Username or Password is not correct."})
        return HTMLResponse(content="Invalid username or password", status_code=401)