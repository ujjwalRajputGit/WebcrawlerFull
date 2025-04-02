from pymongo import MongoClient
from utils.config import MONGO_URI, MONGO_DB

mongo_client = MongoClient(MONGO_URI, tlsallowinvalidcertificates=True)
db = mongo_client[MONGO_DB]
