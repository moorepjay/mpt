from pymongo import MongoClient
from constant import CONNECTION_STRING


# TODO: Use python-dotenv!!!!
def get_collection(collection):
    client = MongoClient(CONNECTION_STRING)
    db = client['PROD']
    collection = db[collection]

    return collection
