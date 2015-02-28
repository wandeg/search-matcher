import actions
from flask import Blueprint, request, redirect, render_template
from flask import url_for, session, flash
from flask.views import MethodView
from profile_matcher.models import UserSearch, Result, People
from flask.ext.mongoengine.wtf import model_form

user_searches = Blueprint('user_searches', __name__, 
	template_folder='templates')


class ListView(MethodView):

    def get(self):
        user_searches = UserSearch.objects.all()
        return render_template('user_searches/list.html', 
        	user_searches=user_searches)


class DetailView(MethodView):

    def get(self, slug):
        search = UserSearch.objects.get_or_404(slug=slug)
        return render_template('user_searches/detail.html', 
        	search=search)

class SearchView(MethodView):
	def get(self):
		if 'user' in session:
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
				terms=user.terms_used
			else:
				terms={}
			if age:
				terms[age]=terms.get(age,0)+1
			if gender:
				terms[gender]=terms.get(gender,0)+1
			if company:
				terms[company]=terms.get(company,0)+1
			if tags:
				for tag in tags:
					if len(tag):
						terms[tag]=terms.get(tag,0)+1 
			user.terms_used=terms
			user.save()
			search=UserSearch()
			search.user=user
			search.terms=data
			search.save()
			search.slug=str(search.id)
			search.save()

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






# Register the urls
user_searches.add_url_rule('/', view_func=ListView.as_view('list'))
user_searches.add_url_rule('/login/', view_func=LoginView.as_view('login'),methods=["GET","POST"])
user_searches.add_url_rule('/logout/', view_func=LogoutView.as_view('logout'),methods=["GET"])
user_searches.add_url_rule('/search', view_func=SearchView.as_view('search'),methods=["GET","POST"])
user_searches.add_url_rule('/<slug>/', view_func=DetailView.as_view('detail'))