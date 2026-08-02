# Overview
This is a general server and it is built with FastAPI

# IF STARTING SERVER FIRST TIME, YOU MUST RUN STEP 1 -3

## Create python environment Step 1
python -m venv venv

# Activate environment Step 2
## for windows
venv\Scripts\activate

## linux 
source venv/bin/activate

# Install dependencies Step 3
pip install -r requirements.txt


# START SERVER
 <!-- Only run venv command if venv is not activated else skip to start -->
 # Activate environment Step 2
## for windows
venv\Scripts\activate

## linux 
source venv/bin/activate

# Start Server
uvicorn main:app --reload --host 0.0.0.0 --port 8001


# Version Control for deployment to Github
git add .
git commit -m "Your message"
git push origin develop