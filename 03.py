import facebook
import os.path
import random
import sqlite3
import signal

from User import User
from Common import Common

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.options
import tornado.web
import tornado.ioloop

from tornado.options import define, options

"""
Second degree friend list
http://www.facebook.com/friends.php?id='whatever'

Include How many times you played and some witty comments.
"""

define("port", default=8080, help="run on the given port", type=int)
define("facebook_app_id", help="Facebook Application ID",
	default="144264565621291")
define("facebook_api_key", help="Facebook Application API Key",
	default="6e7de423d7fadb3e3d82b2711845fc38")
define("facebook_app_secret", help="Facebook Application Secret",
	default="e2f6258a62933fd5de53469e861ba0da")


class BaseHandler(tornado.web.RequestHandler):
	def getCookie(self):
		cookies = dict((n, self.cookies[n].value) for n in self.cookies.keys())
		cookie = facebook.get_user_from_cookie(
			cookies, options.facebook_app_id, options.facebook_app_secret)
		return cookie

	def addCurrentUser(self):
		cookie = self.getCookie()
		Common.setGraph(facebook.GraphAPI(cookie["access_token"]))
		profile = Common.graph().get_object("me")
		friends = Common.graph().get_connections("me", "friends")
		User.addCurrentUser(profile["id"], 
								User(str(profile["id"]),
									profile["name"],
									profile.get("link", ""),
									profile.get("about", ""),
									profile.get("birthday", ""),
									profile.get("hometown", {"name":""})["name"]))
		User.addCurrentUserFriendList(profile["id"],
										friends["data"])

	'''def initializeDB(self):
		cookie = self.getCookie()
		Common.setGraph(facebook.GraphAPI(cookie["access_token"]))
		profile = Common.graph().get_object("me")
		friends = Common.graph().get_connections("me", "friends")
		# set currentUser to me
		User.setCurrentUser(User(str(profile["id"]),
								profile["name"],
								profile.get("link", ""),
								profile.get("about", ""),
								profile.get("birthday", ""),
								profile.get("hometown", {"name":""})["name"]))
		# insert me
		DB.execute("insert into profile(fid, name, profile_url, about, birthday, hometown) values (?, ?, ?, ?, ?, ?)",
			profile["id"],
			profile["name"],
			profile.get("link", ""),
			profile.get("about", ""),
			profile.get("birthday", ""),
			profile.get("hometown", {"name":""})["name"])
		# insert all friends
		for friend in friends["data"]:
			profile = Common.graph().get_object(str(friend["id"]))
			DB.execute("insert into profile (fid, name, profile_url, about, birthday, hometown) values (?, ?, ?, ?, ?, ?)",
				profile["id"],
				profile["name"],
				profile.get("link", ""),
				profile.get("about", ""),
				profile.get("birthday", ""),
				profile.get("hometown", {"name":""})["name"])
			DB.execute("insert into friends (fid, name, score) values (?, ?, ?)", profile["id"], profile["name"], 0)
	'''	
	def get_current_user(self):
		cookie = self.getCookie()
		self.addCurrentUser()
		return User.getCurrentUser(cookie["uid"])

class MainHandler(BaseHandler):
	def get(self):
		cookie = self.getCookie()
		currentUser = User.getCurrentUser(cookie["uid"])
		if currentUser is None:
			self.redirect("/auth/login")
			return
		page = 0
		has_friends = False
		'''cursor = DB.execute("select count(*) from friends")
		row = DB.fetchone(cursor)
		if row is None:
			has_friends = False
		else:
			has_friends = True'''
		if len(User.getCurrentUserFriendList(cookie["uid"])) > 0:
			has_friends = True
		self.render("template.html", options=options, page = page, current_user=currentUser, count=currentUser.count, has_friends = has_friends);

class FaceHandler(BaseHandler):
	def get(self):
		cookie = self.getCookie()
		currentUser = User.getCurrentUser(cookie["uid"])
		if currentUser is None:
			self.redirect("/auth/login")
			return
		page = 2
		currentUser.count += 1
		self.render("template.html", options=options, page = page, current_user=currentUser, has_friends = True);
	
	def post(self):
		if str(self.get_argument("clicked")) == "user1":
			currentUser.user1Clicked = True
			currentUser.user2Clicked = False
			update_ranking(currentUser.friend1, currentUser.friend2)
		elif str(self.get_argument("clicked")) == "user2":
			currentUser.user1Clicked = False
			currentUser.user2Clicked = True
			update_ranking(currentUser.friend2, currentUser.friend1)
		self.redirect("/facemesh")

class LoginHandler(BaseHandler):
	def get(self):
		page = 1
		self.render("login.html", options=options, page=page);

