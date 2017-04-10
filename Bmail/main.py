#!/usr/bin/env python
import os
import jinja2
import webapp2
import cgi
import json

from google.appengine.api import users
from models import Bmail
from google.appengine.api import urlfetch


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            sign_in = True
            logout_url = users.create_logout_url("/")
            output = {
                "user": user,
                "sign_in": sign_in,
                "logout_url": logout_url,
            }
            return self.render_template("hello.html", output)
        else:
            sign_in = False
            login_url = users.create_login_url("/")
            output = {
                "user": user,
                "sign_in": sign_in,
                "login_url": login_url,
            }
            return self.render_template("sign_out.html", output)

class  NewMessage(BaseHandler):
    def get(self):
        logout_url = users.create_logout_url("/")
        output = {
            "logout_url": logout_url
        }
        return self.render_template("new-message.html", output)

class SaveHandler(BaseHandler):
    def post(self):
        recipient = cgi.escape(self.request.get("to"))
        subject = cgi.escape(self.request.get("subject"))
        message = cgi.escape(self.request.get("message"))

        user = users.get_current_user()
        if user:
            email = user.email()

        save = Bmail(recipient=recipient, subject=subject, message=message, email=email)
        save.put()

        return self.render_template("save.html")

class SentHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            email = user.email()
            messages = Bmail.query(Bmail.email == email).fetch()
            logout_url = users.create_logout_url("/")
            output = {
                "messages": messages,
                "logout_url": logout_url
            }
            return self.render_template("sent.html", output)
        else:
            return self.write("Nisi prijavljen.")

class DetailsHandler(BaseHandler):
    def get(self, details_id):
        message = Bmail.get_by_id(int(details_id))
        output = {
            "message": message
        }
        return self.render_template("details.html", output)

class InboxHandler(BaseHandler):
    def get(self):
        logout_url = users.create_logout_url("/")
        user = users.get_current_user()
        if user:
            email = user.email()
            inbox = Bmail.query(Bmail.recipient == email).fetch()
            output = {
                "inbox": inbox,
                "logout_url": logout_url
            }
            return self.render_template("inbox.html", output)
        else:
            return self.write("Nisi prijavljen.")

class AnswerHandler(BaseHandler):
    def post(self):
        recipient = cgi.escape(self.request.get("to"))
        subject = cgi.escape(self.request.get("subject"))
        message = cgi.escape(self.request.get("answer"))

        user = users.get_current_user()
        if user:
            email = user.email()

        save_answer = Bmail(recipient=recipient, subject=subject, message=message, email=email)
        save_answer.put()

        return self.redirect("/sent")

class WeatherHandler(BaseHandler):
    def get(self):
        url = "https://opendata.si/vreme/report/?lat=47.05&lon=12.92"

        data = urlfetch.fetch(url).content

        json_data = json.loads(data)

        weather = json_data["forecast"]["data"][0]["rain"]
        weather_clouds = json_data["forecast"]["data"][0]["clouds"]

        output = {
            "weather": weather,
            "weather_clouds": weather_clouds
        }

        return self.render_template("weather.html", output)

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/new-message', NewMessage),
    webapp2.Route('/save', SaveHandler),
    webapp2.Route('/sent', SentHandler),
    webapp2.Route('/details/<details_id:\d+>', DetailsHandler),
    webapp2.Route('/inbox', InboxHandler),
    webapp2.Route('/answer', AnswerHandler),
    webapp2.Route('/weather', WeatherHandler),
], debug=True)
