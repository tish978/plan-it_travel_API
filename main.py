# This File contains all the necessary server-side code for the application

import logging
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bson import json_util, ObjectId
from pydantic import BaseModel, ValidationError
from itertools import product
import json, datetime, pytz, os, sendgrid
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from database import db

app = FastAPI()

# Mount the "static" directory as "/static" for serving static files (such as images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Connect to database specified in database.py
database = db['plan-it_travel']

# Specify templates to be used for each HTML Web Page
templates = Jinja2Templates(directory="templates")

# Specify timezone for timestamps in Reports
pst = pytz.timezone('US/Pacific')

# Sendgrid API from env vars
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

# Endpoint used for sending emails on Contact Page
@app.post("/send_email")
async def send_email(request: Request, name: str = Form(...), email: str = Form(...), message: str = Form(...)):

    # Specify details for the email
    message = Mail(
        from_email=email,
        to_emails='satish.bisa@gmail.com',
        subject=name,
        html_content=message
    )

    # Try to send message but throw exception if not
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        print("message: Email Sent!")
        return RedirectResponse(url="/home")
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


# Endpoint to default to Login Page when opening application
@app.get("/")
async def root():
    return FileResponse("templates/login.html")


# Endpoint to go to Plan Trip page
@app.get("/plan-trip", response_class=HTMLResponse)
async def plan_trip(request: Request):
    return templates.TemplateResponse("plan-trip.html", {"request": request})


# Endpoint to go to Generate Reports page
@app.get("/generate-report", response_class=HTMLResponse)
async def generate_report(request: Request):
    return templates.TemplateResponse("make-report.html", {"request": request})


