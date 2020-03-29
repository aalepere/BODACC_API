from flask import Flask
from flask_restful import Api, Resource
from utils.mongo_connection import mongo_connect

app = Flask(__name__)
api = Api(app)


class BodaccPCL(Resource):
    def get(self, siren):
        collection = mongo_connect()
        result = collection.find_one({"SIREN": siren})
        return {
                "SIREN": result["SIREN"],
                "PCL_TYPE": result["PCL_TYPE"],
                "PCL_DATE": result["PCL_DATE"]
                }


api.add_resource(BodaccPCL, '/<string:siren>')


if __name__ == '__main__':
    app.run()
