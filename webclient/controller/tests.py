# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import inspect
import copy

from google.appengine.ext import blobstore
from google.appengine.api import images

from app import orm, settings
from app.models import base

from webclient import handler
  
class BaseTestHandler(handler.Base):
   
  LOAD_CURRENT_USER = False
  
  def before(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8;'
  
  def out_json(self, s):
    self.out(handler.output_json(s))
  
  def out(self, s, a=0, before=True):
    sp = "\n"
    if before:
      self.response.write(sp*a)
    self.response.write(s)
    self.response.write(sp*a)
    
    
class TestA(orm.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_record_engine = False
  _use_rule_engine = False
  _use_search_engine = False
  
  
  name = orm.SuperStringProperty()
  gaa = orm.SuperIntegerProperty()
  
class TestB(orm.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_record_engine = False
  _use_rule_engine = False
  _use_search_engine = False
  
  
  name = orm.SuperStringProperty()
  gaa = orm.SuperIntegerProperty()
  
    
class TestP(orm.BaseModel):
  
  _use_memcache = False
  _use_cache = False
  _use_record_engine = False
  _use_rule_engine = False
  _use_search_engine = False
  
  tests1 = orm.SuperStructuredProperty(TestA, repeated=True)
  tests2 = orm.SuperStructuredProperty(TestB)
    
class Test1(BaseTestHandler):
  
  def respond(self):
    if self.request.get('rr'):
      orm.delete_multi(TestP.query().fetch(keys_only=True))
    pp = self.request.get('pp')
    cc = self.request.get('cc')
    if pp and cc:
      outer = TestP(id=pp, tests1=[TestA(name='foobar1', gaa=1)], tests2=TestB(name='foobar2', gaa=2))
      outer.put()
    else:
      outer = TestP.build_key(pp).get()
      outer.read()
      if self.request.get('edit'):
        outer.tests1 = [TestA(name='zoobar1', gaa=2, _sequence=10)]
        outer.put()
    self.out_json([outer.tests2.value._properties, outer])
  
  
class Test2(BaseTestHandler):
  
  def respond(self):
    import PIL
    import sys
    
    self.out_json([sys.version, sys.version_info, sys.path])
    #self.out_json(copy.copy(sys.modules))
    
 
for k,o in globals().items():
  if inspect.isclass(o) and issubclass(o, BaseTestHandler):
    handler.register(('/Tests/%s' % o.__name__, o))