from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

DB_USERNAME = os.getenv("MONGODB_USERNAME")
DB_PASSWORD = os.getenv("MONGODB_PASSWORD")

# mongodb+srv://<db_username>:<db_password>@cluster0.tmm4plt.mongodb.net/?appName=Cluster0
uri = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.tmm4plt.mongodb.net/?appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)