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
	"""Returns all searches by all users"""
	searches = cache.get('searches')
	if searches is None:
		searches = actions.generateAllSearches()
		cache.set('searches', searches, timeout=600)
	return searches


def get_suggestion_from_other_searches(searches, my_id):
	"""Returns search suggestions based on other users searches"""
	suggestions = cache.get('suggestions')
	if suggestions is None:
		suggestions = actions.getSearchSuggestions(searches, my_id)
		cache.set('suggestions', suggestions, timeout=600)
	return suggestions


def get_users_with_similar_searches(searches, my_id, n=5):
	"""Returns users with similar search patterns.
	If there are no users"""
	similar_users = cache.get('similar_users')
	if similar_users is None:
		similar_users = actions.mostSimilar(searches, my_id, n)
		cache.set('similar_users', similar_users, timeout=600)
	return similar_users


def get_users_with_similar_friends(user):
	"""Returns users with similar friends to the current user"""
	friends = People.objects(friends__in=user.friends).only("guid", "name")
	return friends


def get_colleagues(user):
	"""Returns users who work in the same company as the current user"""
	colleagues = People.objects(company=user.company).only("guid", "name")
	return colleagues


def get_users_with_similar_tags(user):
	"""Returns users with similar tags to the current user"""
	similar_tags = People.objects(tags__in=user.tags).only("guid", "name")
	return similar_tags


def get_my_most_common_results(user):
	"""Returns the current user's most repeatedly occurring results"""
	my_searches = UserSearch.objects(user=user)
	my_results = [result for search in my_searches
					for result in search.results]
	return Counter(my_results).most_common(10)


def most_common_queries_per_category(user):
	"""Returns the current user's most repeatedly searched query
	per search category"""
	terms_used = user.terms_used
	common = {}
	for k, v in terms_used.items():
		common[k] = Counter(v).most_common(1)
	return common


class HomeView(MethodView):

	def get(self):
		return render_template('user_searches/home.html')


class ListView(MethodView):

	def get(self):
		user_searches = []
		if 'user' in session:
			user = People.objects.get(guid=session['user']['guid'])
			searches = UserSearch.objects(user=user).order_by('-created_at')
		return render_template('user_searches/list.html',
			user_searches=searches)


class DetailView(MethodView):

	def get(self, slug):
		search = UserSearch.objects.get_or_404(slug=slug)
		return render_template('user_searches/detail.html',
								search=search)


class SearchView(MethodView):

	def get(self):
		if 'user' in session:
			my_id = session['user']['guid']
			user = People.objects.get(guid=my_id)
			suggs = {}
			searches = get_searches()
			my_searches = searches[my_id]
			ordered_searches = sorted(my_searches.items(),
								key=operator.itemgetter(1), reverse=True)
			params = get_suggestion_from_other_searches(searches, my_id)
			suggs['param_suggestions'] = params
			profiles_viewed = user.profiles_viewed
			if profiles_viewed:
				most_viewed = Counter(profiles_viewed).most_common(3)
				if most_viewed:
					suggs['most_viewed'] = [People.objects.get(guid=res[0]) 
													for res in most_viewed] 
			return render_template('user_searches/search.html', 
				suggestions=suggs)
		else:
			return redirect('/login')

	def post(self):
		data = request.form.to_dict()
		age = data['age']
		gender = data['gender']
		company = data['company']
		tags = data['tags'].split(',')
		logged_in_user = session['user']
		user = People.objects.get(guid=logged_in_user['guid'])
		if user:
			terms = {'age': {}, 'gender': {}, 'company': {}, 'tags': {}}
			if hasattr(user, 'terms_used') and user.terms_used.keys():
				terms = user.terms_used
			# Increment the value of each posted search term by 1 in the user's
			# search terms
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
			most_common = most_common_queries_per_category(user)
			# Modify query to use most common parameter per
			# category if it hasn't been provided
			if 'intellisense' in data:
				for k, v in data.items():
					if not data[k] and most_common[k]:
						data[k] = most_common[k][0][0]
				data.pop('intellisense')
			query = actions.create_query(**data)
			profiles = People.objects(**query).only("guid", "name")
			user.terms_used = terms
			if isinstance(user.registered, str):
				# Prevent register date from an causing error to be thrown
				# on save
				user.registered = parse(user.registered)
			user.save()
			search = UserSearch()
			search.user = user
			search.terms = data
			search.save()
			search.slug = str(search.id)
			if profiles:
				search.results = profiles
			search.save()
			return redirect('my_searches')

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
		profile = {}
		user = People.objects.get(guid=guid)
		profile['user'] = user
		viewing_own_profile = session['user']['guid'] == guid
		if viewing_own_profile:
			# Only show certain things if viewing own profile
			friends = []
			colleagues = []
			similar_tags = []
			most_returned_results = []
			most_viewed = []
			friends = get_users_with_similar_friends(user)[:5]
			colleagues = get_colleagues(user)[:5]
			similar_tags = get_users_with_similar_tags(user)[:5]
			most_returned_results = get_my_most_common_results(user)
			searches = get_searches()
			similar_searchers = get_users_with_similar_searches(searches,
								session['user']['guid'])
			profile['mutual_friends'] = friends
			profile['colleagues'] = colleagues
			profile['similar_tags'] = similar_tags
			profile['most_returned'] = [res[0]
										for res in most_returned_results]
			profile['similar_searchers'] = [People.objects.get(guid=res[1])
											for res in similar_searchers]
		else:
			# Increment profile views for profile fetched for logged in user
			logged_in_user = People.objects.get(guid=session['user']['guid'])
			profiles_viewed = logged_in_user.profiles_viewed
			profiles_viewed[guid] = profiles_viewed.get(guid, 0)+1
			logged_in_user.profiles_viewed = profiles_viewed
			logged_in_user.save()

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
