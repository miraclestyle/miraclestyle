# -*- coding: utf-8 -*-

'''
Created on Jul 8, 2013

@copyright: Vertazzar (Edis Šehalić)
@author: Vertazzar (Edis Šehalić)
@module app.settings.py

'''

import os

ROOT_URLCONF = 'app.urls'
  
INSTALLED_APPS = ( 
    'app.sys',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'debug_toolbar',
    
) 
INTERNAL_IPS = ('127.0.0.1', '::1',)
ALLOWED_HOSTS = []
 
PRODUCTION = (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') and os.getenv('SETTINGS_MODE') == 'prod') 
DEBUG = PRODUCTION is False
TEMPLATE_DEBUG = DEBUG
TRANSACTIONS_MANAGED = False
SESSION_USER_KEY = 'user_id'
EMAIL_BACKEND = "gae_backends.mail.EmailBackend"
CACHES = {
    'default': {
        'BACKEND': 'gae_backends.memcache.MemcacheCache',
    },
    'locmem': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
)
FILE_UPLOAD_MAX_MEMORY_SIZE = 36700160 # i.e. 30 MB
  
SECRET_KEY = '25199r029ifs0f9fk093wpmsfdj29510jtkofsedmflsknwojf'
 
SITE_ID = 1
STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
)
 

MIDDLEWARE_CLASSES = (
    'app.middleware.Current',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

if PRODUCTION:
    # Running on production App Engine, so use a Google Cloud SQL database.
    DATABASES = {
        'default': {
            'ENGINE': 'google.appengine.ext.django.backends.rdbms',
            'INSTANCE': 'sql-network:miraclestyle-demo',
            'NAME': 'miraclestyle_demo',
        }
    }
else:
    # Running in development, so use a local MySQL database.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'USER': 'root',
            'PASSWORD': 'root',
            'HOST' : '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock',
            'NAME': 'miraclestyle2',
        }
    }
