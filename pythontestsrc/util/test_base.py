import unittest

import factory
from flask.json import JSONDecoder as FlaskJSONDecoder

from app import app
from util.access_util import ATN_HEADER

from sqlalchemy.orm import Session
from flask.testing import FlaskClient

versioned_session(Session)
scoped_session = db.create_scoped_session()


class AppTestClient(FlaskClient):
    """
    Tweak the Flask test client to mark sent content as JSON and to ignore cookies by default.
    """

    def _set_default_content_type(self, kw):
        kw['content_type'] = kw.get('content_type', 'application/json')

    def _set_default_authentication_header(self, kw):
        if 'headers' in kw and ATN_HEADER in kw['headers']:
            return
        kw.setdefault('headers', {})[ATN_HEADER] = 'User1@sainsburys.co.uk'

    def __init__(self, *args, **kw):
        kw['use_cookies'] = kw.get('use_cookies', False)
        return super().__init__(*args, **kw)

    def get(self, *args, **kw):
        self._set_default_authentication_header(kw)
        return super().get(*args, **kw)

    def patch(self, *args, **kw):
        self._set_default_content_type(kw)
        self._set_default_authentication_header(kw)
        return super().patch(*args, **kw)

    def post(self, *args, **kw):
        self._set_default_content_type(kw)
        self._set_default_authentication_header(kw)
        return super().post(*args, **kw)

    def put(self, *args, **kw):
        self._set_default_content_type(kw)
        self._set_default_authentication_header(kw)
        return super().put(*args, **kw)

    def delete(self, *args, **kw):
        self._set_default_content_type(kw)
        self._set_default_authentication_header(kw)
        return super().delete(*args, **kw)


class TestBase(unittest.TestCase):
    def _setFactoryStrategy(self, strategy):
        """
        Set the create/build strategy of the factory classes in the tests.factories module.
        The factories' default strategy is set at import time when the classes are created so to override it each
        created factory class must be found and the strategy option set within it.
        :param strategy: factory.CREATE_STRATEGY or factory.BUILD_STRATEGY
        :return:
        """
        from tests import factories
        md = factories.__dict__
        factory_classes = [md[c] for c in md
                           if (isinstance(md[c], type) and md[c].__module__ == factories.__name__)]
        for factory_class in factory_classes:
            factory_class._meta.strategy = strategy

    def setUp(self, create_all=True, factory_create=True):
        """
        Base per-test setup for all unit tests.
        :param create_all: (re)create the database
        :param factory_create: create factory objects on the database if true ('create' strategy), otherwise only in
        memory ('build' strategy). Set to false when passing fixtures to the database as VALUE expressions using
        ModelAsValues.
        """
        app.test_client_class = AppTestClient
        db.engine.echo = app.config.get('DEBUG', True)
        self._setFactoryStrategy(factory.CREATE_STRATEGY if factory_create else factory.BUILD_STRATEGY)
        self.create_all = create_all
        if self.create_all:
            db.engine.execute("drop schema if exists public cascade")
            db.engine.execute("create schema public")
            db.create_all(bind=None)  # Only create things on the default db (Postgres)
        self.session = scoped_session


    def doCleanups(self):
        self.session.close_all()
        # db.engine.execute("drop schema if exists public cascade")
        # db.engine.execute("create schema public")

    def verify_json_response(self, expected_data, url, **kwargs):
        with app.test_client() as client:
            resp = client.get(url, **kwargs)
            self.assertEqual(resp.status_code, 200)
            retrieved_json = resp.get_data(as_text=True)
            retrieved_data = FlaskJSONDecoder().decode(retrieved_json)
            self.assertDictEqual(expected_data, retrieved_data)

    def get_results(self, exp):
        """
        Execute SQL core expression and return result rows as a list, translating each row into a plain dict.
        :param exp:
        :return:
        """
        return [dict(result) for result in self.session.bind.engine.execute(exp).fetchall()]

    def assertIntersectedDictsEqual(self, first, second, msg=None):
        """Fail if the intersected dicts are unequal as determined by the '=='
           operator.
        """
        second = {x: second[x] for x in first if x in second}
        assertion_func = self._getAssertEqualityFunc(first, second)
        assertion_func(first, second, msg=msg)
