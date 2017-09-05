from api import api

@api.route('/healthcheck', methods=['GET'])
def get_healthcheck():
    """
    ---
    get:
       description: Check that the app is live, e.g. by load balancer

       responses:
           200:
               description: 'ok'
    """
    return 'ok'
