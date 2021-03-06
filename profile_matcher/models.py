import datetime
from flask import url_for
from profile_matcher import db
from mongoengine import *
from werkzeug.security import generate_password_hash, check_password_hash


class People(db.Document):
	id = db.IntField()
	guid = db.StringField()
	picture = db.StringField()
	age = db.IntField()
	name = db.StringField()
	gender = db.StringField()
	company = db.StringField()
	phone = db.StringField()
	email = db.StringField()
	address = db.StringField()
	about = db.StringField()
	registered = db.DateTimeField()
	tags = db.ListField(db.StringField())
	friends = db.ListField(db.EmbeddedDocumentField('Friend'))
	terms_used = db.DictField()
	profiles_viewed = db.DictField()
	password = db.StringField()

	def __unicode__(self):
		return self.name

	def set_password(self, password):
		hashed = generate_password_hash(password)
		self.password = hashed
		self.save()

	def check_password(self, password):
		hashed = generate_password_hash(password)
		if self.password:
			return check_password_hash(self.password, password)
		else:
			return True

	def unpack_terms(self):
		unpacked = {}
		my_terms = self.terms_used
		if my_terms:
			for key in my_terms.keys():
				unpacked.update(my_terms[key])
		return unpacked


class Friend(db.EmbeddedDocument):
	id = db.IntField()
	name = db.StringField()


class UserSearch(db.Document):
	user = db.ReferenceField('People', reverse_delete_rule=CASCADE)
	title = db.StringField()
	slug = db.StringField()
	created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
	terms = db.DictField()
	results = db.ListField()
