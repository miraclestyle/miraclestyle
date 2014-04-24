# -*- coding: utf-8 -*-
'''
Created on Feb 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb
from app.srv import rule, event, log, cruds
from app.plugins import common
from app.plugins import rule as p_rule


class Filter(ndb.BaseExpando):
  
  _kind = 65
  
  name = ndb.SuperStringProperty('1', required=True)
  kind = ndb.SuperStringProperty('2', required=True)
  query = ndb.SuperJsonProperty('3', required=True, default={})


class Widget(ndb.BaseExpando):
  
  _kind = 62
  
  name = ndb.SuperStringProperty('1', required=True)
  sequence = ndb.SuperIntegerProperty('2', required=True)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  role = ndb.SuperKeyProperty('4', kind='60', required=True)
  search_form = ndb.SuperBooleanProperty('5', required=True, default=True)
  filters = ndb.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('62', repeated=True)
    }
  
  _global_role = rule.GlobalRole(
    permissions=[
      rule.ActionPermission('62', event.Action.build_key('62-0').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('62', event.Action.build_key('62-1').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity._is_system"),
      rule.ActionPermission('62', event.Action.build_key('62-2').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('62', event.Action.build_key('62-3').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity._is_system"),
      rule.ActionPermission('62', event.Action.build_key('62-4').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity._is_system"),
      rule.ActionPermission('62', event.Action.build_key('62-5').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('62', event.Action.build_key('62-6').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('62', event.Action.build_key('62-7').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], False, None,
                           "not context.rule.entity.namespace_entity.state == 'active' or context.rule.entity._is_system"),
      rule.FieldPermission('62', ['name', 'sequence', 'active', 'role', 'search_form', 'filters', '_records'], None, False,
                           "not context.rule.entity.namespace_entity.state == 'active'")
      ]
    )
  
  _actions = {
    'prepare': event.Action(
      id='62-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'create': event.Action(
      id='62-1',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        }
      ),
    'read': event.Action(id='62-2', arguments={'key': ndb.SuperKeyProperty(kind='62', required=True)}),
    'update': event.Action(
      id='62-3',
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sequence': ndb.SuperIntegerProperty(required=True),
        'active': ndb.SuperBooleanProperty(default=True),
        'role': ndb.SuperKeyProperty(kind='60', required=True),
        'search_form': ndb.SuperBooleanProperty(default=True),
        'filters': ndb.SuperJsonProperty()
        }
      ),
    'delete': event.Action(id='62-4', arguments={'key': ndb.SuperKeyProperty(kind='62', required=True)}),
    'search': event.Action(
      id='62-5',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "sequence", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'role': {'operators': ['==', '!='], 'type': ndb.SuperKeyProperty(kind='60')},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty()}
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['role'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': ['role', 'active'],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]},
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['sequence', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'sequence': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'read_records': event.Action(
      id='62-6',
      arguments={
        'key': ndb.SuperKeyProperty(kind='62', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'build_menu': event.Action(
      id='62-7',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      )
    }
  
  _plugins = [common.Prepare(subscriptions=[event.Action.build_key('62-0')], domain_model=True),
              p_rule.Prepare(subscriptions=[event.Action.build_key('62-0')], skip_user_roles=False, strict=False),
              p_rule.Exec(subscriptions=[event.Action.build_key('62-0')]),
              common.Output(subscriptions=[event.Action.build_key('62-0')], output_data={'entity': 'entities.62'})]
  
  @property
  def _is_system(self):
    return self.key_id_str.startswith('system_')
  
  @classmethod
  def complete_save(cls, entity, context):
    role_key = context.input.get('role')
    role = role_key.get()
    if role.key_namespace != entity.key_namespace:  # Both, the role and the entity namespace must match. Perhaps, this could be done with rule engine?
      raise rule.ActionDenied(context)
    filters = []
    input_filters = context.input.get('filters')
    for input_filter in input_filters:
      filters.append(Filter(**input_filter))
    values = {'name': context.input.get('name'),
              'sequence': context.input.get('sequence'),
              'active': context.input.get('active'),
              'role': role_key,
              'search_form': context.input.get('search_form'),
              'filters': filters}
    return values
  
  @classmethod
  def create(cls, context):
    domain_key = context.input.get('domain')
    entity = cls(namespace=domain_key.urlsafe())
    values = cls.complete_save(entity, context)
    context.cruds.entity = cls(namespace=domain_key.urlsafe())
    context.cruds.values = values
    cruds.Engine.create(context)
  
  @classmethod
  def update(cls, context):
    entity_key = context.input.get('entity_key')
    entity = entity_key.get()
    values = cls.complete_save(entity, context)
    context.cruds.entity = entity
    context.cruds.values = values
    cruds.Engine.update(context)
  
  """@classmethod
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    context.cruds.entity = cls(namespace=domain_key.urlsafe())
    cruds.Engine.prepare(context)
    entity = context.output['entity']
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)"""
  
  @classmethod
  def read(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read(context)
    entity = context.output['entity']
    context.output['roles'] = cls.selection_roles_helper(entity.key_namespace)
  
  @classmethod
  def delete(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.delete(context)
  
  @classmethod
  def search(cls, context):
    context.cruds.entity = cls
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.search(context)
  
  @classmethod
  def read_records(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read_records(context)
  
  @classmethod
  def build_menu(cls, context):
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    context.rule.entity = cls(namespace=domain.key_namespace)
    rule.Engine.run(context)
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=domain.key.urlsafe())
    domain_user = domain_user_key.get()
    if domain_user:
      widgets = cls.query(cls.active == True,
                          cls.role.IN(domain_user.roles),
                          namespace=domain.key_namespace).order(cls.sequence).fetch()
      context.output['menu'] = widgets
      context.output['domain'] = domain
  
  @classmethod
  def selection_roles_helper(cls, namespace):  # @todo This method will die, and ajax DomainRole.search() will be used instead!?
    return rule.DomainRole.query(rule.DomainRole.active == True, namespace=namespace).fetch()
