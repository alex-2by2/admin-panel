import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGODB_URI")

client = MongoClient(MONGO_URI)
db = client["captionbot"]

captions = db.captions
