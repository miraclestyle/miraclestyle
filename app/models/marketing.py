# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime

from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.marketing import *


class CatalogPricetag(orm.BaseModel):
  
  _kind = 34
  
  product_template = orm.SuperKeyProperty('1', kind='38', required=True, indexed=False)
  position_top = orm.SuperFloatProperty('2', required=True, indexed=False)
  position_left = orm.SuperFloatProperty('3', required=True, indexed=False)
  value = orm.SuperStringProperty('4', required=True, indexed=False)


class CatalogImage(Image):
  
  _kind = 36
  
  pricetags = orm.SuperLocalStructuredProperty(CatalogPricetag, '8', repeated=True)


class Catalog(orm.BaseExpando):
  
  _kind = 35
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)
  publish_date = orm.SuperDateTimeProperty('4', required=True)
  discontinue_date = orm.SuperDateTimeProperty('5', required=True)
  state = orm.SuperStringProperty('6', required=True, default='unpublished', choices=['unpublished', 'locked', 'published', 'discontinued'])
  
  _default_indexed = False
  
  _expando_fields = {
    'cover': orm.SuperLocalStructuredProperty(CatalogImage, '7'),
    'cost': orm.SuperDecimalProperty('8')
    }
  
  _virtual_fields = {
    '_images': orm.SuperLocalStructuredProperty(CatalogImage, repeated=True),
    '_records': orm.SuperRecordProperty('35')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('35', [orm.Action.build_key('35', 'prepare'),
                                  orm.Action.build_key('35', 'create'),
                                  orm.Action.build_key('35', 'read'),
                                  orm.Action.build_key('35', 'update'),
                                  orm.Action.build_key('35', 'upload_images'),
                                  orm.Action.build_key('35', 'search'),
                                  orm.Action.build_key('35', 'lock'),
                                  orm.Action.build_key('35', 'discontinue'),
                                  orm.Action.build_key('35', 'log_message'),
                                  orm.Action.build_key('35', 'duplicate')], False, 'entity._original.namespace_entity.state != "active"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'update'),
                                  orm.Action.build_key('35', 'lock'),
                                  orm.Action.build_key('35', 'upload_images')], False, 'entity._original.state != "unpublished"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'process_images'),
                                  orm.Action.build_key('35', 'process_cover'),
                                  orm.Action.build_key('35', 'process_duplicate'),
                                  orm.Action.build_key('35', 'delete'),
                                  orm.Action.build_key('35', 'publish'),
                                  orm.Action.build_key('35', 'sudo'),
                                  orm.Action.build_key('35', 'index'),
                                  orm.Action.build_key('35', 'unindex'),
                                  orm.Action.build_key('35', 'cron')], False, 'True'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'discontinue'),
                                  orm.Action.build_key('35', 'duplicate')], False, 'entity._original.state != "published"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'read')], True, 'entity._original.state == "published" or entity._original.state == "discontinued"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'publish')], True, 'user._is_taskqueue and entity._original.state != "published" and entity._original._is_eligible'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'discontinue')], True, 'user._is_taskqueue and entity._original.state != "discontinued"'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'sudo')], True, 'user._root_admin'),
      orm.ActionPermission('35', [orm.Action.build_key('35', 'process_images'),
                                  orm.Action.build_key('35', 'process_cover'),
                                  orm.Action.build_key('35', 'process_duplicate'),
                                  orm.Action.build_key('35', 'delete'),
                                  orm.Action.build_key('35', 'index'),
                                  orm.Action.build_key('35', 'unindex'),
                                  orm.Action.build_key('35', 'cron')], True, 'user._is_taskqueue'),
      orm.FieldPermission('35', ['created', 'updated', 'state', 'cover'], False, None, 'True'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], False, False,
                          'entity.namespace_entity.state != "active"'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], False, None,
                          'entity.state != "unpublished"'),
      orm.FieldPermission('35', ['state'], True, None,
                          '(action.key_id_str == "create" and entity.state == "unpublished") or (action.key_id_str == "lock" and entity.state == "locked") or (action.key_id_str == "publish" and entity.state == "published") or (action.key_id_str == "discontinue" and entity.state == "discontinued") or (action.key_id_str == "sudo" and (entity.state == "published" or entity.state == "discontinued"))'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', '_images'], None, True,
                          'entity._original.state == "published" or entity._original.state == "discontinued"'),
      orm.FieldPermission('35', ['_records.note'], True, True,
                          'user._root_admin'),
      orm.FieldPermission('35', ['_records.note'], False, False,
                          'not user._root_admin'),
      orm.FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], None, True,
                          'user._is_taskqueue or user._root_admin'),
      orm.FieldPermission('35', ['_images'], True, None,
                          'action.key_id_str == "process_images" and (user._is_taskqueue or user._root_admin)'),
      orm.FieldPermission('35', ['cover'], True, None,
                          'action.key_id_str == "process_cover" and (user._is_taskqueue or user._root_admin)')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('35', 'prepare'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'upload_url': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            BlobURL(cfg={'bucket': settings.CATALOG_IMAGE_BUCKET}),
            Set(cfg={'d': {'output.entity': '_catalog',
                           'output.upload_url': '_blob_url'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'create'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'name': orm.SuperStringProperty(required=True),
        'publish_date': orm.SuperDateTimeProperty(required=True),
        'discontinue_date': orm.SuperDateTimeProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'unpublished'},
                     'd': {'_catalog.name': 'input.name',
                           '_catalog.publish_date': 'input.publish_date',
                           '_catalog.discontinue_date': 'input.discontinue_date'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'name': orm.SuperStringProperty(required=True),
        'sort_images': orm.SuperStringProperty(repeated=True),
        'pricetags': orm.SuperLocalStructuredProperty(CatalogImage, repeated=True),  # must be like this because we need to match the pricetags with order.....
        'publish_date': orm.SuperDateTimeProperty(required=True),
        'discontinue_date': orm.SuperDateTimeProperty(required=True),
        'search_cursor': orm.SuperIntegerProperty(default=0)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            CatalogUpdateSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_cover', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'upload_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        '_images': orm.SuperLocalStructuredImageProperty(CatalogImage, repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_catalog._images': 'input._images'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_images', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'process_images'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'catalog_image_keys': orm.SuperKeyProperty(kind='36', repeated=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_cover', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'process_cover'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            CatalogProcessCoverSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.Delete() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('35', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'created', 'operator': 'desc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name', 'state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'created': {'operators': ['asc', 'desc']},
            'update': {'operators': ['asc', 'desc']}
            }
          ),
        'cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'lock'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True)
        #'note': orm.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'locked'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'publish'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True)
        #'note': orm.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'published'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'index', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'discontinue'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True)
        #'note': orm.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_catalog.state': 'discontinued'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'unindex', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'sudo'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'state': orm.SuperStringProperty(required=True, choices=['published', 'discontinued']),
        'index_state': orm.SuperStringProperty(choices=['index', 'unindex']),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_catalog.state': 'input.state'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),  # 'index_state': 'input.index_state',  # @todo We embed this field on the fly, to indicate what administrator has chosen!
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_model': '35'},
                               {'action_id': 'input.index_state', 'key': '_catalog.key_urlsafe'})])  # @todo What happens if input.index_state is not supplied (e.g. None)?
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),  # @todo Should run out of transaction!!!
            Set(cfg={'d': {'output.entity': '_catalog'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'log_message'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.SearchWrite() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('35', 'index'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogSearchDocumentWrite(cfg={'index': settings.CATALOG_INDEX,
                                            'max_doc': settings.CATALOG_DOCUMENTS_PER_INDEX})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'sra': {'log_entity': False}}),  # @todo Perhaps entity should be logged in order to refresh updated field? - 'd': {'message': 'tmp.message'}
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      # marketing.SearchDelete() plugin deems this action to allways execute in taskqueue!
      key=orm.Action.build_key('35', 'unindex'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogSearchDocumentDelete(cfg={'index': settings.CATALOG_INDEX,
                                             'max_doc': settings.CATALOG_DOCUMENTS_PER_INDEX})
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'sra': {'log_entity': False}}),  # @todo Perhaps entity should be logged in order to refresh updated field? - 'd': {'message': 'tmp.message'}
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'cron'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogCronPublish(cfg={'page': 10}),
            CatalogCronDiscontinue(cfg={'page': 10}),
            CatalogCronDelete(cfg={'page': 10,
                                   'unpublished_life': settings.CATALOG_UNPUBLISHED_LIFE,
                                   'discontinued_life': settings.CATALOG_DISCONTINUED_LIFE}),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_catalog'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_duplicate', 'action_model': '35'},
                               {'key': '_catalog.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('35', 'process_duplicate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Duplicate(),  # @todo Not sure about this!!
            Write(),  # @todo Not sure about this!!
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      )
    ]
  
  @property
  def _is_eligible(self):
    # @todo Here we implement the logic to validate if catalog publisher has funds to support catalog publishing!
    return True


class CatalogIndex(orm.BaseExpando):
  
  _kind = 82
  
  _default_indexed = False
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('82', [orm.Action.build_key('82', 'search')], True, 'True')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('82', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [{'field': 'kind', 'value': '35', 'operator': '=='}], 'order_by': {'field': 'created', 'operator': 'desc'}},
          filters={
            'query_string': {'operators': ['=='], 'type': orm.SuperStringProperty()},
            'kind': {'operators': ['=='], 'type': orm.SuperStringProperty()},
            'name': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()}
            },
          indexes=[
            {'filter': ['kind'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name', 'state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'created': {'operators': ['asc', 'desc'],
                        'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}},
            'update': {'operators': ['asc', 'desc'],
                       'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}}
            }
          ),
        'cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            CatalogSearch(cfg={'index': settings.CATALOG_INDEX, 'page': settings.SEARCH_PAGE, 'document': True}),
            #DocumentDictConverter(),
            #DocumentEntityConverter(),
            #RulePrepare(cfg={'path': 'entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.total_matches': '_total_matches',
                           'output.documents_count': '_documents_count',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      )
    ]
