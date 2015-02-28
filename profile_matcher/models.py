import datetime
from flask import url_for
from profile_matcher import db
from mongoengine import *


class People(db.Document):
	id=db.IntField()
	guid=db.StringField()
	picture=db.StringField()
	age=db.IntField()
	name=db.StringField()
	gender=db.StringField()
	company=db.StringField()
	phone=db.StringField()
	email=db.StringField()
	address=db.StringField()
	about=db.StringField()
	registered=db.DateTimeField()
	tags=db.ListField(db.StringField(max_length=10))
	friends=db.ListField(db.EmbeddedDocumentField('Friend'))

class Friend(db.EmbeddedDocument):
	id=db.IntField()
	name=db.StringField()

class SearchTerms(db.EmbeddedDocument):
	age=db.IntField()
	gender=db.StringField()
	company=db.StringField()
	tags=db.ListField()

class UserSearch(db.Document):
	user=db.ReferenceField('People',reverse_delete_rule=CASCADE)
	title=db.StringField()
	created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
	terms=db.EmbeddedDocumentField('SearchTerms')
	results=db.ListField(db.EmbeddedDocumentField('Result'))



class Result(db.EmbeddedDocument):
	match=db.ReferenceField('People')

class ProfileView(db.Document):
	user=db.ReferenceField('People',reverse_delete_rule=CASCADE)
	profile_viewed=db.StringField()