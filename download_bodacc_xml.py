""" This script download new BODACC filings and save them into Mongo db """
import pickle

from env_conf import bodacc_url, pickle_file
from utils.download_list_of_pcls import get_list_of_bodaccs
from utils.mongo_connection import mongo_connect
from utils.mongo_ops import create_index, insert_all

if __name__ == "__main__":
    # Connection to Mongo db cluster created on Mongo Atlas
    annonce_collection = mongo_connect()

    # Loads the pickle list of bodacc xmls that have not been already loaded into Mongo
    bodacc_loaded, pcl_bodacc_files = get_list_of_bodaccs(
        pickle_file, bodacc_url
    )

    # Load into MongoDB all new PCL publications
    insert_all(pcl_bodacc_files, bodacc_url, annonce_collection)

    # Create an index on the SIREN
    create_index(annonce_collection, "SIREN")

    # Pickle the list of
    with open(pickle_file, "wb") as f:
        pickle.dump(set(bodacc_loaded + pcl_bodacc_files), f)
