[![CodeFactor](https://www.codefactor.io/repository/github/aalepere/bodacc_api/badge)](https://www.codefactor.io/repository/github/aalepere/bodacc_api)

# Author
Arnaud ALEPEE

# Example

```shell
curl https://bodacc.herokuapp.com/813251303
```

# Documentation
https://arnaudalepee.docs.apiary.io/

# Medium ref

## Introduction and background
The french government published on a daily basis all the notices published on the BODACC (Bulletin officiel des annonces civiles et commerciales, https://www.data.gouv.fr/en/datasets/bodacc/). 
These notices are mainly related to:
* Registration of a new company
* Filing of new financial statements
* Legal actions related to insolvency

In this article, we will only focus on the insolvency notices. 

## Challenges
All these notices are published by day and in a XML format on a FTP. There are 2 main issues:
* The day by day files, do not allow you to search for a specific company; and
* the XML format on the FTP doesn't allow to consume it in real time.

In order to overcome those issues, we can create a database that will ingest the new files on a daily basis and expose this information through a REST API that will allow to retrieve all insolvency notices for a given company.

## Infrastructure

![Image description](https://cdn-images-1.medium.com/max/1600/1*WecRNLFDXKPm387EXy460A.png)

The infrastructure proposed is as follows:

(1) A scheduler is loading the XML files from the FTP into the Mongo database every time a new XML is published.

(2) A local computer (or another system) calls the GET API for a given company.

(3) The flask API endpoint runs a query on Mongo for the given company that was used in the API call.

(4) Mongo retrieves the relevant document from the collection.

(5) The answer from Mongo is deserialise into a python dictionary which then sent back to the local computer.

## Solution
### MongoDB
First we need to create an instance on Mongo Atlas: https://www.mongodb.com/cloud/atlas. 
You can create a sandbox cluster for free but you will be limited by the storage (512MB). Also please note that when using Heroku freemium we can't control IPs so it will required to whitelist all IPs.

With the help of 3 main libraries, we can insert data into our MongoDB cluster:
**pymongo**, python API for MongoDB which allows us to connect the database and also perform some operations such as inserting documents or finding documents.

```python
import os
from pymongo import MongoClient  
def mongo_connect(db_name, collection_name):    
    """    
    Connection to Mongo db cluster created on Mongo Atlas    
    Use env variable for the user and the pwd to be used.
    Once connected, you need to choose the database and the    
    collection.
    """     
    client = MongoClient(        
         "mongodb+srv://%s:%s@XXXXXXXXXX.net/"        
         % (os.environ["mongo_user"], os.environ["mongo_pwd"])    
    )    
    
    db = client.db_name    
    annonce_collection = db.collection_name     
    
    return annonce_collection

def insert_all(pcl_bodacc_files, url, annonce_collection):    
    """        
        Loop though all the bodac files that havent been downloaded
        yet, download them, untar them.
        Then create a dictionary than can then be pushed into
        MongoDB.    
    """    
    
    # For each file, downlod and untar    
    for pcl in pcl_bodacc_files:       
        my_dict = convert_xml_bodacc_to_dict(pcl, url)         
        
        # For each annonce create a collection to be inserted into
        # Mongo        
        for annonce in my_dict["PCL_REDIFF"]["annonces"]["annonce"]:
            collection = create_document_for_insert(annonce)       
            # Insert the collection
            annonce_collection.insert_one(collection)
```

**BeautifulSoup**, library for parsing the html content when a web page is call through an http request. In our scenario, the webpage contains the list of all XML files which are available. We can parse this webpage and then download each file one by one:

```python
# Get the list of available filings for 2020    
r = requests.get(url)    
soup = BeautifulSoup(r.text, "html.parser")     
list_bodacc_files = []    
for link in soup.find_all("a"):
    list_bodacc_files.append(link.get("href"))
xmltodict, a library to convert XML content to a python dictionary. All the BODACC filing which are made available are in an XML format, thanks to this library we can convert it to a dictionary and browse through it to extract the information we need:

# Transforms XML to dictionnary    
with open(file_xml, "r") as file:        
    my_dict = xmltodict.parse(file.read())
print(my_dict["numeroImmatriculation"])
Flask
Flask is web framework written in Python, which allows us to create a REST API in a few lines of code:
from flask import Flask
from flask_restful import Api, Resource
from utils.mongo_connection import mongo_connect 
app = Flask(__name__)
api = Api(app)  

class BodaccPCL(Resource):    
    def get(self, siren):
        """
           Retries the list of documents stored in Mongo which are
           linked to the give SIREN        
        """        
        
        collection = mongo_connect()        
        result = collection.find({"SIREN": siren})        
        if result:            
             list_of_annonces = []            
             for r in result:                
                 list_of_annonces.append(                    
                 {
                      "PCL_TYPE": r["PCL_TYPE"], 
                      "PCL_DATE": r["PCL_DATE"]
                 }                
                 )            
             return {siren: list_of_annonces}        
        else:            
            return {siren: []}  
    api.add_resource(BodaccPCL, "/<string:siren>")  
if __name__ == "__main__":    
    app.run()
```
### Heroku
Now that we have the Flask API working locally, it is time to push to the production environment!
To be ready to use Heroku, we need to have some extra files in our GitHub repos:

**requirements.txt**, which will contain all the python libraries required to run the project. If you have already set up an virtual environment you can create such file with the command line 
```shell
pip freeze > requirements.txt
```

**runtime.txt**, this is to tell to Heroku which version of python to install. For example: python-3.7.5

An application server, here we are using uWSGI (https://uwsgi-docs.readthedocs.io/en/latest/)

```ini
#uwsgi.ini file content
[uwsgi]
http-socket = :$(PORT) # port to be used, using the env one
master = true
die-on-term = true
module = app:app # name of the Flask app, app.py
memory-report = true
```

**Procfile**, in order to initiate the webserver:

```
# Procfile file content
web: uwsgi uwsgi.ini
```
