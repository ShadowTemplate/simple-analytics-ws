import webapp2


class HomeHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello Thron!')


app = webapp2.WSGIApplication([
    ('/', HomeHandler)
], debug=True)

