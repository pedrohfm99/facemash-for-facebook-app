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

	def initializeCurrentUser(self):
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

	def initializeDB(self):
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
		
	def get_current_user(self):
		if Common.initialized() == False:
			#self.initializeDB()
			self.initializeCurrentUser()
			Common.setInitialized(True)
		return User.currentUser()

class MainHandler(BaseHandler):
	def get(self):
		if User.currentUser() is None:
			self.redirect("/auth/login")
			return
		page = 0
		has_friends = False
		cursor = DB.execute("select count(*) from friends")
		row = DB.fetchone(cursor)
		if row is None:
			has_friends = False
		else:
			has_friends = True
		self.render("template.html", options=options, page = page, current_user=User.currentUser(), count=User.count(), has_friends = has_friends);

class FaceHandler(BaseHandler):
	def get(self):
		if User.currentUser() is None:
			self.redirect("/auth/login")
			return
		page = 2
		User.setCount(User.count()+1)
		self.render("template.html", options=options, page = page, current_user=User.currentUser(), has_friends = True);
	
	def post(self):
		if str(self.get_argument("clicked")) == "user1":
			User.setUserClicked(1)
			update_ranking(User.friend1(), User.friend2())
		elif str(self.get_argument("clicked")) == "user2":
			User.setUserClicked(2)
			update_ranking(User.friend2(), User.friend1())
		self.redirect("/facemesh")

class LoginHandler(BaseHandler):
	def get(self):
		page = 1
		self.render("login.html", options=options, page=page);

class DeveloperHandler(BaseHandler):
	def get(self):
		if User.currentUser() is None:
			self.redirect("/auth/login")
			return
		page = 3
		self.render("template.html", options=options, page=page, current_user=User.currentUser(), count=User.count(), has_friends = True);

class GuessHandler(BaseHandler):
	def get(self):
		if User.currentUser() is None:
			self.redirect("/auth/login")
			return
		page = 4
		User.setCount(User.count()+1)
		has_friends = False
		cursor = DB.execute("select count(*) from friends")
		row = DB.fetchone(cursor)
		if row is None:
			has_friends = False
		else:
			has_friends = True
		self.render("template.html", options=options, page=page, current_user=User.currentUser(), has_friends = has_friends);
	
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
	def render(self):
		if User.count() < 50:		count_message = ""
		elif User.count() < 100:	count_message = "You're awesome!\n You played " + str(User.count()) + " times."
		elif User.count() < 500:	count_message = "You are bored.. aren't ya?\n You played " + str(User.count()) + " times."
		elif User.count() < 1000:	count_message = "Having fun? " + str(User.count()) + " times."
		elif User.count() >= 1000:	count_message = "... " + str(User.count())
		else:				count_message = "Are you trying something funny? We are watching you! " + str(User.count())
		return self.render_string("modules/count.html", count=User.count(), count_message=count_message)

class RankModule(tornado.web.UIModule):
	def render(self, rank):
		# Get appropriate RANK ID FROM DATABASE
		# FOR NOW JUST PLUGIN TO FRIEND LIST
		cursor = DB.execute("select fid, name from friends order by score desc limit 5;")
		for i in range(0, rank):
			row = DB.fetchone(cursor)

		cursor2 = DB.execute("select profile_url from profile where fid = ?", row[0])
		row2 = DB.fetchone(cursor2)
		power_user = User(
			id = str(row[0]),
			name = row[1],
			profile_url = row2[0]
		)
		return self.render_string("modules/rank.html", power_user=power_user)

class GuessModule(tornado.web.UIModule):
	def render(self):
		cursor = DB.execute("select fid, name, profile_url, about, birthday, hometown from profile order by random() limit 1;")
		row = DB.fetchone(cursor)
		mystery = User(
			id = str(row[0]),
			name = row[1],
			profile_url = row[2],
			about = row[3],
			birthday = row[4],
			hometown = row[5]
		)
		return self.render_string("modules/guess.html", mystery=mystery)

class FriendModule(tornado.web.UIModule):
	def render(self):
		if User.user1Clicked():
			friend1 = User.friend1()
		else:
			cursor = DB.execute("select fid, name, profile_url, about, birthday, hometown from profile order by random() limit 1;")
			row = DB.fetchone(cursor)
			friend1 = User(
				id = str(row[0]),
				name = row[1],
				profile_url = row[2],
				about = row[3],
				birthday = row[4],
				hometown = row[5],
			)
			User.setFriend1(friend1)
		if User.user2Clicked():
			friend2 = User.friend2()
		else:
			cursor = DB.execute("select fid, name, profile_url, about, birthday, hometown from profile order by random() limit 2;")
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
			)
			User.setFriend2(friend2)
		return self.render_string("modules/friend.html", friend=friend1, friend2=friend2, user1_clicked=User.user1Clicked(), user2_clicked=User.user2Clicked())

class DeveloperModule(tornado.web.UIModule):
	def render(self):
		cursor = DB.execute("select * from profile where fid = ?", 503655210)
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
		)
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
	#DB.execute("create table profile(id integer primary key, fid integer, name text, profile_url text, about text, birthday text, hometown text)")
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
