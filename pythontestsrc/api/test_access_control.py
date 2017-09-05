from app import app
from util.access_util import login_required, ATN_HEADER
from util.factories import UserFty
from util.test_base import TestBase


@app.route('/api/projects/<int:project_id>/unprotected')
def unprotected_api(project_id):
    return 'OK'

@app.route('/api/projects/<int:project_id>/login_only')
@login_required
def login_only_api(project_id):
    return 'OK'

@app.route('/api/projects/<int:project_id>/project_owner_only')
@login_required
@project_owner_required
def project_owner_only_api(project_id):
    return 'OK'


class TestCase(TestBase):
    def setUp(self, create_all=True, factory_create=True):
        super().setUp(self)
        self.owner_user = UserFty(name ='owner1', email='owner1@sainsburys.co.uk')

    def test_can_access_unprotected_api(self):
        with app.test_client() as client:
            resp = client.get('/api/projects/{}/unprotected'.format(self.project.id))
            self.assertEqual(resp.status_code, 200)

    def test_cant_access_login_only_api_without_user_id(self):
        with app.test_client() as client:
            resp = client.get('/api/projects/{}/login_only'.format(self.project.id))
            self.assertEqual(resp.status_code, 401)

    def test_can_access_login_only_api_with_user_id(self):
        with app.test_client() as client:
            resp = client.get('/api/projects/{}/login_only'.format(self.project.id),
                              headers={ATN_HEADER: self.any_user.email})
            self.assertEqual(resp.status_code, 200)

    def test_cant_access_project_owner_only_api_without_user_id(self):
        with app.test_client() as client:
            resp = client.get('/api/projects/{}/project_owner_only'.format(self.project.id))
            self.assertEqual(resp.status_code, 401)

    def test_cant_access_project_owner_only_api_as_non_owner(self):
        with app.test_client() as client:
            resp = client.get('/api/projects/{}/project_owner_only'.format(self.project.id),
                              headers={ATN_HEADER: self.any_user.email})
            self.assertEqual(resp.status_code, 403)

    def test_can_access_project_owner_only_api_as_owner(self):
        with app.test_client() as client:
            resp = client.get('/api/projects/{}/project_owner_only'.format(self.project.id),
                              headers={ATN_HEADER: self.owner_user.email})
            self.assertEqual(resp.status_code, 200)
