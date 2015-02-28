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