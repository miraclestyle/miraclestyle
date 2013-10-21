# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import decimal
import hashlib
 
from google.appengine.ext.ndb import *

from app import pyson
from app.util import import_module
 
ctx = get_context()

# memory policy for google app engine ndb calls is set to false, instead we decide per `get` wether to use memcache or not
ctx.set_memcache_policy(False)

# We always put double underscore for our private functions in order to avoid ndb library from clashing with our code
# see https://groups.google.com/d/msg/appengine-ndb-discuss/iSVBG29MAbY/a54rawIy5DUJ

class _BaseModel(Model):
  
  original_values = {}
  
  def loaded(self):
      return self.key != None
  
  def _pre_put_hook(self):
      for p in self._properties:
          prop = self._properties.get(p)
          if prop._get_value(self) is None:
             cb = 'default_%s' % p
             if hasattr(self, cb):
                prop._set_value(self, getattr(self, cb)())
             
          if prop and hasattr(prop, '_writable') and prop._writable:
             self.__resolve_writable(prop)
 
  def __resolve_writable(self, prop):
      if isinstance(prop._writable, pyson.PYSON):
         environ = EvalEnvironment(self)
         encoded = pyson.PYSONEncoder(environ).encode(prop._writable)
         check = pyson.PYSONDecoder(environ).decode(encoded)
         if not check:
            # if the evaluation is not true, set the original values because new value is not allowed to be set
            prop._set_value(self, self.original_values.get(prop._name))
    
  def set_original_values(self):
      for p in self._properties:
          self.original_values[p] = self._properties[p]._get_value(self)
       
    
  @classmethod
  def _get_kind(cls):
    """Return the kind name for this class.

    This defaults to cls.__name__; users may overrid this to give a
    class a different on-disk name than its class name.
    """
    if hasattr(cls, 'KIND_ID'):
       if cls.KIND_ID < 0:
          raise TypeError('Invalid KIND_ID %s, for %s' % (cls.KIND_ID, cls.__name__)) 
       return str(cls.KIND_ID)
    return cls.__name__

class BaseModel(_BaseModel):
    """
      Base class for all `ndb.Model` entities
    """
    @classmethod
    def _from_pb(cls, *args, **kwargs):
        """ Allows for model to get original values who get loaded from the protocol buffer  """
        entity = super(_BaseModel, cls)._from_pb(*args, **kwargs) 
        entity.set_original_values()
        return entity

  
class BaseExpando(_BaseModel, Expando):
    """
     Base class for all `ndb.Expando` entities
    """
    def has_expando_fields(self):
        if hasattr(self, 'EXPANDO_FIELDS'):
           return self.EXPANDO_FIELDS
        else:
           return False
        
    def __getattr__(self, name):
       ex = self.has_expando_fields()
       if ex:
          vf = ex.get(name) 
          if vf:
             return vf._get_value(self)
       return super(BaseExpando, self).__getattr__(name)
      
    def __setattr__(self, name, value):
        ex = self.has_expando_fields()
        if ex:
           vf = ex.get(name) 
           if vf:
              vf._code_name = name
              self._properties[name] = vf
              vf._set_value(self, value)
              return vf
        return super(BaseExpando, self).__setattr__(name, value)
      
    def __delattr__(self, name):
       ex = self.has_expando_fields()
       if ex:
          vf = ex.get(name) 
          if vf:
             vf._delete_value(self)
             if vf in self.__class__._properties:
                 raise RuntimeError('Property %s still in the list of properties for the '
                                       'base class.' % name)
             del self._properties[name]
       return super(BaseExpando, self).__delattr__(name)

class _BaseProperty(object):
    
    _writable = False
    _visible = False
    
    def __init__(self, *args, **kwds):
        self._writable = kwds.pop('writable', self._writable)
        self._visible = kwds.pop('visible', self._visible)
        
        custom_kind = kwds.get('kind')
        if custom_kind and isinstance(custom_kind, basestring) and '.' in custom_kind:
           custom_kinds = custom_kind.split('.')
           far = custom_kinds[-1] 
           del custom_kinds[-1] 
           
           kwds['kind'] = getattr(import_module(".".join(custom_kinds)), far)
             
        super(_BaseProperty, self).__init__(*args, **kwds)

class BaseProperty(_BaseProperty, Property):
   """
    Base property class for all properties capable of having writable, and visible options
   """
 
