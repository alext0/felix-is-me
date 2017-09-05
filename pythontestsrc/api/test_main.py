"""
Create a small Flask app that has 3 main routes:
/login
/logout
/main
The user should be able to login using OIDC (http://flask-oidc.readthedocs.io/en/latest/) and the "/main" route should
be protected.
As an end-user I would access the web application using my browser, go to the login page, use my credentials, be
redirected to the IdP, give my consent that the current app can access my user data, access the main page and logout
from the flask app.

Bonus 1: If my access token expires, I would like the app/client (not End-User) to use my refresh_token.
Bonus 2: Add a fourth route called /api that accepts only tokens. That requires the creation of an "/authorize" route
that returns an access token.

A few Identity Providers:
https://developers.google.com/identity/protocols/OpenIDConnect
https://www.okta.com/api/signup/
https://auth0.com/signup

OAuth2/OIDC RFC:
http://openid.net/specs/openid-connect-core-1_0.html

References:
https://www.youtube.com/watch?v=6DxRTJN1Ffo&t=6s
https://www.youtube.com/watch?v=WVCzv50BslE&t=1s
"""

from util.test_base import TestBase
from util.factories import UserFty


class ClusterResourceTestCase(TestBase):
    """
    Tests for the Cluster API.
    """

    def test_get_cluster(self):
        section = SectionFty()
        cdh = CdhFty(section_id=section)
        user = UserFty(__sequence=1)
        clustering = ClusteringFty(section=section)
        task = TaskFty()
        project = ProjectFty(
            cdh=cdh,
            clustering=clustering,
            current_task=task,
            section=section,
            owner_user=user
        )
        cluster = ClusterFty(clustering=clustering)

        self.session.commit()

        expected_data = {
            "items": [
                {
                    "clustering_id": cluster.clustering_id,
                    "display_order": cluster.display_order,
                    "id": cluster.id,
                    "name": cluster.name
                }
            ]
        }

        self.verify_json_response(expected_data, '/api/projects/{}/clusters'.format(project.id))

    def test_cluster_ordering(self):
        section = SectionFty()
        cdh = CdhFty(section=section)
        user = UserFty(__sequence=1)
        clustering = ClusteringFty(section=section)
        task = TaskFty()
        project = ProjectFty(
            cdh_id=cdh.id,
            clustering=clustering,
            current_task=task,
            section=section,
            owner_user=user
        )
        clusters = [ClusterFty(clustering=clustering), ClusterFty(clustering=clustering)]

        self.session.commit()

        expected_data = {
            "items": [
                {
                    "id": clusters[0].id,
                    "name": clusters[0].name,
                    "clustering_id": clusters[0].clustering_id,
                    "display_order": clusters[0].display_order
                },
                {
                    "id": clusters[1].id,
                    "name": clusters[1].name,
                    "clustering_id": clusters[1].clustering_id,
                    "display_order": clusters[1].display_order
                }
            ]
        }

        self.verify_json_response(expected_data, '/api/projects/{}/clusters'.format(project.id))
