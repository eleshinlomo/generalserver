# Overview
This is a general server and it is built with FastAPI

# First app opening, must install all dependencies for app to work
source venv/bin/activate
pip install -r requirements.txt

# Start app
 <!-- Only run first command if venv is not activated -->
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001


# Version Control for deployment to Github
git add .
git commit -m "Your message"
git push origin develop