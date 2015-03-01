from math import sqrt
from profile_matcher.models import People

def login(email,password):
	user=None
	valid=False
	try:
		user=People.objects.get(email=email)
	except Exception, e:
		pass
	if user:
		valid=user.check_password(password)
	return [user,valid]

def create_query(**params):
	query={}
	if 'age' in params:
		if params['age']:
			query['age']=params['age']
	if 'gender'in params:
		if params['gender']:
			query['gender']=params['gender']
	if 'company'in params:
		if params['company']:
			query['company']=params['company']
	if 'tags' in params:
		if params['tags']:
			valid_tags=[tag for tag in params['tags'].split(',') 
						if len(tag) ]
			query['tags__in']=valid_tags
	return query

def generateAllSearches():
	people=People.objects.all()
	searches={}
	for user in people:
		searches[user.guid]=user.unpack_terms()
	return searches

def pearson(searches,user1,user2):
	"""
	Use pearson's product moment correlation coeffecient to get
	users with similar	search patterns
	"""
	# Get the commonly searched terms
	common={}
	for item in searches[user1]: 
		if item in searches[user2]: 
			common[item]=1


	if len(common)==0: return 0


	n=len(common)
	print searches[user1]
	print [i for i in common]

	# Sums the searches for the common terms for each person
	sum1=sum([searches[user1][term] for term in common])
	sum2=sum([searches[user2][term] for term in common])

	# Sums of the squares of the searches for each common term
	sum1Sq=sum([pow(searches[user1][term],2) for term in common])
	sum2Sq=sum([pow(searches[user2][term],2) for term in common])	

	# Sum of the products
	prodSum=sum([searches[user1][term]*searches[user2][term] for term in common])

	num=prodSum-(sum1*sum2/n)
	den=sqrt((sum1Sq-pow(sum1,2)/n)*(sum2Sq-pow(sum2,2)/n))
	if den==0: return 0

	similarity=num/den

	return similarity

def mostSimilar(searches,me,n=3):
	""" Returns the n users most similar to me based on their search terms
	Goes through all users.
	"""
	scores=[(pearson(searches,me,user),user)
		for user in searches if user!=me]
	# Sort the list so the highest scores appear at the top
	scores.sort(reverse=True)
	return scores[0:n]


def getSearchSuggestions(searches,me):
	"""Gets recommendations for a person by using a weighted average
	of every other user's searches. This should not be
	calculated frequently since it grows as n (number of users) and 
	m(number of terms they search) grows."""
	totals={}
	simSums={}
	for user in searches:
		# don't compare me to myself
		if user==me: 
			continue
		sim=pearson(searches,me,user)

		# ignore scores of zero or lower to prevent division by zero
		if sim<=0: 
			continue
		for term in searches[user]:
			if term not in searches[me] or searches[me][term]==0:
				# Similarity * number of times user has searched that term
				# to get my expected number of searches
				# for the term
				expected=searches[user][term]*sim
				totals[term]=totals.get(term,0)+expected
				# Sum the user's similarity to me for every term the
				# user has seached
				simSums[term]=simSums.get(term,0)+sim

	# Create the normalized list
	rankings=[(total/simSums[term],term) for term,total in totals.items()]

	# Return the sorted list
	rankings.sort(reverse=True)
	return rankings

def invertSearches(searches):
	"""
	Flips the search dictionary from {user:searchterms} to {searchterm:users}
	"""
	result={}
	for user in searches:
		for term in searches[user]:
			result[term]=result.get(term,{})
			# Flip term and user
			result[term][user]=searches[user][term]
	return result

def getSimilarTerms(searches,n=10):
	"""Create a dictionary of each term showing which other terms they
				are most similar to."""
	result={}
	# Invert the search matrix to be term-centric
	termSearches=invertSearches(searches)
	for term in termSearches:
		# Find the most similar terms to this one
		scores=mostSimilar(termSearches,term,n=n)
		result[term]=scores
	return result