class User:
	_userlists = dict()
	_friendlists = dict()

	def __init__(self, id, name, profile_url, about=None, birthday=None, hometown=None):
		self.id = id
		self.name = name
		self.profile_url = profile_url
		self.about = about
		self.birthday = birthday
		self.hometown = hometown
		self.score = 0
		self.user1Clicked = False
		self.user2Clicked = False
		self.count = 0
		self.friend1 = None
		self.friend2 = None

	@classmethod
	def getCurrentUser(cls, id):
		# returns None if user for given id is not present
		return cls._userlists.get(id, None);

	@classmethod
	def addCurrentUser(cls, id, user):
		# id = facebookID
		# user = internal user object
		cls._userlists[id] = user;

	@classmethod
	def getCurrentUserFriendList(cls, id):
		# returns None if friendlists for given user id is not present
		return cls._friendlists.get(id, None)

	@classmethod
	def addCurrentUserFriendList(cls, id, friendlist):
		cls._friendlists[id] = friendlist
