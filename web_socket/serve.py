#!/usr/bin/env python

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import base64

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/mapsocket", MapSocketHandler),
        ]
        settings = dict(
            cookie_secret=base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            login_url="/login",
        )
        tornado.web.Application.__init__(self, handlers, **settings)

""" This handler renders the main page "index.html", but 
requires an authentication. Therefore, it redirects to the
LoginHandler, if no user is found in the cookie
"""
class MainHandler(tornado.web.RequestHandler):
    @tornado.web.authenticated
    def get(self):
        tempusers=dict()
        for user in MapSocketHandler.sock_users.values():
            if user in MapSocketHandler.users:
                tempusers[user] = MapSocketHandler.users[user]
        self.render("index.html", usermap=tempusers,
                user_name=self.get_secure_cookie("user"))

""" This handler takes care of authentication,
which is very rudimentary and only asks for a user name and a
desired color. The color should be specified as "#HHHHHH",
where H is an uppercase hexadecimal
"""
class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.set_secure_cookie("color", self.get_argument("color"))
        self.redirect("/")

""" This Handler serves the websockets and keeps track of all connected
users and their information. On opening of a websocket, the user information
like color and positions are sent to the current connection websocket.
When a message is received by this handler, the user map will be updated
and then the new message is broadcasted to all other users.
"""

class MapSocketHandler(tornado.websocket.WebSocketHandler):
    sock_users = dict()
    users = dict()

    def allow_draft76(self):
        # for iOS 5.0 Safari
        return True

    def open(self):
        user_name=self.get_secure_cookie("user")
        logging.info("opening websocket for user: %s", user_name)
        if user_name:
            color=self.get_secure_cookie("color")
            MapSocketHandler.sock_users[self]=user_name
            if MapSocketHandler.users.get(user_name) is None:
                MapSocketHandler.users[user_name]=(color, 0, 0)
            msg = {
                "user": tornado.escape.to_basestring(user_name),
                "color": tornado.escape.to_basestring(color),
                "x": MapSocketHandler.users[user_name][1],
                "y": MapSocketHandler.users[user_name][2],
                }
            MapSocketHandler.send_updates(msg)
            self.send_initial_updates(user_name)

    def on_close(self):
        user_name=self.get_secure_cookie("user")
        logging.info("closing websocket for user: %s", user_name)
        del MapSocketHandler.sock_users[self]

    def update_user(self, user, parsed):
        color=self.get_secure_cookie("color")
        entry=(color, parsed["x"], parsed["y"])
        self.users[user]=entry

    def send_initial_updates(self, user_name):
        logging.info("sending initial updates to user %s", user_name)
        for sock_user in MapSocketHandler.sock_users.values():
            user_info=MapSocketHandler.users.get(sock_user)
            if user_info and (sock_user != user_name):
                logging.info("sending updates from %s to %s", sock_user, user_name)
                msg = {
                    "user": tornado.escape.to_basestring(sock_user),
                    "color": tornado.escape.to_basestring(user_info[0]),
                    "x": user_info[1],
                    "y": user_info[2],
                    }
                try:
                    self.write_message(msg)
                except:
                    logging.error("Error sending message", exc_info=True)

    @classmethod
    def send_updates(cls, msg):
        logging.info("sending message to %d users", len(cls.sock_users))
        for user in cls.sock_users:
            try:
                logging.info("sending to %s", MapSocketHandler.sock_users[user])
                user.write_message(msg)
            except:
                logging.error(MapSocketHandler.sock_users)
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        user_name=self.get_secure_cookie("user")
        if user_name:
            parsed = tornado.escape.json_decode(message)
            color=self.get_secure_cookie("color")
            self.update_user(user_name, parsed)
            msg = {
                "user": tornado.escape.to_basestring(user_name),
                "color": tornado.escape.to_basestring(color),
                "x": parsed["x"],
                "y": parsed["y"],
                }
            MapSocketHandler.send_updates(msg)

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