class DeveloperHandler(BaseHandler):
	def get(self):
		cookie = self.getCookie()
		currentUser = User.getCurrentUser(cookie["uid"])
		if currentUser is None:
			self.redirect("/auth/login")
			return
		page = 3
		self.render("template.html", options=options, page=page, current_user=currentUser, count=currentUser.count, has_friends = True);

class GuessHandler(BaseHandler):
	def get(self):
		cookie = self.getCookie()
		currentUser = User.getCurrentUser(cookie["uid"])
		if currentUser is None:
			self.redirect("/auth/login")
			return
		page = 4
		currentUser.count += 1
		has_friends = False
		'''cursor = DB.execute("select count(*) from friends")
		row = DB.fetchone(cursor)
		if row is None:
			has_friends = False
		else:
			has_friends = True'''
		if len(User.getCurrentUserFriendList(cookie["uid"])) > 0:
			has_friends = True
		self.render("template.html", options=options, page=page, current_user=currentUser, has_friends = has_friends);
	
	def post(self):
		if str(self.get_argument("post_name")) == mystery["name"]:
			Common.setMystery_Correct(True)
			# Increase score
		elif str(self.get_argument("birthday")) == mystery["birthday"]:
			Common.setMystery_Correct(True)
			# Increase score
		else:
			Common.setMystery_Correct(False)
		self.redirect("/guess")

class CountModule(tornado.web.UIModule):
	def render(self, currentUser):
		if currentUser.count < 50:
			count_message = ""
		elif currentUser.count < 100:
			count_message = "You're awesome!\n You played " + \
								str(currentUser.count) + " times."
		elif currentUser.count < 500:
			count_message = "You are bored.. aren't ya?\n You played " + \
								str(currentUser.count) + " times."
		elif currentUser.count < 1000:
			count_message = "Having fun? " + str(currentUser.count) + " times."
		elif currentUser.count >= 1000:
			count_message = "... " + str(currentUser.count)
		else:
			count_message = "Are you trying something funny? We are watching you! " + \
								str(currentUser.count)
		return self.render_string("modules/count.html", count=currentUser.count,
					count_message=count_message)

class RankModule(tornado.web.UIModule):
	def render(self, rank):
		# Get appropriate RANK ID FROM DATABASE
		# FOR NOW JUST PLUGIN TO FRIEND LIST
		cursor = DB.execute("select fid, name from profile order by score desc limit 5;")
		for i in range(0, rank):
			row = DB.fetchone(cursor)

		power_user = None
		if row != None:
			power_user = User(
							id = str(row[0]),
							name = row[1]
							)
		return self.render_string("modules/rank.html", power_user=power_user)

class GuessModule(tornado.web.UIModule):
	def render(self, currentUser):
		friendlist = User.getCurrentUserFriendList(currentUser.id)
		num_friends = len(friendlist)
		index = random.randint(0, num_friends-1)
		'''cursor = DB.execute("select fid, name, profile_url, about, birthday, hometown from profile order by random() limit 1;")
		row = DB.fetchone(cursor)
		mystery = User(
			id = str(row[0]),
			name = row[1],
			profile_url = row[2],
			about = row[3],
			birthday = row[4],
			hometown = row[5]
		)'''
		mystery = User(
					id = str(friendlist[index]["id"]),
					name = friendlist[index]["name"],
					profile_url = "",
					about = "",
					birthday = "",
					hometown = ""
					)

		# check if exists in DB; if not store
		cursor = DB.execute("select id from profile where id = ?", mystery.id)
		row = DB.fetchone(cursor)
		if len(row) == 0:
			DB.execute("insert into profile(fid, name) values (?, ?)",
				mystery.id, mystery.name)
		return self.render_string("modules/guess.html", mystery=mystery)

