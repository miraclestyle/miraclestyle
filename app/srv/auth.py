# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import hashlib
import os

from app import ndb, settings, memcache, util
from app.srv import io, rule
from app.lib import oauth2
from app.srv import log
  
class Context():
  
  def __init__(self):
    self.user = User.current_user()
    self.domain = None
 
  
class Session(ndb.BaseModel):
    
      session_id = ndb.SuperStringProperty('1', indexed=False)
      updated = ndb.SuperDateTimeProperty('2', auto_now_add=True, indexed=False)
 
     
class Identity(ndb.BaseModel):
 
    # StructuredProperty model
    identity = ndb.SuperStringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.SuperStringProperty('2', required=True)
    associated = ndb.SuperBooleanProperty('3', default=True)
    primary = ndb.SuperBooleanProperty('4', default=True)
 
class User(ndb.BaseExpando):
    
    _kind = 0
 
    _use_memcache = True
    
    identities = ndb.SuperStructuredProperty(Identity, '1', repeated=True)# soft limit 100x
    emails = ndb.SuperStringProperty('2', repeated=True)# soft limit 100x
    state = ndb.SuperStringProperty('3', required=True)
    sessions = ndb.SuperLocalStructuredProperty(Session, '4', repeated=True)
 
    _default_indexed = False
  
    _expando_fields = {  

    }
    
    _global_role = rule.GlobalRole(permissions=[
                                                rule.ActionPermission('0', io.Action.build_key('0-0').urlsafe(), True, "context.rule.entity.is_guest or context.rule.entity.is_active"),
                                                rule.ActionPermission('0', io.Action.build_key('0-1').urlsafe(), True, "not context.rule.entity.is_guest"),
                                                rule.ActionPermission('0', io.Action.build_key('0-2').urlsafe(), True, "context.auth.user.root_admin"),
                                                rule.ActionPermission('0', io.Action.build_key('0-3').urlsafe(), True, "not context.rule.entity.is_guest"),
                                               ])
    
    _actions = {
       'login' : io.Action(id='0-0',
                              arguments={
                                 'login_method' : ndb.SuperStringProperty(required=True),
                                 'code' : ndb.SuperStringProperty(),
                                 'error' : ndb.SuperStringProperty()
                              }
                             ),
                
       'update' : io.Action(id='0-1',
                              arguments={
                                 'primary_email' : ndb.SuperStringProperty(),
                                 'disassociate' : ndb.SuperStringProperty(),
                              }
                             ),
                
       'sudo' : io.Action(id='0-2',
                              arguments={
                                 'id'  : ndb.SuperKeyProperty(kind='0', required=True),
                                 'message' : ndb.SuperKeyProperty(required=True),
                                 'note' : ndb.SuperKeyProperty(required=True)
                              }
                             ),
                
       'logout' : io.Action(id='0-3',
                              arguments={
                                'code' : ndb.SuperStringProperty(required=True),
                              }
                             )
    }
 
    def __todict__(self):
      
        d = super(User, self).__todict__()
        
        d['logout_code'] = self.logout_code
        d['is_guest'] = self.is_guest
        
        return d 
    
    @property
    def root_admin(self):
       return self.primary_email in settings.ROOT_ADMINS
    
    @property
    def primary_email(self):
        if not self.identities:
           return None
        for i in self.identities:
            if i.primary == True:
               return i.email   
        return i.email
    
    @property
    def logout_code(self):
        session = self.current_user_session()
        if not session:
           return None
        return hashlib.md5(session.session_id).hexdigest()
      
    @property
    def is_guest(self):
        return self.key == None
      
    @property
    def is_active(self):
        return self.state == 'active'
    
    @classmethod
    def set_current_user(cls, user, session=None):
        memcache.temp_memory_set('_current_user', user)
        memcache.temp_memory_set('_current_user_session', session)
        
    @classmethod
    def current_user(cls):
        current_user = memcache.temp_memory_get('_current_user')
        if not current_user:
           current_user = cls()
           
        return current_user
    
    def generate_authorization_code(self, session):
        return '%s|%s' % (self.key.urlsafe(), session.session_id)
    
    def new_session(self):
        session_id = self.generate_session_id()
        session = Session(session_id=session_id)
        self.sessions.append(session)
        
        return session
  
    def session_by_id(self, sid):
        for s in self.sessions:
            if s.session_id == sid:
               return s
        return None
    
    def generate_session_id(self):
        sids = [s.session_id for s in self.sessions]
        while True:
              random_str = hashlib.md5(util.random_chars(30)).hexdigest()
              if random_str not in sids:
                  break
        return random_str
    
    @classmethod
    def current_user_session(cls):
        return memcache.temp_memory_get('_current_user_session')
    
    @classmethod
    def login_from_authorization_code(cls, auth):
 
        try:
           user_key, session_id = auth.split('|')
        except:
           # fail silently if the authorization code is not set properly, or its corrupted somehow
           return
        
        if not session_id:
           # fail silently if the session id is not found in the split sequence
           return
        
        user = ndb.Key(urlsafe=user_key).get()
        if user:
           session = user.session_by_id(session_id)
           if session:
              cls.set_current_user(user, session)
               
    def has_identity(self, identity_id):
        for i in self.identities:
            if i.identity == identity_id:
               return i
        return False  
      
    @classmethod
    def sudo(cls, args):
      
        # @todo Treba obratiti paznju na to da suspenzija usera ujedno znaci i izuzimanje svih negativnih i neutralnih feedbackova
        # koje je user ostavio dok je bio aktivan.
      
        action = cls._actions.get('sudo')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               user_to_update_key = context.args.get('id')
               message = context.args.get('message')
               note = context.args.get('note')
           
               user_to_update = user_to_update_key.get()
               context.rule.entity = user_to_update
               rule.Engine.run(context, True)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               new_state = 'active'
               
               if user_to_update.is_active:
                  new_state = 'suspended'
                  user_to_update.sessions = [] # delete sessions
 
               user_to_update.state = new_state
               user_to_update.put()
               
               context.log.entities.append((user_to_update, {'message' : message, 'note' : note}))
               log.Engine.run(context)
               
               context.response['updated'] = True
               context.response['updated_user'] = user_to_update
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
      
    @classmethod
    def update(cls, args):
      
        action = cls._actions.get('update')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
           
               current_user = cls.current_user()
               context.rule.entity = current_user
               rule.Engine.run(context, True)
               
               if not rule.executable(context):
                  return context.not_authorized()
    
               primary_email = context.args.get('primary_email')
               disassociate = context.args.get('disassociate')
 
               for identity in enumerate(current_user.identities):
                   if primary_email:
                       identity.primary = False
                       if identity.email == primary_email:
                          identity.primary = True
                    
                   if disassociate:  
                       if identity.identity == disassociate:
                          identity.associate = False
                      
               current_user.put()
               
               context.log.entities.append((current_user, ))
               log.Engine.run(context)
               
               context.response['updated'] = True
               context.response['user'] = current_user
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
  
    
    @classmethod  
    def logout(cls, args):
          
        action = cls._actions.get('logout')
        context = action.process(args)
        
        if not context.has_error():
          
          current_user = cls.current_user()
          context.rule.entity = current_user
          rule.Engine.run(context, True)
         
          if not rule.executable(context):
             return context.not_authorized()
          
          @ndb.transactional(xg=True)
          def transaction():
               
              if current_user.is_guest:
                 return context.error('login', 'already_logged_out')
             
              if not current_user.logout_code == context.args.get('code'):
                 return context.error('login', 'invalid_code')
           
              if current_user.sessions:
                 current_user.sessions = []
   
              context.log.entities.append((current_user, {'ip_address' : os.environ['REMOTE_ADDR']}))
              
              log.Engine.run(context)
              
              current_user.put()
              
              current_user.set_current_user(None, None)
              
              context.status('logged_out')
          
          try:
              transaction()
          except Exception as e:
              context.transaction_error(e)
              
        return context
     
    @classmethod
    def login(cls, args):
        
        action = cls._actions.get('login')
        context = action.process(args)
    
        if not context.has_error():
        
           login_method = context.args.get('login_method')
           error = context.args.get('error')
           code = context.args.get('code')
           current_user = cls.current_user()
           
           context.rule.entity = current_user
           context.auth.user = current_user
           rule.Engine.run(context, True)
 
           if not rule.executable(context):
              return context.not_authorized()
           
           if login_method not in settings.LOGIN_METHODS:
              context.error('login_method', 'not_allowed')
           else:
              context.response['providers'] = settings.LOGIN_METHODS
              
              cfg = getattr(settings, '%s_OAUTH2' % login_method.upper())
              client = oauth2.Client(**cfg)
              
              context.response['authorization_url'] = client.get_authorization_code_uri()
        
              if error:
                 return context.error('oauth2_error', 'rejected_account_access')
               
              if code:
                
                 client.get_token(code)
                 
                 if not client.access_token:
                    return context.error('oauth2_error', 'failed_access_token')
                  
                 context.response['access_token'] = client.access_token
                 
                 userinfo = getattr(settings, '%s_OAUTH2_USERINFO' % login_method.upper())
                 info = client.resource_request(url=userinfo)
                 
                 if info and 'email' in info:
                   
                     identity = settings.LOGIN_METHODS.get(login_method)
                     identity_id = '%s-%s' % (info['id'], identity)
                     email = info['email']
                     
                     user = cls.query(cls.identities.identity == identity_id).get()
                     if not user:
                        user = cls.query(cls.emails == email).get()
                     
                     if user:   
                        
                       context.rule.entity = user
                       context.auth.user = user
                       rule.Engine.run(context, True)
                       
                       if not rule.executable(context):
                          return context.not_authorized()
                        
                     
                     @ndb.transactional(xg=True)
                     def transaction(user):
                       
                        if not user or user.is_guest:
                          
                           user = cls()
                           user.emails.append(email)
                           user.identities.append(Identity(identity=identity_id, email=email, primary=True))
                           user.state = 'active'
                           session = user.new_session()
                           
                           user.put()
                             
                        else:
                          
                          if email not in user.emails:
                             user.emails.append(email)
                             
                          used_identity = user.has_identity(identity_id)
                          
                          if not used_identity:
                             user.append(Identity(identity=identity_id, email=email, primary=False))
                          else:
                             used_identity.associated = True
                             if used_identity.email != email:
                                used_identity.email = email
                          
                          session = user.new_session()   
                          user.put()
                            
                        cls.set_current_user(user, session)
                        context.auth.user = user
                        
                        context.log.entities.append((user, {'ip_address' : os.environ['REMOTE_ADDR']}))
                        log.Engine.run(context)
                         
                        context.response.update({'user' : user,
                                                 'authorization_code' : user.generate_authorization_code(session),
                                                 'session' : session
                                                 })
                     try:
                        transaction(user) 
                     except Exception as e:
                        context.transaction_error(e)
               
        return context
      
