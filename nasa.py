#!/usr/bin/env python

import cgi
import webapp2
import urllib
import urllib2
import json

from google.appengine.ext import ndb
from google.appengine.api import users

DEFAULT_PARENT_NAME = 'default_nasa_root'


def data_key(parent_name=DEFAULT_PARENT_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('SaveSearch', parent_name)


class SearchQuery(ndb.Model):
    author = ndb.UserProperty()
    search_string = ndb.TextProperty()
    search_url = ndb.TextProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


class MainHandler(webapp2.RequestHandler):

    def get(self):

        self.response.out.write("""
            <html>
            <head>
                <link rel="stylesheet" type="text/css" href="/css/main.css">
            </head>
            <body>
            <form action="/search" method="post">
                <div id="search_box" >
                    <input type="text" name="search_string" placeholder="Enter search words">
                    <input type="submit" name="search" title="Search">
                </div>
            </form>
            <div id="search_results">""")

        search_string = self.request.get('search_string')

        if len(search_string) > 0:

            self.response.write(
                "Search results for " + search_string + "</br>")

            params = {'search': search_string}
            url = "http://data.nasa.gov/api/get_search_results/?" + \
                urllib.urlencode(params)

            try:
                result = urllib2.urlopen(url)
                response = result.read()
                # self.response.write(response)
                json_data = json.loads(response)
                self.PrintJsonResult(json_data)

                result.close()

            except urllib2.URLError, e:
                self.response.write(e)

        self.response.out.write("""
            </div>
            <div id="history">""")

        search_query = SearchQuery.query(ancestor=data_key(
            DEFAULT_PARENT_NAME)).order(-SearchQuery.date)
        search_queries = search_query.fetch(10)

        for query in search_queries:
            # if query.author:
            #     self.response.write(
            #         '<b>%s</b> wrote:' % query.author.nickname())
            # else:
            #     self.response.write('An anonymous person wrote:')
            self.response.write('<span>@%s - <a href="%s">%s</a></span></br>' %
                                (query.date, query.search_url, cgi.escape(query.search_string)))

        self.response.out.write("""
            </div>
            </body>
            </html>""")

    def PrintJsonResult(self, json_data):
        if json_data["status"] == "ok":
            count = json_data["count"]
            for post in json_data["posts"]:
                self.response.write('<span>%s - <a href="%s">%s</a></span></br>' % (
                    post["id"], post["url"], post["title"]))


class SaveSearch(webapp2.RequestHandler):

    def post(self):
        search_query = SearchQuery(parent=data_key(DEFAULT_PARENT_NAME))

        if users.get_current_user():
            search_query.author = users.get_current_user()

        search_query.search_string = self.request.get('search_string')
        params = {'search': self.request.get('search_string')}
        url = "http://data.nasa.gov/api/get_search_results/?" + \
            urllib.urlencode(params)
        search_query.search_url = url

        search_query.put()

        query_params = {'search_string': self.request.get('search_string')}
        self.redirect('/?' + urllib.urlencode(query_params))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/search', SaveSearch)
], debug=True)
