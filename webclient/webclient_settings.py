# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
ACTIVE_CONTROLLERS = ('test', 'auth', 'task', 'ui', 'admin', 'domain')

TEMPLATE_CACHE = 0

SESSION_USER_KEY = 'usr'

ANGULAR_MODULES = ['router', 
                   'ngStorage', 
                   'ngUpload',
                   'ngAnimate',
                   'ngCookies',
                   'ngSanitize',
                   'ngTouch',
                   'transition', 
                   'collapse', 
                   'accordion',
                   'modal', 
                   'select2',
                   'busy', 
                   'checklist'
                  ]

ANGULAR_COMPONENTS = ['home/home',
                      'srv/auth/account',
                      'srv/auth/app',
                      'opt/buyer/buyer',
                      
                      # this goes last
                      'admin/admin',
                      ]

JQUERY_PLUGINS = ['select2/select2']

WEBAPP2_EXTRAS = {}