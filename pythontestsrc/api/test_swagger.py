from app import app
from tests.test_base import TestBase
from flask.json import JSONDecoder as FlaskJSONDecoder


class TestCase(TestBase):

    def test_get_swagger(self):
        with app.test_client() as client:
            resp = client.get('/api/swagger')
            self.assertEqual(resp.status_code, 200)
            swagger = FlaskJSONDecoder().decode(resp.get_data(as_text=True))
            self.assertGreater(len(swagger['definitions']), 10)
            self.assertGreater(len(swagger['paths']), 10)
