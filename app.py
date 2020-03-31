from flask import Flask
from flask_restful import Api, Resource
from utils.mongo_connection import mongo_connect

app = Flask(__name__)
api = Api(app)


class BodaccPCL(Resource):
    def get(self, siren):
        collection = mongo_connect()
        result = collection.find({"SIREN": siren})
        if result:
            list_of_annonces = []
            for r in result:
                list_of_annonces.append(
                    {"PCL_TYPE": result["PCL_TYPE"], "PCL_DATE": result["PCL_DATE"]}
                )
            return {result["SIREN"]: list_of_annonces}
        else:
            return {result["SIREN"]: []}


api.add_resource(BodaccPCL, "/<string:siren>")


if __name__ == "__main__":
    app.run()
