
from flask import Flask
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "refunite"}
app.config["SECRET_KEY"] = "Th3r@1n1n5p@1n5t@y5m@1nly1nth3pl@1n"

db = MongoEngine(app)

def register_blueprints(app):
    # Prevents circular imports
    from profile_matcher.views import user_searches
    app.register_blueprint(user_searches)

register_blueprints(app)

if __name__ == '__main__':
    app.run()