class Domain(ndb.BaseExpando):
    
    # domain will use in-memory cache and memcache
     
    _use_memcache = True
    
    _kind = 6
    
    # root
    # composite index: ancestor:no - state,name
    name = ndb.SuperStringProperty('1', required=True)
    primary_contact = ndb.SuperKeyProperty('2', kind=User, required=True, indexed=False)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
    state = ndb.SuperStringProperty('5', required=True)
    
    _default_indexed = False
    
    _global_role = rule.GlobalRole(permissions=[
                                            # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
                                            rule.ActionPermission('6', io.Action.build_key('6-0').urlsafe(), True, "context.rule.entity.is_active or not context.auth.user.is_guest"),
                                            rule.ActionPermission('6', io.Action.build_key('6-1').urlsafe(), True, "context.rule.entity.is_active"),
                                            rule.ActionPermission('6', io.Action.build_key('6-2').urlsafe(), True, "not context.rule.entity.is_active"),
                                            rule.ActionPermission('6', io.Action.build_key('6-3').urlsafe(), True, "context.auth.user.root_admin"),
                                            rule.ActionPermission('6', io.Action.build_key('6-4').urlsafe(), True, "context.rule.entity.is_active"),
                                            rule.ActionPermission('6', io.Action.build_key('6-5').urlsafe(), True, "not context.auth.user.is_guest"),
                                          ])
    # unique action naming, possible usage is '_kind_id-manage'
    _actions = {
       'manage' : io.Action(id='6-0',
                              arguments={
                                 'create' : ndb.SuperBooleanProperty(required=True),
                                 'name' : ndb.SuperStringProperty(required=True),
                                 'domain' : ndb.SuperKeyProperty(kind='6'),
                                 #'primary_contact' : ndb.SuperKeyProperty(kind='0', required=True),
                              }
                             ),
                
       'suspend' : io.Action(id='6-1',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'activate' : io.Action(id='6-2',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'sudo' : io.Action(id='6-3',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'state' : ndb.SuperStringProperty(required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True)
                              }
                             ),
                
       'log_message' : io.Action(id='6-4',
                              arguments={
                                 'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                 'message' : ndb.SuperTextProperty(required=True),
                                 'note' : ndb.SuperTextProperty(required=True),
                              }
                             ),
                
       'list' : io.Action(id='6-5',
                              arguments={
                              }
                             ),
    }
    
    @property
    def is_active(self):
        return self.state == 'active'
      
    def __todict__(self):
      
      d = super(Domain, self).__todict__()
      
      d['users'] = rule.UserRole.query(namespace=self.key.urlsafe()).fetch()
      d['roles'] = rule.LocalRole.query(namespace=self.key.urlsafe()).fetch()
      d['logs'] = log.Record.query(ancestor=self.key).fetch()
      
      return d
 
    @classmethod
    def manage(cls, args):
        
        action = cls._actions.get('manage')
        context = action.process(args)
        
        if not context.has_error():
          
            @ndb.transactional(xg=True)
            def transaction():
              
                create = context.args.get('create')
                
                if create:
                   entity = cls(state='active', primary_contact=context.auth.user.key)
                else:
                   entity_key = context.args.get('domain')
                   entity = entity_key.get()
             
                context.rule.entity = entity
                 
                if not create:
                   
                   rule.Engine.run(context)
                   
                   if not rule.executable(context):
                      return context.not_authorized()
                    
                elif context.auth.user.is_guest:
                      return context.not_authorized()
                    
                primary_contact = context.auth.user.key
                
                if not primary_contact:
                   primary_contact = context.args.get('primary_contact')
                 
                entity.name = context.args.get('name')
                entity.primary_contact = primary_contact
                entity.put()
                
                namespace = entity.key.urlsafe()
                
                if create:
                  
                  # build a role
                  
                  #from app.domain import business, marketing, product
                  
                  permissions = []
                  
                  # from all objects specified here, the ActionPermission will be built. So the role we are creating
                  # will have all action permissions - taken `_actions` per model
                  """business.Company, business.CompanyContent, business.CompanyFeedback,
                                    marketing.Catalog, marketing.CatalogImage, marketing.CatalogPricetag,
                                    product.Content, product.Instance, product.Template._actions, product.Variant"""
                  objects = [cls, rule.LocalRole, rule.UserRole]
                  
                  for obj in objects:
                      for friendly_action_key, action_instance in obj._actions.items():
                          permissions.append(rule.ActionPermission(kind=obj.get_kind(), 
                                                                   action=action_instance.key.id(),
                                                                   executable=True,
                                                                   condition='True'))
                  
                  role = rule.LocalRole(namespace=namespace, name='Administrators', permissions=permissions)
                  role.put()
                  
                  
                  # build UserRole for creator
                  
                  user_role = rule.UserRole(namespace=namespace, id=str(context.auth.user.key.id()),
                                            name=context.auth.user.primary_email, state='accepted',
                                            roles=[role.key])
                  
                  user_role.put()
                  
                context.log.entities.append((entity,))
                log.Engine.run(context)
                   
                context.status(entity)
               
            try:
                transaction()
            except Exception as e:
                context.transaction_error(e)
            
        return context
      
    @classmethod
    def suspend(cls, args):
      
        action = cls._actions.get('suspend')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('domain')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               entity.state = 'suspended'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
               context.response['suspended'] = True
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
 
    @classmethod
    def activate(cls, args):
      
        action = cls._actions.get('activate')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('domain')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
               
               entity.state = 'active'
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
               context.response['activated'] = True
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
    
    # Ova akcija suspenduje ili aktivira domenu. Ovde cemo dalje opisati posledice suspenzije
    @classmethod
    def sudo(cls, args):
      
        action = cls._actions.get('sudo')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('domain')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               if context.args.get('state') not in ('active', 'suspended'):
                  return context.error('state', 'invalid_state')
               
               entity.state = context.args.get('state')
               entity.put()
               
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
               context.response['activated'] = True
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
    
    @classmethod
    def log_message(cls, args):
      
        action = cls._actions.get('log_message')
        context = action.process(args)
        
        if not context.has_error():
          
           @ndb.transactional(xg=True)
           def transaction():
             
               entity_key = context.args.get('domain')
               entity = entity_key.get()
          
               context.rule.entity = entity
               rule.Engine.run(context)
               
               if not rule.executable(context):
                  return context.not_authorized()
                
               entity.put() # ref project-documentation.py #L-244
  
               context.log.entities.append((entity, {'message' : context.args.get('message'), 'note' : context.args.get('note')}))
               log.Engine.run(context)
                
               context.status(entity)
               context.response['logged_message'] = True
               
           try:
              transaction()
           except Exception as e:
              context.transaction_error(e)
           
        return context
      
    @classmethod
    def list(cls, args):
      
        action = cls._actions.get('list')
        context = action.process(args)
        
        if not context.has_error():
          
           user = context.auth.user
              
           context.response['domains'] = cls.query().fetch()
              
           return context
        