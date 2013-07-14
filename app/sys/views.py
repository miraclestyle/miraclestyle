# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
from app.core import HttpResponse
from app.sys.models import User

# index page view
def index(request):
    user = User.objects.get(pk=29)
    user.login()
    return HttpResponse('<body>Hello World 2.0v, hi %s, settings mode %s and software %s</body>'
                         % (user.get_last_state().pk, os.getenv('SETTINGS_MODE'), os.getenv('SERVER_SOFTWARE', '')))