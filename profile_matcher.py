from flask import Flask
from pymongo import MongoClient
from flask_login import LoginManager
client = MongoClient("mongodb://localhost:27017")
db = client.refunite


app = Flask(__name__)