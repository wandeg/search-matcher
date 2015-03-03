import operator
from dateutil.parser import parse
from collections import Counter
from flask import Blueprint, request, redirect, render_template
from flask import url_for, session, flash
from flask.views import MethodView
from flask.ext.mongoengine.wtf import model_form
from mongoengine.queryset import Q
from werkzeug.contrib.cache import SimpleCache

from profile_matcher.models import UserSearch, People
import actions

cache = SimpleCache()

user_searches = Blueprint('user_searches', __name__,
	template_folder='templates')


def get_searches():
	searches = cache.get('searches')
	if searches is None:
		searches = actions.generateAllSearches()
		cache.set('searches', searches, timeout=3600)
	return searches


def get_suggestion_from_other_searches(searches, my_id):
	suggestions = cache.get('suggestions')
	if suggestions is None:
		suggestions = actions.getSearchSuggestions(searches, my_id)
		cache.set('suggestions', suggestions, timeout=3600)
	return suggestions


def get_users_with_similar_searches(searches, my_id):
	similar_users = cache.get('similar_users')
	if similar_users is None:
		similar_users = actions.mostSimilar(searches, my_id)
		cache.set('similar_users', similar_users, timeout=3600)
	return similar_users


def get_users_with_similar_friends(user):
	friends = People.objects(friends__in=user.friends).only("guid", "name")
	return friends


def get_colleagues(user):
	colleagues = People.objects(company=user.company).only("guid", "name")
	return colleagues


def get_users_with_similar_tags(user):
	similar_tags = People.objects(tags__in=user.tags).only("guid", "name")
	return similar_tags


def get_my_common_results(user):
	my_searches = UserSearch.objects(user=user)
	my_results = [result for search in my_searches 
				for result in search.results]
	return Counter(my_results).most_common(10)


class HomeView(MethodView):
	def get(self):
		return render_template('user_searches/home.html')


class ListView(MethodView):

	def get(self):
		user_searches = []
		if 'user' in session:
			user = People.objects.get(email=session['user']['email'])
			user_searches = UserSearch.objects(user=user).order_by('-created_at')
			searches = get_searches()
			similar_search_users = get_users_with_similar_searches(searches, user.guid)
			for usr in similar_search_users:
				user = People.objects.get(guid=usr[1])
				print user

		return render_template('user_searches/list.html', 
			user_searches=user_searches)


class DetailView(MethodView):

	def get(self, slug):
		search = UserSearch.objects.get_or_404(slug=slug)
		print search.terms
		terms_used = search.terms.values
		searches = cache.get('searches')
		return render_template('user_searches/detail.html', 
								search=search)


class SearchView(MethodView):
	def get(self):
		if 'user' in session:
			my_id = session['user']['guid']
			print session['user']
			searches = get_searches()
			my_searches=searches[my_id]
			ordered_searches=sorted(my_searches.items(),
								key=operator.itemgetter(1), reverse=True)
			print ordered_searches
			suggestions = get_suggestion_from_other_searches(searches,my_id)
			print suggestions
			similar_search_users=get_users_with_similar_searches(searches,my_id)
			print similar_search_users
			print [searches[k[1]] for k in similar_search_users]
			return render_template('user_searches/search.html')
		else:
			return redirect('/login')

	def post(self):
		data = request.form.to_dict()
		print data
		age = data['age']
		gender = data['gender']
		company = data['company']
		tags = data['tags'].split(',')
		logged_in_user = session['user']
		user = People.objects.get(email=logged_in_user['email'])
		if user:
			terms = {'age': {}, 'gender': {}, 'company': {}, 'tags': {}}
			if hasattr(user, 'terms_used') and user.terms_used.keys():
				terms = user.terms_used
				
			print terms
			if len(age):
				terms['age'][age] = terms['age'].get(age, 0)+1
			if len(gender):
				terms['gender'][gender] = terms['gender'].get(gender, 0)+1
			if len(company):
				terms['company'][company] = terms['company'].get(company, 0)+1
			if len(tags):
				for tag in tags:
					if len(tag):
						terms['tags'][tag] = terms['tags'].get(tag, 0)+1 
			print terms
			query = actions.create_query(**data)
			print query
			print user.registered
			profs = People.objects(**query).only("guid", "name")
			user.terms_used = terms
			print user
			if isinstance(user.registered, str):
				# Register date causing error to be thrown on save
				user.registered = parse(user.registered) 
			user.save()
			search = UserSearch()
			search.user = user
			search.terms = data
			search.save()
			search.slug = str(search.id)
			if profs:
				search.results = profs
			search.save()
			return render_template('user_searches/results.html',search=search)

		return render_template('user_searches/search.html')


class LoginView(MethodView):

	def get(self):
		return render_template('user_searches/login.html')
	
	def post(self):
		data = request.form.to_dict()
		email = data['email']
		password = data['password']
		if email and password:
			password = str(password)
			[user, valid] = actions.login(email, password)
			if user and valid:
				session['user'] = user
				return redirect('/search')
		return redirect('/login')


class LogoutView(MethodView):
	
	def get(self):
		session.pop('user', None)
		return redirect('/login')


class ProfileView(MethodView):

	def get(self, guid):
		#  	if 'user' in session:
		# user=session['user']
		profile = {}
		user = People.objects.get(guid=guid)
		profile['user'] = user
		if session['user']['guid'] == user['guid']:
			friends = []
			colleagues = []
			similar_tags = []
			most_returned = []

			friends = get_users_with_similar_friends(user)[:10]
			colleagues = get_colleagues(user)[:10]
			similar_tags = get_users_with_similar_tags(user)[:10]
			most_returned = get_my_common_results(user)
			profile['mutual_friends'] = friends
			profile['colleagues'] = colleagues
			profile['similar_tags'] = similar_tags
			profile['most_returned'] = [People.objects.get(guid=res[0])
										for res in most_returned]
		else:
			# print session['user']
			# print type(session['user'])
			sess_user = People.objects.get(guid=session['user']['guid'])
			profiles_viewed = sess_user.profiles_viewed
			profiles_viewed[guid] = profiles_viewed.get(guid, 0)+1
			sess_user.profiles_viewed = profiles_viewed
			sess_user.save()
			
		# for usr in similar_search_users:
		# 	user=People.objects.get(guid=usr[1])
		# 	print user

		return render_template('user_searches/profile.html', profile=profile)
# Register the urls
user_searches.add_url_rule('/', 
							view_func=HomeView.as_view('home'))
user_searches.add_url_rule('/my_searches', 
							view_func=ListView.as_view('my_searches'))
user_searches.add_url_rule('/login/', 
							view_func=LoginView.as_view('login'),
							methods=["GET", "POST"])
user_searches.add_url_rule('/logout/', 
							view_func=LogoutView.as_view('logout'))
user_searches.add_url_rule('/search', 
							view_func=SearchView.as_view('search'),
							methods=["GET", "POST"])
user_searches.add_url_rule('/profile/<guid>/', 
							view_func=ProfileView.as_view('profile'))
user_searches.add_url_rule('/search/<slug>/', 
							view_func=DetailView.as_view('detail'))
