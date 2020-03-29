from mongo_conf import mongo_pwd, mongo_user
from pymongo import MongoClient


def mongo_connect():
    """
    Connection to Mongo db cluster created on Mongo Atlas 
    Reads information from mongo_conf file and returns the annonces collection
    """

    client = MongoClient(
        "mongodb+srv://%s:%s@bodacc-lnbdu.mongodb.net/test?retryWrites=true&w=majority"
        % (mongo_user, mongo_pwd)
    )
    db = client.bodacc
    annonce_collection = db.annonces

    return annonce_collection
