import json

from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client.refunite


with open('people.json', 'r') as f:
    people_data = json.load(f)
    people = people_data['result']
    db.people.insert(people)
db.people.create_index('age')
db.people.create_index('gender')
db.people.create_index('company')
db.people.create_index('tags')
