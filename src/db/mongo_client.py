from pymongo import MongoClient
from utils.config import MONGO_URI, MONGO_DB

# Connect to the external MongoDB instance
mongo_client = MongoClient(MONGO_URI, tlsallowinvalidcertificates=True)
db = mongo_client[MONGO_DB]