class SuperStringProperty(_BaseProperty, StringProperty):
    pass

class SuperIntegerProperty(_BaseProperty, IntegerProperty):
    pass

class SuperDateTimeProperty(_BaseProperty, DateTimeProperty):
    pass

class SuperKeyProperty(_BaseProperty, KeyProperty):
    pass

class SuperBooleanProperty(_BaseProperty, BooleanProperty):
    pass

class SuperBlobKeyProperty(_BaseProperty, BlobKeyProperty):
    pass
  
class SuperDecimalProperty(SuperStringProperty):
    """Decimal property that accepts only `decimal.Decimal`"""
    
    def _validate(self, value):
      if not isinstance(value, (decimal.Decimal)):
        raise TypeError('expected an decimal, got %s' % repr(value)) # explicitly allow only decimal
    
    def _to_base_type(self, value):
        return str(value) # Doesn't matter which type, always return in string format
    
    def _from_base_type(self, value):
        return decimal.Decimal(value)  # Always return a decimal

      
class SuperReferenceProperty(SuperKeyProperty):
      
    """Replicated property from `db` module"""
      
    def _validate(self, value):
        if not isinstance(value, Model):
           raise TypeError('expected an ndb.Model, got %s' % repr(value))
    
    def _to_base_type(self, value):
        return value.key
    
    def _from_base_type(self, value):
        return value.get()

class SuperRelationProperty(dict):
    """
      ################################################################################################   
      ##### This property is not yet tested and yet to be decided whether should be used anyway! #####
      ################################################################################################
      This is a fake property that will `not` be stored in datastore,
       it only represents on what one model can depend. Like so
       
       class UserChildEntity(ndb.BaseModel):
             user = ndb.SuperRelationProperty(User)
             name = ndb.StringProperty(required=True, writable=Eval('user.state') != 'active')
             
       foo = UserChildEntity(name='Edward', user=ndb.Key('User', 'foo').get())
       foo.save()     
       
       The `Eval` will evaluate: self.user.state != 'active' and therefore the property
       will validate itself to be read only
       
       This property only accepts model that needs validation, otherwise it will accept any value provided
    """
    def __get__(self, entity):
        """Descriptor protocol: get the value on the entity."""
        return self.model
        
    def __set__(self, entity, value):
        """Descriptor protocol: set the value on the entity."""
        if self.model_type:
           if not isinstance(value, self.model_type):
              raise TypeError('Expected %s, got %s' % (repr(self.model_type), repr(value)))
        self.model = value
    
    def __init__(self, model=None):
        self.model_type = model
    
    def __getitem__(self, item):
       return getattr(self.model, item)
        
    def __getattr__(self, item):
       try:
          return self.__getitem__(item)
       except KeyError, exception:
          raise AttributeError(*exception.args)
        
    def get(self, item, default=None):
       try:
          return self.__getitem__(item)
       except Exception:
          pass
       return super(SuperRelationProperty, self).get(item, default)     
 
# Workflow error exceptions 
class WorkflowTransitionError(Exception):
      pass
  
class WorkflowStateError(Exception):
      pass
  
class WorkflowActionError(Exception):
      pass
  
class WorkflowActionNotReadyError(Exception):
      pass
  
class WorkflowBadStateCodeError(Exception):
      pass

class WorkflowBadActionCodeError(Exception):
      pass