class FriendModule(tornado.web.UIModule):
	def render(self, currentUser):
		if currentUser.user1Clicked:
			pass
		else:
			'''cursor = DB.execute("select fid, name, profile_url, about, birthday, hometown from profile order by random() limit 1;")
			row = DB.fetchone(cursor)
			friend1 = User(
				id = str(row[0]),
				name = row[1],
				profile_url = row[2],
				about = row[3],
				birthday = row[4],
				hometown = row[5],
			)'''
			friendlist = User.getCurrentUserFriendList(currentUser.id)
			index = random.randint(0, len(friendlist)-1)
			friend1 = User(
						id = str(friendlist[index]["id"]),
						name = friendlist[index]["name"],
						profile_url = "",
						about = "",
						birthday = "",
						hometown = ""
						)
			# check if exists in DB; if not store
			cursor = DB.execute("select id from profile where id = ?", friend1.id)
			row = DB.fetchone(cursor)
			if row != None and len(row) == 0:
				DB.execute("insert into profile (fid, name) values (?, ?)",
						friend1.id, friend1.name)
			currentUser.friend1 = friend1
		if currentUser.user2Clicked:
			pass
		else:
			'''cursor = DB.execute("select fid, name, profile_url, about, birthday, hometown from profile order by random() limit 2;")
			row = DB.fetchone(cursor)
			if row[0] == int(friend1.id):
				row = DB.fetchone(cursor)
			friend2 = User(
				id = str(row[0]),
				name = row[1],
				profile_url = row[2],
				about = row[3],
				birthday = row[4],
				hometown = row[5]
			)'''
			friendlist = User.getCurrentUserFriendList(currentUser.id)
			index = random.randint(0, len(friendlist)-1)
			friend2 = User(
						id = str(friendlist[index]["id"]),
						name = friendlist[index]["name"],
						profile_url = "",
						about = "",
						birthday = "",
						hometown = ""
						)
			cursor = DB.execute("select id from profile where id = ?", friend2.id)
			row = DB.fetchone(cursor)
			if len(row) == 0:
				DB.execute("insert into profile(fid, name) values (?, ?)",
					friend2.id, friend2.name)
			currentUser.friend2 = friend2
		return self.render_string("modules/friend.html",
					friend=currentUser.friend1,
					friend2=currentUser.friend2,
					user1_clicked=currentUser.user1Clicked,
					user2_clicked=currentUser.user2Clicked)

class DeveloperModule(tornado.web.UIModule):
	def render(self):
		'''cursor = DB.execute("select * from profile where fid = ?", 503655210)
		row = DB.fetchone(cursor)
		developer = User(
			id = str(row[1]),
			name = row[2],
			profile_url = row[3],
			about = row[4],
			birthday = row[5],
			hometown = row[6]
		)
		cursor = DB.execute("select * from profile where fid = ?", 122609369)
		row = DB.fetchone(cursor)
		developer2 = User(
			id = str(row[1]),
			name = row[2],
			profile_url = row[3],
			about = row[4],
			birthday = row[5],
			hometown = row[6]
		)'''
		developer = User.getCurrentUser(503655210)
		developer = User.getCurrentUser(122609369)
		return self.render_string("modules/developers.html", developer=developer, developer2=developer2)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler), # ID: 0
			(r"/auth/login", LoginHandler), # ID: 1
			(r"/facemesh", FaceHandler), # ID: 2
			(r"/developers", DeveloperHandler), # ID: 3
			(r"/guess", GuessHandler), # ID: 4
        ]
        settings = dict(
			#cookie_secret="12oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
			login_url="/auth/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
			#xsrf_cookies=True,
            facebook_api_key=options.facebook_api_key,
			ui_modules = {"Friend": FriendModule, "Developer": DeveloperModule, "Guess": GuessModule, "Rank": RankModule, "Count": CountModule},
            facebook_secret=options.facebook_app_secret,
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class DB():
	conn = None
	
	@classmethod
	def connect(cls, dbname):
		cls.conn = sqlite3.connect(dbname)

	@classmethod
	def execute(cls, query, *argv):
		cursor = cls.conn.cursor()
		if len(argv) == 0:
			cursor.execute(query)
		else:
			cursor.execute(query, argv)
		cls.conn.commit()
		return cursor

	@classmethod
	def fetchone(cls, cursor):
		return cursor.fetchone()

	@classmethod
	def close(cls):
		cls.conn.close()

def signal_handler(signal, frame):
	print "closing db connection"
	DB.close()
	sys.exit(0)

#user1 is winner
def update_ranking(user1, user2):
	K0 = 15
	Q0 = 10 ** (float(user1.score)/400)
	Q1 = 10 ** (float(user2.score)/400)
	E0 = Q0 / (Q0 + Q1)
	E1 = Q1 / (Q0 + Q1)
	user1.score += int(K0 * (1 - E0))
	user2.score += int(K0 * (0 - E1))
	if user1.score < 0:
		user1.score = 0
	if user2.score < 0:
		user2.score = 0
	
	DB.execute("update friends set score=? where fid = ?", user1.score, user1.id)
	DB.execute("update friends set score=? where fid = ?", user2.score, user2.id)
	
		
def main():
	signal.signal(signal.SIGINT, signal_handler)
	random.seed()
	DB.connect('facemash.db')
	#DB.execute("drop table friends")	# table used for facemash
	#DB.execute("drop table profile")	# table used for detailed profile
	#DB.execute("create table friends(id integer primary key, fid integer, name text, score integer)")
	DB.execute("create table profile(id integer primary key, fid integer, name text, profile_url text, about text, birthday text, hometown text)")
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
