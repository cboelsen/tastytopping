import traceback
from django.http import HttpResponse

class PlainTextExceptionMiddleware(object):
     def process_exception(self, request, exception):
         return HttpResponse(traceback.format_exc(), "text/plain")
