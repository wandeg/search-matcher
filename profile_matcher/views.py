from flask import Blueprint, request, redirect, render_template, url_for
from flask.views import MethodView
from profile_matcher.models import UserSearch, Result

user_searches = Blueprint('user_searches', __name__, template_folder='templates')


class ListView(MethodView):

    def get(self):
        user_searches = UserSearch.objects.all()
        return render_template('user_searches/list.html', user_searches=user_searches)


class DetailView(MethodView):

    def get(self, slug):
        search = UserSearch.objects.get_or_404(slug=slug)
        return render_template('user_searches/detail.html', search=search)


# Register the urls
user_searches.add_url_rule('/', view_func=ListView.as_view('list'))
user_searches.add_url_rule('/<slug>/', view_func=DetailView.as_view('detail'))