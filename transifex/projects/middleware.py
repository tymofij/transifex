import re
from django.http import HttpResponsePermanentRedirect
from transifex.urls import PROJECTS_URL

pattern = re.compile(r'^/projects/p/([^/]+)/')
class ProjectSlugMiddleware(object):
    def process_request(self, request):
        path = request.path
        match = pattern.search(path)
        if match:
            slug = match.groups()[0]
            slug_lower = slug.lower()
            if slug_lower == slug:
                return None
            else:
                return HttpResponsePermanentRedirect("/projects/p/%s/%s" % (slug_lower, path[match.end():]))