class Workflow():
    
      """
      Workflow is a class used for making the object capable of having
      actions, states and transitions and every other aspect of ObjectLog concept.
      
      Example: 
      
      class User(ndb.BaseModel, ndb.Workflow)  or for expando class Expando(ndb.BaseExpando, ndb.Workflow)
            ....
      """
    
      OBJECT_DEFAULT_STATE = False
      OBJECT_STATES = {}
      OBJECT_TRANSITIONS = {}
      OBJECT_ACTIONS = {}
      
      __record_action = []
      
      @classmethod
      def default_state(cls):
        # returns default state for this model
        return cls.resolve_state_code_by_name(cls.OBJECT_DEFAULT_STATE)
  
      @classmethod
      def resolve_state_code_by_name(cls, state_code):
          """
          Resolves state code by name
          """
          codes = cls.OBJECT_STATES
          code = codes.get(state_code)
          if not code:
             raise WorkflowStateError('This model does not have state code %s, while available %s' % (state_code, codes))
          return code[0]
      
      @classmethod
      def resolve_action_code_by_name(cls, st):
          """
          Resolves action code by name
          """
          actions = cls.OBJECT_ACTIONS
          action = actions.get(st, None)
          if action == None:
             raise WorkflowActionError('Unexisting action called %s, while available %s' % (st, actions))
          return action
      
      @classmethod
      def resolve_action_name_by_code(cls, code):
          """
         Resolves action name by code provided
          """
          for k, v in cls.OBJECT_ACTIONS.items():
              if v == code:
                 return k
          raise WorkflowBadActionCodeError('Bad action coded provided %s, possible names %s' % (code, cls.OBJECT_ACTIONS.keys()))  
      
      @classmethod
      def resolve_state_name_by_code(cls, code):
          """
           Resolves state name by provided code
          """
          for k, value in cls.OBJECT_STATES.items():
              if value[0] == code:
                 return k
          raise WorkflowBadStateCodeError('Bad state code provided %s, possible names %s' % (code, cls.OBJECT_STATES.keys()))  
      
      def check_transition(self, state, action):
          """
          Checks if the transition is valid based on state and action provided
          """
          transitions = self.OBJECT_TRANSITIONS[action]
          
          if self.state not in transitions['from'] or state not in transitions['to']:
             raise WorkflowTransitionError('This object cannot go from state `%s` to state `%s`. It can only go from states `%s` to `%s`'
                                           % (self.state, state, transitions['from'], transitions['to']))
      
      def set_state(self, state):
          self.state = self.resolve_state_code_by_name(state)
          
      @property
      def get_state(self):
          return self.resolve_state_name_by_code(self.state)
          
      def new_action(self, action, state=None, **kwargs):
          """ Sets new state inited by some action, and prepares object"""
          
          if state is not None: # if state is unchanged, no checks for transition needed?
              self.set_state(state)
              self.check_transition(state, action)
              
          action = self.resolve_action_code_by_name(action)
 
          if self.state == None:
             state = self.default_state()
 
          from app.core import log
          objlog = log.ObjectLog(state=self.state, action=action, parent=self.key, **kwargs)
          
          self.__record_action.append(objlog)

          return objlog
      
      def record_action(self, skip_check=False):
          any_actions = len(self.__record_action)
          if not any_actions and not skip_check:
             raise WorkflowActionNotReadyError('This entity did not have self.new_action called')
          
          if any_actions:
             return put_multi(self.__record_action)
 
   
class Response(dict):
    
    """ 
      Response dict object used for preparing data which is returned to clients for parsing.
      Usually every model method should return this type of response object.
    """
    
    def __setattr__(self, *args, **kwargs):
        return dict.__setitem__(self, *args, **kwargs)
    
    def __getattr__(self, *args, **kwargs):
        return dict.__getitem__(self, *args, **kwargs)
    
    def has_error(self, k=None):
        if k is None:
           return len(self['errors'].keys())
        else:
           return len(self['errors'][k])
    
    def error(self, f, m):
        
        if self['errors'] == None:
           self['errors'] = {}
           
        if f not in self['errors']:
            self['errors'][f] = list()
            
        self['errors'][f].append(m)
        return self
    
    def __init__(self):
        self['errors'] = None
        
  
class EvalEnvironment(dict):
    
  """
    Eval environment is helper class for pyson.Eval in which creates context that helps pyson.Eval  
    successfully evaluate expressions given trough its constructor.
  """  

  def __init__(self, record):
     super(EvalEnvironment, self).__init__()
     self._record = record
        
  def __getitem__(self, item):
     if item in self._record._properties:
        items = item.split('.') # if Eval('object.foo.bar') it will digg till it reaches to .bar
        g = None
        for i in items:
            if not g:
               g = self._record
            # this will throw AttributError if Eval() is not configured properly, or model does not posses the actual
            # object that will return the attribute, wether that be `None` or `False` the attribute must exist
            g = getattr(g, i)
        return g
     return super(EvalEnvironment, self).__getitem__(item)

  def __getattr__(self, item):
      try:
         return self.__getitem__(item)
      except KeyError, exception:
         raise AttributeError(*exception.args)

  def get(self, item, default=None):
      try:
        return self.__getitem__(item)
      except Exception:
        pass
      return super(EvalEnvironment, self).get(item, default)

  def __nonzero__(self):
      return bool(self._record)