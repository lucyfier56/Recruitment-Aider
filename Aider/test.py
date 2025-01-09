# Test connection separately
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()
import os

connection_string = os.getenv("MONGODB_CONNECTION_STRING")
client = MongoClient()
try:
    client.admin.command('ping')
    print("Connected successfully!")
except Exception as e:
    print(f"Connection failed: {e}")