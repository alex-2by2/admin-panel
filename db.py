import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URI = os.environ.get("MONGODB_URI")

client = None
db = None
captions = None

def init_db():
    global client, db, captions
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")
        db = client["captionbot"]
        captions = db.captions
        print("✅ MongoDB connected")
    except ServerSelectionTimeoutError as e:
        print("❌ MongoDB not connected:", e)
        captions = None
