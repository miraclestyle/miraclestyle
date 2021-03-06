# -*- coding: utf-8 -*-
'''
Created on Apr 16, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm
from app.util import *


class DomainUserError(Exception):
  
  def __init__(self, message):
    self.message = {'domain_user': message}


class DomainUserInviteSet(orm.BaseModel):
  
  def run(self, context):
    User = context.models['0']
    email = context.input.get('email')
    user = User.query(User.emails == email).get()
    if not user:
      raise DomainUserError('not_found')
    if user.state != 'active':
      raise DomainUserError('not_active')
    already_invited = context.model.build_key(user.key_id_str, namespace=context.namespace).get()
    if already_invited:
      raise DomainUserError('already_invited')
    context._domainuser = context.model(id=user.key_id_str, namespace=context.namespace)
    input_roles = orm.get_multi(context.input.get('roles'))
    roles = []
    for role in input_roles:
      if role.key_namespace == context.namespace:
        roles.append(role.key)
    context._domainuser.populate(name=context.input.get('name'), state='invited', roles=roles)
    user._use_rule_engine = False
    user.domains.append(context.domain.key)
    context._user = user


class DomainUserUpdateSet(orm.BaseModel):
  
  def run(self, context):
    # Avoid rogue roles.
    input_roles = context.input.get('roles')
    roles = []
    for role in input_roles:
      if role._namespace == context._domainuser.key_namespace:
        roles.append(role)
    context._domainuser.name = context.input.get('name')
    context._domainuser.roles = roles


class DomainUserRemoveSet(orm.BaseModel):
  
  def run(self, context):
    context._user = context._domainuser._user.read()
    context._user._use_rule_engine = False
    context._user.domains.remove(orm.Key(urlsafe=context._domainuser.key_namespace))


class DomainUserCleanRolesSet(orm.BaseModel):
  
  def run(self, context):
    roles = orm.get_multi(context._domainuser.roles)
    for role in roles:
      if role is None:
        context._domainuser.roles.remove(role)
