
from flask import Flask
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "refunite"}
app.config["SECRET_KEY"] = "\xb9\xb9\x14\x95\xd5AJ\xb1\xef\x08\xf4\xff\x8c\xcd\xbb4\xb2P\n\xc5&G\xc4T"

db = MongoEngine(app)

def register_blueprints(app):
    # Prevents circular imports
    from profile_matcher.views import user_searches
    app.register_blueprint(user_searches)

register_blueprints(app)

if __name__ == '__main__':
    app.run()