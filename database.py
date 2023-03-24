from pymongo import MongoClient
import os


def get_database(database):
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb+srv://moorepj:$tandForSomething1441|@agsrmt.6jcivn0.mongodb.net/test"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client[database]


# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":
    # Get the database
    dbname = get_database()
