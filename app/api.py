from re import sub
from markdown import markdown
from unicodedata import normalize
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from tornado.web import (
    RequestHandler, UIModule, HTTPError, authenticated)


class BaseHandler(RequestHandler):
    executor = ThreadPoolExecutor(10)

    @property
    def user(self):
        return self.application.user

    @property
    def entries(self):
        return self.application.entries

    @property
    def log(self):
        return self.application.log

    def get_current_user(self):
        user_id = self.get_secure_cookie('blogdemo_user')
        return self.user.get_by_id(int(user_id)) if user_id else None

    @run_on_executor
    def async_exec(self, flag, data):
        if flag == 'get_all':
            out = self.entries.get_all()
            out[:data] if len(out) > data else out
        elif flag == 'get_by_slug':
            out = self.entries.get_by_slug(data)
        elif flag == 'any_user_exists':
            out = bool(self.user.get_one())
        elif flag == 'entries.add':
            out = self.entries.add(data)
        elif flag == 'entries.update':
            out = self.entries.update(data)
        elif flag == 'entries.get_by_id':
            out = self.entries.get_by_id(data)
        elif flag == 'entries.get_by_slug':
            out = self.entries.get_by_slug(data)
        elif flag == 'verify_user':
            out = self.user.verify_user(data['email'], data['password'])
        elif flag == 'hash_pd':
            out = self.user.hash_pd(data)
        elif flag == 'user_id':
            out = self.user.get_by_email(data.get('email')).id \
            if self.user.add(data) else None
        return out


class HomeHandler(BaseHandler):
    '''route: / '''

    @coroutine
    @authenticated
    def get(self):
        entries = yield self.async_exec('get_all', 5)
        self.render('home.html', entries=entries) if entries \
            else self.redirect('/compose')


class EntryHandler(BaseHandler):
    '''route: /entry/([^/]+)'''

    @coroutine
    @authenticated
    def get(self, slug):
        entry = yield self.async_exec('get_by_slug', slug)
        if not entry:
            raise HTTPError(404)
        self.render('entry.html', entry=entry)


class ArchiveHandler(BaseHandler):
    '''route: /archive '''

    @coroutine
    @authenticated
    def get(self):
        entries = yield self.async_exec('get_all', 5)
        self.render('archive.html', entries=entries)


class FeedHandler(BaseHandler):
    '''route: /feed '''

    @coroutine
    @authenticated
    def get(self):
        entries = yield self.async_exec('get_all', 10)
        self.set_header('Content-Type', 'application/atom+xml')
        self.render('feed.xml', entries=entries)


class ComposeHandler(BaseHandler):
    '''route: /compose '''

    @coroutine
    @authenticated
    def get(self):
        id = self.get_argument('id', None)
        if id:
            entry = yield self.async_exec('entries.get_by_id', int(id))
        else:
            entry = None
        self.render('compose.html', entry=entry)

    @coroutine
    @authenticated
    def post(self):
        id = self.get_argument('id', None)
        title = self.get_argument('title')
        text = self.get_argument('markdown')
        html = markdown(text)
        if id:
            entry = yield self.async_exec('entries.get_by_id', int(id))
            if not entry:
                raise HTTPError(404)
            slug = entry.slug
            yield self.async_exec('entries.update', {
                'title': title, 'markdown': text, 'html': html, 'id': int(id)})
        else:
            slug = normalize('NFKD', title).encode(
                'ascii', 'ignore')
            slug = sub(r'[^\w]+', ' ', slug.decode())
            slug = '-'.join(slug.lower().strip().split())
            if not slug:
                slug = 'entry'
            while True:
                e = yield self.async_exec('entries.get_by_slug', slug)
                if not e:
                    break
                slug += '-2'
            yield self.async_exec('entries.add', {
                'user_id': self.current_user.id, 'title': title,
                'slug': slug, 'markdown': text, 'html': html})
        self.redirect('/entry/' + slug)


class AuthCreateHandler(BaseHandler):
    '''route: /auth/create '''

    def get(self):
        self.render('create_author.html', error=None)

    @coroutine
    def post(self):
        hashed_password = yield self.async_exec('gen_hash_pd', self.get_argument('password'))
        user_info = {
            'email': self.get_argument('email'),
            'name': self.get_argument('name'),
            'hashed_password': hashed_password}
        user_id = yield self.async_exec('user_id', user_info)
        if user_id:
            self.set_secure_cookie('blogdemo_user', str(user_id))
            self.redirect(self.get_argument('next', '/'))
        else:
            error = 'some error occur, please check your email, name, password'
            self.render('create_author.html', error=error)


class AuthLoginHandler(BaseHandler):
    '''route: /auth/login '''

    @coroutine
    def get(self):
        user = yield self.async_exec('any_user_exists', None)
        self.render('login.html', error=None) if user \
            else self.redirect('/auth/create')

    @coroutine
    def post(self):
        user = yield self.async_exec('verify_user', {
            'email': self.get_argument('email'),
            'password': self.get_argument('password'),
            })
        if not user:
            self.render('login.html', error='incorrect email or password')
            return
        self.set_secure_cookie('blogdemo_user', str(user.id))
        self.redirect(self.get_argument('next', '/'))


class AuthLogoutHandler(BaseHandler):
    '''route: /auth/logout '''

    def get(self):
        self.clear_cookie('blogdemo_user')
        self.redirect(self.get_argument('next', '/'))


class EntryModule(UIModule):
    def render(self, entry):
        return self.render_string('modules/entry.html', entry=entry)


handlers = [
    ('/', HomeHandler),
    ('/feed', FeedHandler),
    ('/archive', ArchiveHandler),
    ('/compose', ComposeHandler),
    ('/entry/([^/]+)', EntryHandler),
    ('/auth/login', AuthLoginHandler),
    ('/auth/create', AuthCreateHandler),
    ('/auth/logout', AuthLogoutHandler),
]
