# search-matcher
Match people based on common search patterns

# Search Engine
The search engine allows you to query for user profiles using several parameters such as age, gender, company and tags. The parameters and results are stored so that the engine can adapt to previous searches and generate suggestions.


# People you may know:
This appears on an individual's profile. It is based on several factors such as: mutual friends, similar search parameters, results that appear most frequently in your searches and users with similar properties such as tags, and company.

All search and profile matching is done by and elementary form of collaborative filterting using an Euclidean distance calculator that analyzes a user against the rest of the users


# Prerequisites:

Python 2.7
MongoDb 2.6+

# Installation
This is preferrably done within a virtualenv - Instructions for setting one up can be found here: https://virtualenvwrapper.readthedocs.org/en/latest/

Once that is done activate the virtualenv. 

Clone the git repo into your working directory. 

Install all dependencies using pip install -r requirements.txt 

Run the json_loader.py file to set up the database

Run python manage.py runserver to start the program

Login using any of the email addresses in people.json

Use anything as your password but the field should not be left blank

Navigate to the search page to make your query

The engine will track your searches and optimize results and suggestions based on patterns it detects
