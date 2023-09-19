from health_check.backends import BaseHealthCheckBackend
from cache_retry import SOLR

class SolrHealthCheckBackend(BaseHealthCheckBackend):
    #: The status endpoints will respond with a 200 status code
    #: even if the check errors.
    critical_service = False

    def check_status(self):
        try:
            resp = SOLR(q="cats")
        except:
            raise HealthCheckException

    def identifier(self):
        return self.__class__.__name__  # Display name on the endpoint.