# Endpoint to query the database based on the end user's Plan Trip Survey answers
@app.post("/query", response_class=HTMLResponse)
async def query_destinations(request: Request, q1: list = Form(...), q2: list = Form(...), q3: list = Form(...),
                             q4: list = Form(...), q5: list = Form(...), q6: list = Form(...), q7: list = Form(...),
                             q8: list = Form(...), q9: list = Form(...)):
    collection = database['destinations']
    reports_collection = database['reports']

    # Convert q2 (weather) and q4 (budget) to a list of integers
    q2_int = [int(value) for value in q2]
    q4_int = [int(value) for value in q4]

    # Convert q6-q9 to a list of bool
    q6_bool = [bool(value) for value in q6]
    q7_bool = [bool(value) for value in q7]
    q8_bool = [bool(value) for value in q8]
    q9_bool = [bool(value) for value in q9]

    # Build the MongoDB query based on the form input
    query = {}

    # Add conditions to the query based on the presence of each input
    if q1:
        query["continent"] = {"$in": q1}
    if q2_int:
        query["weather"] = {"$in": q2_int}
    if q3:
        query["language"] = {"$in": q3}
    if q4_int:
        query["budget"] = {"$in": q4_int}
    if q5:
        query["cuisine"] = {"$in": q5}
    if q6_bool:
        query["family_friendly"] = {"$in": q6_bool}
    if q7_bool:
        query["group_friendly"] = {"$in": q7_bool}
    if q8_bool:
        query["party_scene"] = {"$in": q8_bool}
    if q9_bool:
        query["romantic"] = {"$in": q9_bool}

    # Try to query on each combination of Survey input to find the proper matching destinations in the DB
    try:
        # Create all possible combinations of selected values
        combinations = list(product(q1, q2_int, q3, q4_int, q5, q6_bool, q7_bool, q8_bool, q9_bool))

        # Store results for each combination
        all_results = {}

        for combo in combinations:
            # Construct a query for the current combination
            combo_query = {}

            if combo[0]:
                combo_query["continent"] = combo[0]
            if combo[1]:
                combo_query["weather"] = combo[1]
            if combo[2]:
                combo_query["language"] = combo[2]
            if combo[3]:
                combo_query["budget"] = combo[3]
            if combo[4]:
                combo_query["cuisine"] = combo[4]
            if combo[5]:
                combo_query["family_friendly"] = combo[5]
            if combo[6]:
                combo_query["group_friendly"] = combo[6]
            if combo[7]:
                combo_query["party_scene"] = combo[7]
            if combo[8]:
                combo_query["romantic"] = combo[8]

            # Perform the query
            results = list(collection.find(combo_query))

            # Store results for the current combination
            all_results[combo] = results

            # Debugging: Log the results for the current combination
            print(f"Results for combination {combo}:")
            for result in results:
                print(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error querying the DB")

    # Try to perform query to create Reports collection entry in DB (a report needs to be made based on the recommended
    # destinations from this current Survey input, so that it can be used for when the end user wants to
    # Generate Reports in the future)
    try:
        results = list(collection.find(query))
        # List to store _ids
        location_ids = []
        for result in results:
            # Remove the _id field from the result dictionary
            _id = result.pop('_id', None)
            if _id:
                # Convert ObjectId to string and store in the list
                location_ids.append(str(_id))

        # Create a new entry in the reports collection
        current_time_pst = datetime.datetime.now(pst)
        current_time_pst = current_time_pst.strftime('%Y-%m-%d %H:%M:%S')
        new_report = {'user_id': curr_userID, 'location_ids': location_ids, 'timestamp': current_time_pst}
        reports_collection.insert_one(new_report)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error querying the database")

    # Try to perform the query for output on Plan Trip Results page
    try:
        results = list(collection.find(query))
        print("Results: " + str(results))
        if not results:
            return templates.TemplateResponse("plan-trip-results-error.html", {"request": request})

        # Convert and return each individual result as separate JSON responses
        response_list = []
        for result in results:
            stripped_result = json.loads(json_util.dumps(result))
            response_list.append(stripped_result)
        return templates.TemplateResponse("plan-trip-results.html", {"request": request, "results": response_list})
    except Exception as e:
        return templates.TemplateResponse("plan-trip-results-error.html", {"request": request})


# Endpoint for Generate Report Functionality
@app.post("/make-report")
async def make_report(request: Request):
    reports_collection = database['reports']
    destination_collection = database['destinations']

    # Use the current user's ID to query for the current user's reports in the DB
    query = {
        "user_id": curr_userID
    }

    # Try to find all the reports related to the current user's ID, and print
    # them onto Reports Results page, and throw exception if not
    try:
        results = list(reports_collection.find(query))

        # Throw error if user has not taken a Plan Trip Survey yet
        if not results:
            return templates.TemplateResponse("make-report-error.html", {"request": request})

        response_list = []

        for result in results:
            stripped_result = json.loads(json_util.dumps(result))

            # Extract location_ids from the result because it's an unnecessary detail to show the end user
            location_ids = stripped_result.get("location_ids", [])

            # Skip entry if location_ids is empty
            if not location_ids:
                continue

            # Retrieve location_name for each location_id because that's what we want to show the end user
            locations_info = []
            location_ids_oid = [ObjectId(location_id) for location_id in location_ids]

            for location_id in location_ids_oid:
                location_query = {
                    "_id": location_id
                }

                location_name_results = list(destination_collection.find(location_query))
                location_name = [result['location_name'] for result in location_name_results]
                location_name_str = ", ".join([str(item) for item in location_name])
                locations_info.append(str(location_name_str))

            stripped_result["locations_info"] = locations_info
            response_list.append(stripped_result)

        return templates.TemplateResponse("report-results.html", {"request": request, "results": response_list})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error querying the database")


# Endpoint to return/get to Home Page
@app.post("/home")
def home():
    return FileResponse("templates/home.html")

# Endpoint to get home from nav bar
@app.get("/getHome")
def home():
    return FileResponse("templates/home.html")


# Endpoint to get to About Page
@app.get("/about")
def about():
    return FileResponse("templates/about.html")

# Endpoint to get to Contact Page
@app.get("/contact")
def contact():
    return FileResponse("templates/contact.html")

# Endpoint to get to Sign Up page
@app.get("/sign-up", response_class=HTMLResponse)
async def sign_up(request: Request):
    return templates.TemplateResponse("sign-up.html", {"request": request})


# Endpoint to perform the Sign Up functionality
@app.post("/sign-up")
async def handle_sign_up(request: Request):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    # Check if username already exists
    collection = database['users']
    existing_user = collection.find_one({"username": username})
    if existing_user:
        return templates.TemplateResponse("sign-up-error.html", {"request": request})

    # Insert username and password into the users collection
    collection.insert_one({"username": username, "password": password})
    print("message: User registered successfully")

    collection = database['users']

    existing_user = collection.find_one({"username": username, "password": password})

    if existing_user:
        global curr_userID
        curr_userID = existing_user['_id']
        print(f"The _id value of the curr_userID is: {curr_userID}")
        print({"message": "Successful login!"})
        return RedirectResponse(url="/home")
    else:
        print({"message": "ERROR: User not found."})
        return HTMLResponse(content="Invalid user account.", status_code=401)


# Endpoint to perform Login functionality
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
        return templates.TemplateResponse("login-error.html", {"request": request})
