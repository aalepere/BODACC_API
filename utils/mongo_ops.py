import tarfile

import requests
import xmltodict


def insert_all(pcl_bodacc_files, url, annonce_collection):
    """
        Loop though all the bodac files that havent been downloaded yet, download them, untar them.
        Then create a dictionary than can then be pushed into MongoDB.
    """
    # For each file, downlod and untar
    for pcl in pcl_bodacc_files:
        r = requests.get(url + pcl)
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
                            collection["PCL_TYPE"] = annonce["jugement"][
                                "nature"
                            ]
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


def create_index(annonce_collection, index_col):
    """
        create an index for a given collection and for a given column
    """
    annonce_collection.create_index([(index_col, 1)])
