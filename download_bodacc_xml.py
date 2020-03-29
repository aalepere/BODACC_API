import pickle
import tarfile

import requests
import xmltodict

from bs4 import BeautifulSoup
from mongo_conf import mongo_user, mongo_pwd
from pymongo import MongoClient

# Connection to Mongo db cluster created on Mongo Atlas
client = MongoClient(
    "mongodb+srv://%s:%s@bodacc-lnbdu.mongodb.net/test?retryWrites=true&w=majority"
    % (mongo_user, mongo_pwd)
)
db = client.bodacc
annonce_collection = db.annonces

# Loads the pickle list of bodacc xmls that have been already loaded into Mongo
try:
    with open("bodacc_loaded.pkl", "rb") as f:
        bodacc_loaded = pickle.load(f)
except FileNotFoundError:
    print("Loading BODACC files for the first time")
    bodacc_loaded = []

# Get the list of available filings for 2020
r = requests.get("https://echanges.dila.gouv.fr/OPENDATA/BODACC/2020/")
soup = BeautifulSoup(r.text, "html.parser")

list_bodacc_files = []
for link in soup.find_all("a"):
    list_bodacc_files.append(link.get("href"))

# Keep only the files related to procedures collectives and that haven't been loaded yet
pcl_bodacc_files = [
    i for i in list_bodacc_files if "PCL" in i and i not in bodacc_loaded
]

# For each file, downlod and untar
for pcl in pcl_bodacc_files:
    r = requests.get(
        "https://echanges.dila.gouv.fr/OPENDATA/BODACC/2020/" + pcl
    )
    open(pcl, "wb").write(r.content)
    tf = tarfile.open(pcl)
    tf.extractall()
    tf.close()

    file_xml = pcl.split(".")[0] + ".xml"

    # Transforms XML to dictionnary
    with open(file_xml, "r") as file:
        my_dict = xmltodict.parse(file.read())

    # For each annonce create a collection to be inserted into Mongo
    for annonce in my_dict["PCL_REDIFF"]["annonces"]["annonce"]:
        collection = {}
        if "numeroImmatriculation" in annonce:
            # Some procedures collectives can have more than one company involved
            if type(annonce["numeroImmatriculation"]) is list:
                for comp in annonce["numeroImmatriculation"]:
                    collection["SIREN"] = comp[
                        "numeroIdentificationRCS"
                    ].replace(" ", "")
                    if "jugement" in annonce:
                        collection["PCL_TYPE"] = annonce["jugement"]["nature"]
                        collection["PCL_DATE"] = annonce["jugement"]["date"]
            else:
                collection["SIREN"] = annonce["numeroImmatriculation"][
                    "numeroIdentificationRCS"
                ].replace(" ", "")
                if "jugement" in annonce:
                    collection["PCL_TYPE"] = annonce["jugement"]["nature"]
                    if "date" in annonce["jugement"]:
                        collection["PCL_DATE"] = annonce["jugement"]["date"]
                    else:
                        collection["PCL_DATE"] = None
        # Some companies might not be registered at the RCS (Registre du commerce)
        else:
            collection["SIREN"] = "NonInscrit"
            if "jugement" in annonce:
                collection["PCL_TYPE"] = annonce["jugement"]["nature"]
                if "date" in annonce["jugement"]:
                    collection["PCL_DATE"] = annonce["jugement"]["date"]
                else:
                    collection["PCL_DATE"] = None
        # Insert the collection
        annonce_collection.insert_one(collection)
# Create an index on the SIREN
annonce_collection.create_index([("SIREN", 1)])

# Pickle the list of
with open("bodacc_loaded.pkl", "wb") as f:
    pickle.dump(set(bodacc_loaded + pcl_bodacc_files), f)
