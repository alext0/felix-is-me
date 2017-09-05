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


class InterouteTestCase(TestBase):
    """
    Tests for the Interoute pages and API.
    """

    def test_get_main_page(self):
        with app.test_client() as client:
            url = 'http://localhost:3000/main'
            resp = client.get(url, **kwargs)
            self.assertEqual(resp.status_code, 200)
            response = resp.get_data(as_text=True)
            self.assertRegex(response, '.*Login.*', 'Interoute heading not found')
