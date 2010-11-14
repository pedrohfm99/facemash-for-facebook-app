class User:
	_currentUser = None
	_user1_clicked = False
	_user2_clicked = False
	_count = 0
	_friend1 = None
	_friend2 = None

	def __init__(self, id, name, profile_url, about=None, birthday=None, hometown=None):
		self.id = id
		self.name = name
		self.profile_url = profile_url
		self.about = about
		self.birthday = birthday
		self.hometown = hometown
		self.score = 0

	@classmethod
	def currentUser(cls):
		return cls._currentUser

	@classmethod
	def setCurrentUser(cls, user):
		cls._currentUser = user

	@classmethod
	def user1Clicked(cls):
		if cls._user1_clicked:
			return True
		else:
			return False

	@classmethod
	def user2Clicked(cls):
		if cls._user2_clicked:
			return True
		else:
			return False

	@classmethod
	def setUserClicked(cls, i):
		if i == 1:
			cls._user1_clicked = True
			cls._user2_clicked = False
		elif i == 2:
			cls._user1_clicked = False
			cls._user2_clicked = True

	@classmethod
	def count(cls):
		return cls._count

	@classmethod
	def setCount(cls, count):
		cls._count = count

	@classmethod
	def friend1(cls):
		return cls._friend1

	@classmethod
	def setFriend1(cls, friend1):
		cls._friend1 = friend1

	@classmethod
	def friend2(cls):
		return cls._friend2

	@classmethod
	def setFriend2(cls, friend2):
		cls._friend2 = friend2
