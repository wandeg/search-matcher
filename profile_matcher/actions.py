from math import sqrt
from operator import itemgetter
from profile_matcher.models import People


def login(email, password):
	user = None
	valid = False
	try:
		user = People.objects.get(email=email)
	except Exception, e:
		pass
	if user:
		valid = user.check_password(password)
	return [user, valid]


def create_query(**params):
	query = {}
	if 'age' in params:
		if params['age']:
			query['age'] = params['age']
	if 'gender'in params:
		if params['gender']:
			query['gender'] = params['gender']
	if 'company'in params:
		if params['company']:
			query['company'] = params['company']
	if 'tags' in params:
		if params['tags']:
			valid_tags = [tag for tag in params['tags'].split(',')
						if len(tag)]
			query['tags__in'] = valid_tags
	return query


def generateAllSearches():
	people = People.objects.all()
	searches = {}
	for user in people:
		searches[user.guid] = user.unpack_terms()
	return searches


def euclidean_distance(searches, user1, user2):
	"""
	Use the euclidean distance between users to identify
	users with similar search patterns
	"""
	sim = {}
	# create similarity dictionary for all similar searches
	# and initialize each value to 1
	for item in searches[user1]:
		if item in searches[user2]:
			sim[item] = 1
		# if they have no searches in common, return 0
	if len(sim) == 0:
		return 0
	# Add up the squares of all the differences in search frequencies
	sum_of_squares = sum([pow(searches[user1][item]-searches[user2][item], 2)
					for item in sim])
	# Add one to denominator to prevent division by zero error
	# Reciprocate so that higher values are given to people most similar
	return 1.0/(1+sum_of_squares)


def mostSimilar(searches, me, n=3):
	""" Returns the n users most similar to me based on their search terms
	Goes through all users.
	"""
	scores = [(euclidean_distance(searches, me, user), user)
		for user in searches if user != me]
	# Sort the list so the highest scores appear at the top
	scores.sort(reverse=True)
	return scores[0:n]


def getSearchSuggestions(searches, me):
	"""Gets recommendations for a person by using a weighted average
	of every other user's searches. This should not be
	calculated frequently since it grows as n (number of users) and
	m(number of terms they search) grows."""
	totals = {}
	simSums = {}
	for user in searches:
		# don't compare me to myself
		if user == me:
			continue
		sim = euclidean_distance(searches, me, user)

		# ignore scores of zero or lower to prevent division by zero
		if sim <= 0:
			continue
		for term in searches[user]:
			if term not in searches[me] or searches[me][term] == 0:
				# Similarity * number of times user has searched that term
				# to get my expected number of searches
				# for the term
				expected = searches[user][term]*sim
				totals[term] = totals.get(term, 0)+expected
				# Sum the user's similarity to me for every term the
				# user has seached
				simSums[term] = simSums.get(term, 0)+sim

	# Create the normalized list
	rankings = [(total/simSums[term], term) for term, total in totals.items()]
	# Return the sorted list
	rankings.sort(reverse=True)
	return rankings
