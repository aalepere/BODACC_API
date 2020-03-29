import pickle

import requests

from bs4 import BeautifulSoup


def get_list_of_bodaccs(pickle_file, url):
    """
    Loads the pickle list of bodacc xmls that have been already loaded into Mongo
    Retrieves the list of bodaccs that haven't been downloaded yet
    """

    try:
        with open(pickle_file, "rb") as f:
            bodacc_loaded = pickle.load(f)
    except FileNotFoundError:
        print("Loading BODACC files for the first time")
        bodacc_loaded = []

    # Get the list of available filings for 2020
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    list_bodacc_files = []
    for link in soup.find_all("a"):
        list_bodacc_files.append(link.get("href"))

    # Keep only the files related to procedures collectives and that haven't been loaded yet
    pcl_bodacc_files = [
        i for i in list_bodacc_files if "PCL" in i and i not in bodacc_loaded
    ]

    return bodacc_loaded, pcl_bodacc_files
