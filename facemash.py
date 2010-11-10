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


class User():
    id = ""
    name = ""
    about = ""
    access_token = ""
    clicked = False

class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    cookie = None
    @property
    def current_user1(self):
        if not hasattr(self, "_current_user1"):
            self._current_user1 = None
            if self.cookie == None :
                self.cookie = facebook.get_user_from_cookie(
                    self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if self.cookie :
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                graph = facebook.GraphAPI(self.cookie["access_token"])
                #profile = graph.get_object("me")
                friends = graph.get_connections("me", "friends")
                friend_length = len(friends["data"])
                index = random.randint(1, friend_length)-1
                friend1 = friends["data"][index]
                #friend_profile = graph.get_object(str(friend1["id"]))
                #ppic = db.Blob(urlfetch.Fetch(
                #    "https://graph.facebook.com/" + str(friend1["id"]) + "/picture?type=large&width=400&height=300&" +
                #    cookie["access_token"]).content)
                user1 = User()
                user1.id = friend1["id"]
                user1.name = friend1["name"]
                #user1.about = friend_profile.get("about", "")
                user1.access_token = self.cookie["access_token"]
                self._current_user1 = user1
        return self._current_user1

    @property
    def current_user2(self):
        if not hasattr(self, "_current_user2") :
            self._current_user2 = None
            if self.cookie == None :
                self.cookie = facebook.get_user_from_cookie(
                    self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if self.cookie:
                graph = facebook.GraphAPI(self.cookie["access_token"])
                #profile = graph.get_object("me")
                friends = graph.get_connections("me", "friends")
                friend_length = len(friends["data"])
                index = random.randint(1, friend_length)-1
                friend2 = friends["data"][index]
                #friend_profile = graph.get_object(str(friend2["id"]))
                #ppic = db.Blob(urlfetch.Fetch(
                #    "https://graph.facebook.com/" + str(friend2["id"]) + "/picture?type=large&width=400&height=300&" +
                #    cookie["access_token"]).content)
                user2 = User()
                user2.id = friend2["id"]
                user2.name = friend2["name"]
                #user2.about = friend_profile.get("about","")
                user2.access_token = self.cookie["access_token"]
                self._current_user2 = user2
        return self._current_user2
    

class HomeHandler(BaseHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), "facemash.html")
        args = dict(current_user1=self.current_user1,
                    current_user2=self.current_user2,
                    user1_clicked=self.request.get("user1"),
                    user2_clicked=self.request.get("user2"),
                    facebook_app_id=FACEBOOK_APP_ID)
        self.response.out.write(template.render(path, args))

    def post(self):
        self.get()

def main():
    random.seed()
    util.run_wsgi_app(webapp.WSGIApplication([(r"/", HomeHandler)]))

if __name__ == "__main__":
    main()
