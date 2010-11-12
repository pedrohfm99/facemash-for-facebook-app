#!/usr/bin/env python
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A barebones AppEngine application that uses Facebook for login."""

FACEBOOK_APP_ID = "144264565621291"
FACEBOOK_APP_SECRET = "e2f6258a62933fd5de53469e861ba0da"

import facebook
import os.path
import wsgiref.handlers
import urllib
import random

from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import images
from google.appengine.api import urlfetch


class User(db.Model):
    id = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    score = db.IntegerProperty(required=True)
    access_token = db.StringProperty(required=True)

class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    num_friends = 0
    ids = list()
    user1_clicked = False
    user2_clicked = False
    prev_user1 = None
    prev_user2 = None
    initialized = False

    def initializeDB(self):
        self.cookie = facebook.get_user_from_cookie(
            self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
        if self.cookie :
            graph = facebook.GraphAPI(self.cookie["access_token"])
            friends = graph.get_connections("me", "friends")
            self.__class__.num_friends = len(friends["data"])
            for friend in friends["data"] :
                user = User(key_name=str(friend["id"]),
                            id=str(friend["id"]),
                            name=friend["name"],
                            score=0,
                            access_token=self.cookie["access_token"])
                user.put()
                self.__class__.ids.append(str(friend["id"]))
       
    @property
    def current_user1(self):
        if not hasattr(self, "_current_user1"):
            if self.__class__.user1_clicked:
                self._current_user1 = self.__class__.prev_user1
            else:
                self._current_user1 = None
                index = random.randint(1, self.__class__.num_friends)-1
                id = self.__class__.ids[index]
                query = User.gql("where id = :1", id)
                user1 = query.get()
                self._current_user1 = user1
                self.__class__.prev_user1 = user1
        return self._current_user1

    @property
    def current_user2(self):
        if not hasattr(self, "_current_user2"):
            if self.__class__.user2_clicked:
                self._current_user2 = self.__class__.prev_user2
            else:
                self._current_user2 = None
                index = random.randint(1, self.__class__.num_friends)-1
                id = self.__class__.ids[index]
                query = User.gql("where id = :1", id)
                user2 = query.get()
                self._current_user2 = user2
                self.__class__.prev_user2 = user2
        return self._current_user2

    @property
    def current_user1_rank(self):
        query = db.GqlQuery("select * from User where score > :1 order by score desc", self.current_user1.score)
        return str(query.count()+1)

    @property
    def current_user2_rank(self):
        query = db.GqlQuery("select * from User where score > :1 order by score desc", self.current_user2.score)
        return str(query.count()+1)

class HomeHandler(BaseHandler):
    def get(self):
        if self.__class__.initialized == False:
            self.initializeDB()
            self.__class__.initialized = True
        path = os.path.join(os.path.dirname(__file__), "facemash.html")
        args = dict(current_user1=self.current_user1,
                    current_user2=self.current_user2,
                    current_user1_rank=self.current_user1_rank,
                    current_user2_rank=self.current_user2_rank,
                    user1clicked=self.__class__.user1_clicked,
                    user2clicked=self.__class__.user2_clicked,
                    facebook_app_id=FACEBOOK_APP_ID)
        self.response.out.write(template.render(path, args))

    def post(self):
        if self.request.get("clicked") == "user1" :
            self.__class__.user1_clicked = True
            self.__class__.user2_clicked = False
            # (winner, looser)
            self.update_ranking(self.current_user1.score, self.current_user2.score, 0)
        if self.request.get("clicked") == "user2" :
            self.__class__.user2_clicked = True
            self.__class__.user1_clicked = False
            self.update_ranking(self.current_user2.score, self.current_user1.score, 1)
        self.get()

    def update_ranking(self, score, opponent, winner):
        K0 = 15
        Q0 = 10 ** (float(score)/400)
        Q1 = 10 ** (float(opponent)/400)
        E0 = Q0 / (Q0 + Q1)
        E1 = Q1 / (Q0 + Q1)
        if winner == 0:
            self.current_user1.score = score + int(K0 * (1 - E0))
            self.current_user2.score = opponent + int(K0 * (0 - E1))
        else:
            self.current_user2.score = score + int(K0 * (1 - E0))
            self.current_user1.score = opponent + int(K0 * (0 - E1))
        if self.current_user1.score < 0:
            self.current_user1.score = 0
        if self.current_user2.score < 0:
            self.current_user2.score = 0
        self.current_user1.put()
        self.current_user2.put()


def main():
    random.seed()
    #db.delete(User.all())
    util.run_wsgi_app(webapp.WSGIApplication([(r"/", HomeHandler)]))

if __name__ == "__main__":
    main()
