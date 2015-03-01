import actions
from dateutil.parser import parse
from flask import Blueprint, request, redirect, render_template
from flask import url_for, session, flash
from flask.views import MethodView
from mongoengine.queryset import Q
from profile_matcher.models import UserSearch,  People
from flask.ext.mongoengine.wtf import model_form
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

user_searches = Blueprint('user_searches', __name__, 
	template_folder='templates')

def get_searches():
	searches = cache.get('searches')
	if searches is  None:
		searches=actions.generateAllSearches()
		cache.set('searches', searches, timeout=3600)
	return searches

def get_suggestions(searches,my_id):
	suggestions = cache.get('suggestions')
	if suggestions is  None:
		suggestions=actions.getSearchSuggestions(searches,my_id)
		cache.set('suggestions', suggestions, timeout=3600)
	return suggestions

def get_users_with_similar_searches(searches,my_id):
	similar_users = cache.get('similar_users')
	if similar_users is  None:
		similar_users=actions.mostSimilar(searches,my_id)
		cache.set('similar_users', similar_users, timeout=3600)
	return similar_users

def get_users_with_similar_profiles(user):
	# print user.name
	reason="No users you may know"
	friends=[]
	if not friends:
		friends=People.objects(Q(friends__in=user.friends)) 
		reason="You have mutual friends"
	if not friends or len(friends <10):
		friends=People.objects(Q(company=user.company))
		reason="You are workmates"
	if not friends or len(friends <10):
		friends=People.objects(Q(tags__in=user.tags))
		reason="You have similar tags"
	# friends=People.objects(email__ne=user.email)
	print user.tags
	print friends
	print len(friends)

class ListView(MethodView):

    def get(self):
    	user_searches=[]
    	if 'user' in session:
			user=People.objects.get(email=session['user']['email'])
			user_searches = UserSearch.objects(user=user)
			searches = get_searches()
			get_users_with_similar_profiles(user)
			similar_search_users=get_users_with_similar_searches(searches,user.guid)
			print similar_search_users
			for usr in similar_search_users:
				user=People.objects.get(guid=usr[1])
				print user

        return render_template('user_searches/list.html', 
        	user_searches=user_searches)


class DetailView(MethodView):

    def get(self, slug):
        search = UserSearch.objects.get_or_404(slug=slug)
        print search.terms
        terms_used=search.terms.values
        searches = cache.get('searches')
        return render_template('user_searches/detail.html', 
        	search=search)

class SearchView(MethodView):
	def get(self):
		if 'user' in session:
			my_id=session['user']['guid']
			searches = cache.get('searches')
			suggestions = cache.get('suggestions')
			if searches is  None:
				searches=actions.generateAllSearches()
				cache.set('searches', searches, timeout=3600)
			if suggestions is  None:
				suggestions=actions.getSearchSuggestions(searches,my_id)
				cache.set('suggestions', suggestions, timeout=3600)
			
			return render_template('user_searches/search.html')
		else:
			return redirect('/login')

	def post(self):
		data=request.form.to_dict()
		age=data['age']
		gender=data['gender']
		company=data['company']
		tags=data['tags'].split(',')
		logged_in_user=session['user']
		user=People.objects.get(email=logged_in_user['email'])
		if user:
			if hasattr(user,'terms_used'):
				terms={'age':{},'gender':{},'company':{},'tags':{}}
			else:
				terms={'age':{},'gender':{},'company':{},'tags':{}}
			if age:
				terms['age'][age]=terms['age'].get(age,0)+1
			if gender:
				terms['gender'][gender]=terms['gender'].get(gender,0)+1
			if company:
				terms['company'][company]=terms['company'].get(company,0)+1
			if tags:
				for tag in tags:
					if len(tag):
						terms['tags'][tag]=terms['tags'].get(tag,0)+1 
			print terms
			query=actions.create_query(**data)
			print query
			print user.registered
			profs=People.objects(**query)
			user.terms_used=terms
			print user
			if isinstance(user.registered,str):
				user.registered=parse(user.registered)
			user.save()
			search=UserSearch()
			search.user=user
			search.terms=data
			search.save()
			search.slug=str(search.id)
			if profs:
				search.results=([prof.guid for prof in profs])
			search.save()
			return render_template('user_searches/list.html')

		return render_template('user_searches/search.html')

class LoginView(MethodView):
	def get(self):
		return render_template('user_searches/login.html')

	def post(self):
		data=request.form.to_dict()
		email=data['email']
		password=data['password']
		if email and password:
			password=str(password)
			[user, valid]=actions.login(email,password)
			if user and valid:
				session['user']=user
				return redirect('/search')
		return redirect('/login')

class LogoutView(MethodView):
	def get(self):
		session.pop('user', None)
		return redirect('/login')


class ProfileView(MethodView):

    def get(self):
    	if 'user' in session:
			user=People.objects.get(email=session['user']['email'])
			user_searches = UserSearch.objects(user=user)
			searches = get_searches()
			get_users_with_similar_profiles(user)
			similar_search_users=get_users_with_similar_searches(searches,user.guid)
			print similar_search_users
			for usr in similar_search_users:
				user=People.objects.get(guid=usr[1])
				print user

        return render_template('user_searches/profile.html', 
        	user_searches=user_searches)



# Register the urls
user_searches.add_url_rule('/', view_func=ListView.as_view('list'))
user_searches.add_url_rule('/login/', view_func=LoginView.as_view('login'),methods=["GET","POST"])
user_searches.add_url_rule('/logout/', view_func=LogoutView.as_view('logout'),methods=["GET"])
user_searches.add_url_rule('/search', view_func=SearchView.as_view('search'),methods=["GET","POST"])
user_searches.add_url_rule('/<slug>/', view_func=DetailView.as_view('detail'))