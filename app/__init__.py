from os.path import join, dirname

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.options import parse_command_line

from configparser import ConfigParser
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from .log import PrettyPrintLog

config = ConfigParser()
config.read('config')
Base = declarative_base()
engine = create_engine(
    config['DB']['url'], poolclass=pool.QueuePool,
    pool_size=256, max_overflow=256)  # , echo=True)
DBSession = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))
p = PrettyPrintLog()


class Application(Application):
    def __init__(self):
        from .api import handlers, EntryModule
        from .orm import User, Entries
        settings = dict(
            debug=True,
            autoreload=True,
            # xsrf_cookies=True,
            blog_title='Blog',
            login_url='/auth/login',
            ui_modules={'Entry': EntryModule},
            static_path=join(dirname(__file__), 'static'),
            template_path=join(dirname(__file__), 'templates'),
            cookie_secret='__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__',
        )
        super().__init__(handlers, **settings)

        self.user = User()
        self.entries = Entries()
        self.log = PrettyPrintLog()

        self.init_database()

    @staticmethod
    def init_database():
        Base.metadata.create_all(engine)


def main():
    p.normal('start server ...')
    parse_command_line()
    http_server = HTTPServer(Application())
    http_server.listen(config['base']['port'])
    IOLoop.current().start()
