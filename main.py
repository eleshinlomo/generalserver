import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Routes
from app.routes.remote import remote_router



app = FastAPI(root_path='/api/generalserver')
app.include_router(remote_router)


# Enable CORS for communication with Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

