from util.access_util import ATN_HEADER
from util.factories import UserFty
from util.test_base import TestBase


class TestCase(TestBase):

    def test_get_current_user(self):
        user = UserFty()
        self.session.commit()

        expected_data = {
            'user': {
                'id': user.id,
                'created_at': '2016-01-01T01:00:00+00:00',
                'name': user.name}}

        self.verify_json_response(expected_data, '/api/current_user', headers={ATN_HEADER: user.email})
