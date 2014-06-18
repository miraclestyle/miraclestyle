# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json
import copy
import string
import collections

from google.appengine.api import taskqueue

from app import ndb, util
from app.lib.attribute_manipulator import set_attr, get_attr, get_meta  # @todo To rename lib to tools!
from app.lib.blob_manipulator import create_upload_url, parse, alter_image  # @todo To rename lib to tools!
from app.lib.rule_manipulator import prepare, read, write, _is_structured_field  # @todo To rename lib to tools!
from app.lib.search import ndb_search, document_search, document_from_entity, documents_to_indexes, entities_to_indexes, documents_write, documents_delete  # @todo To rename lib to tools!


class Context(ndb.BaseModel):
  
  def run(self, context):
    # @todo Following lines are temporary, until we decide where and how to distribute them!
    context.user = context.models['0'].current_user()
    caller_user_key = context.input.get('caller_user')
    if context.user._is_taskqueue:
      if caller_user_key:
        caller_user = caller_user_key.get()
        if caller_user:
          context.user = caller_user
      else:
        context.user = context.models['0'].get_system_user()
    context.namespace = None
    context.domain = None
    domain_key = context.input.get('domain')
    if domain_key:
      context.domain = domain_key.get()
      context.namespace = context.domain.key_namespace
    if not hasattr(context, 'entities'):
      context.entities = {}
    if not hasattr(context, 'values'):
      context.values = {}
    if not hasattr(context, 'callbacks'):
      context.callbacks = []
    if not hasattr(context, 'records'):
      context.records = []
    if not hasattr(context, 'blob_delete'):
      context.blob_delete = []
    if not hasattr(context, 'blob_write'):
      context.blob_write = []
    if not hasattr(context, 'blob_transform'):
      context.blob_transform = None
    if not hasattr(context, 'search_documents'):
      context.search_documents = []
    if not hasattr(context, 'search_documents_total_matches'):
      context.search_documents_total_matches = None
    if not hasattr(context, 'search_documents_count'):
      context.search_documents_count = None


class Set(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    static_values = self.config.get('static', {})
    dynamic_values = self.config.get('dynamic', {})
    for key, value in static_values.items():
      set_attr(context, key, value)
    for key, value in dynamic_values.items():
      set_attr(context, key, get_attr(context, value))


class Prepare(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.config, list):
      self.config = []
    if not len(self.config):
      self.config = [{'model': 'models.'  + context.model.get_kind(),
                      'parent': None,
                      'namespace': 'namespace',
                      'save': 'entities.' + context.model.get_kind(),
                      'copy': 'values.' + context.model.get_kind()}]
    for config in self.config:
      model_path = config.get('model')
      model = get_attr(context, model_path)
      parent_path = config.get('parent')
      namespace_path = config.get('namespace')
      parent = get_attr(context, parent_path)
      namespace = get_attr(context, namespace_path)
      if parent != None:
        namespace = None
      save_path = config.get('save')
      copy_path = config.get('copy')
      set_attr(context, save_path, model(parent=parent, namespace=namespace))
      if copy_path != None:
        set_attr(context, copy_path, model(parent=parent, namespace=namespace))


class Read(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    keys = []
    if not isinstance(self.config, list):
      self.config = []
    if not len(self.config):
      self.config = [{'source': 'input.key',
                      'save': 'entities.' + context.model.get_kind(),
                      'copy': 'values.' + context.model.get_kind()}]
    for config in self.config:
      source_path = config.get('source')
      source = get_attr(context, source_path)
      if source and isinstance(source, ndb.Key):
        keys.append(source)
    ndb.get_multi(keys)
    for config in self.config:
      source_path = config.get('source')
      source = get_attr(context, source_path)
      entity = None
      if source and isinstance(source, ndb.Key):
        entity = source.get()
      save_path = config.get('save')
      copy_path = config.get('copy')
      set_attr(context, save_path, entity)
      if copy_path != None:
        set_attr(context, copy_path, copy.deepcopy(entity))


class Write(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    write_entities = []
    if not isinstance(self.config, dict):
      self.config = {}
    entity_paths = self.config.get('paths', ['entities.' + str(context.model.get_kind())])
    parent_path = self.config.get('parent', None)
    namespace_path = self.config.get('namespace', 'namespace')
    parent = get_attr(context, parent_path)
    namespace = get_attr(context, namespace_path)
    for entity_path in entity_paths:
      entities = get_attr(context, entity_path)
      if isinstance(entities, dict):
        for key, entity in entities.items():
          if entity and isinstance(entity, ndb.Model):
            write_entities.append(entity)
      elif isinstance(entities, list):
        for entity in entities:
          if entity and isinstance(entity, ndb.Model):
            write_entities.append(entity)
      elif entities and isinstance(entities, ndb.Model):
        write_entities.append(entities)
    # @todo This parent/namespace block needs improvement!
    if parent != None:
      namespace = None
    for entity in write_entities:
      if not hasattr(entity, 'key'):
        entity.set_key(None, parent=parent, namespace=namespace)
    ndb.put_multi(write_entities)


class Delete(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    delete_keys = []
    if not isinstance(self.config, dict):
      self.config = {}
    entity_paths = self.config.get('paths', ['entities.' + str(context.model.get_kind())])
    for entity_path in entity_paths:
      entities = get_attr(context, entity_path)
      if isinstance(entities, dict):
        for key, entity in entities.items():
          if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
            delete_keys.append(entity.key)
          elif entity and isinstance(entity, ndb.Key):
            delete_keys.append(entity)
      elif isinstance(entities, list):
        for entity in entities:
          if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
            delete_keys.append(entity.key)
          elif entity and isinstance(entity, ndb.Key):
            delete_keys.append(entity)
      elif entities and hasattr(entities, 'key') and isinstance(entities.key, ndb.Key):
        delete_keys.append(entities.key)
      elif entities and isinstance(entities, ndb.Key):
        delete_keys.append(entities)
    ndb.delete_multi(delete_keys)


class Search(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    model_path = self.config.get('model', 'models.' + str(context.model.get_kind()))
    argument_path = self.config.get('argument', 'input.search')
    urlsafe_cursor_path = self.config.get('read_cursor', 'input.search_cursor')
    namespace_path = self.config.get('namespace', 'namespace')
    page_size = self.config.get('page', 10)
    write_entities_path = self.config.get('write_entities', 'entities')
    write_cursor_path = self.config.get('write_cursor', 'search_cursor')
    write_more_path = self.config.get('write_more', 'search_more')
    model = get_attr(context, model_path)
    argument = get_attr(context, argument_path)
    urlsafe_cursor = get_attr(context, urlsafe_cursor_path)
    namespace = get_attr(context, namespace_path)
    result = ndb_search(model, argument, page_size=page_size, urlsafe_cursor=urlsafe_cursor, namespace=namespace)
    set_attr(context, write_entities_path, result['entities'])
    set_attr(context, write_cursor_path, result['cursor'])
    set_attr(context, write_more_path, result['more'])


class RecordRead(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    @ndb.tasklet
    def async(entity):
      if entity.key_namespace and entity.agent.id() != 'system':
        domain_user_key = ndb.Key('8', str(entity.agent.id()), namespace=entity.key_namespace)
        agent = yield domain_user_key.get_async()
        agent = agent.name
      else:
        agent = yield entity.agent.get_async()
        agent = agent._primary_email
      entity._agent = agent
      action_parent = entity.action.parent()
      modelclass = entity._kind_map.get(action_parent.kind())
      action_id = entity.action.id()
      if modelclass and hasattr(modelclass, '_actions'):
        for action in modelclass._actions:
          if entity.action == action.key:
            entity._action = '%s.%s' % (modelclass.__name__, action_id)
            break
      raise ndb.Return(entity)
    
    @ndb.tasklet
    def helper(entities):
      results = yield map(async, entities)
      raise ndb.Return(results)
    
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    entity = get_attr(context, entity_path)
    if entity and hasattr(entity, 'key') and isinstance(entity.key, ndb.Key):
      model = context.models['5']
      argument = {'filters': [{'field': 'ancestor', 'operator': '==', 'value': entity.key}],
                  'order_by': {'field': 'logged', 'operator': 'desc'}}
      urlsafe_cursor_path = self.config.get('read_cursor', 'input.records_cursor')
      page_size = self.config.get('page', 10)
      write_entities_path = self.config.get('write_entities', entity_path + '._records')
      write_cursor_path = self.config.get('write_cursor', 'records_cursor')
      write_more_path = self.config.get('write_more', 'records_more')
      urlsafe_cursor = get_attr(context, urlsafe_cursor_path)
      result = ndb_search(model, argument, page_size=page_size, urlsafe_cursor=urlsafe_cursor)
      entities = helper(result['entities'])
      entities = [entity for entity in entities.get_result()]
      set_attr(context, write_entities_path, entities)
      set_attr(context, write_cursor_path, result['cursor'])
      set_attr(context, write_more_path, result['more'])


class RecordWrite(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    model = context.models['5']
    records = []
    write_arguments = {}
    records_paths = self.config.get('paths', [])
    static_arguments = self.config.get('static', {})
    dynamic_arguments = self.config.get('dynamic', {})
    for records_path in records_paths:
      result = get_attr(context, records_path)
      if isinstance(result, dict):
        context.records.extend([(record, ) for key, record in result.items()])
      elif isinstance(result, list):
        context.records.extend([(record, ) for record in result])
      else:
        context.records.append((result, ))
    write_arguments.update(static_arguments)
    for key, value in dynamic_arguments.items():
      write_arguments[key] = get_attr(context, value)
    if len(context.records):
      for config in context.records:
        arguments = {}
        kwargs = {}
        entity = config[0]
        try:
          entity_arguments = config[1]
        except:
          entity_arguments = {}
        arguments.update(write_arguments)
        arguments.update(entity_arguments)
        log_entity = arguments.pop('log_entity', True)
        if len(arguments):
          for key, value in arguments.items():
            if entity._field_permissions['_records'][key]['writable']:
              kwargs[key] = value
        record = model(parent=entity.key, agent=context.user.key, action=context.action.key, **kwargs)
        if log_entity is True:
          log_entity = entity
        if log_entity:
          record.log_entity(log_entity)
        records.append(record)
    if len(records):
      recorded = ndb.put_multi(records)
    context.records = []


class CallbackNotify(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    dynamic_data = self.config.get('dynamic', {})
    static_data = {}
    static_data.update({'action_id': 'initiate', 'action_model': '61'})
    static_data['caller_entity'] = context.entities[context.model.get_kind()].key_urlsafe
    context.callbacks.append(('notify', static_data, dynamic_data))


class CallbackExec(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  def run(self, context):
    if not isinstance(self.config, list):
      self.config = []
    queues = {}
    url = '/task/io_engine_run'
    context.callbacks.extend(self.config)
    if ndb.in_transaction():
      context.callbacks = context.callbacks[:5]
    if len(context.callbacks):
      for callback in context.callbacks:
        data = {}
        queue_name, static_data, dynamic_data = callback
        data.update(static_data)
        for key, value in dynamic_data.items():
          data[key] = get_attr(context, value)
        if data.get('caller_user') == None:
          data['caller_user'] = get_attr(context, 'user.key_urlsafe')
        if data.get('caller_action') == None:
          data['caller_action'] = get_attr(context, 'action.key_urlsafe')
        if queue_name not in queues:
          queues[queue_name] = []
        queues[queue_name].append(taskqueue.Task(url=url, payload=json.dumps(data)))
    if len(queues):
      for queue_name, tasks in queues.items():
        queue = taskqueue.Queue(name=queue_name)
        queue.add(tasks, transactional=ndb.in_transaction())
    context.callbacks = []


class BlobURL(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    gs_bucket_name = self.config.get('bucket', None)
    upload_url_path = self.config.get('url', 'input.upload_url')
    save_path = self.config.get('save', 'output.upload_url')
    upload_url = get_attr(context, upload_url_path)
    if upload_url:
      set_attr(context, save_path, create_upload_url(upload_url, gs_bucket_name))
      raise event.TerminateAction()


class BlobUpdate(ndb.BaseModel):  # @todo Not migrated!
  
  blob_delete = ndb.SuperStringProperty('1', indexed=False)
  blob_write = ndb.SuperStringProperty('2', indexed=False)
  
  def run(self, context):
    if self.blob_delete:
      blob_delete = get_attr(context, self.blob_delete)
    else:
      blob_delete = context.blob_delete
    if blob_delete:
      context.blob_unused.extend(parse(blob_delete))
    if self.blob_write:
      blob_write = get_attr(context, self.blob_write)
    else:
      blob_write = context.blob_write
    if blob_write:
      blob_write = parse(blob_write)
      for blob_key in blob_write:
        if blob_key in context.blob_unused:
          context.blob_unused.remove(blob_key)


class BlobAlterImage(ndb.BaseModel):  # @todo Not migrated!
  
  source = ndb.SuperStringProperty('1', indexed=False)
  destination = ndb.SuperStringProperty('2', indexed=False)
  config = ndb.SuperJsonProperty('3', indexed=False, required=True, default={})
  
  def run(self, context):
    if self.source:
      original_image = get_attr(context, self.source)
    else:
      original_image = context.blob_transform
    if original_image:
      results = alter_image(original_image, **self.config)
      if results.get('blob_delete'):
        context.blob_delete.append(results['blob_delete'])
      if results.get('new_image'):
        set_attr(context, self.destination, results['new_image'])


class BlobAlterImages(ndb.BaseModel):  # @todo Not migrated!
  
  source = ndb.SuperStringProperty('1', indexed=False)
  destination = ndb.SuperStringProperty('2', indexed=False)
  config = ndb.SuperJsonProperty('3', indexed=False, required=True, default={})
  
  def run(self, context):
    @ndb.tasklet
    def alter_image_async(source, destination):
      @ndb.tasklet
      def generate():
        original_image = get_attr(context, source)
        results = alter_image(original_image, **self.config)
        if results.get('blob_delete'):
          context.blob_delete.append(results['blob_delete'])
        if results.get('new_image'):
          set_attr(context, destination, results['new_image'])
        raise ndb.Return(True)
      yield generate()
      raise ndb.Return(True)
    
    futures = []
    images = get_attr(context, self.source)
    for i, image in enumerate(images):
      source = '%s.%s' % (self.source, i)
      destination = '%s.%s' % (self.destination, i)
      future = alter_image_async(source, destination)
      futures.append(future)
    return ndb.Future.wait_all(futures)


class ActionDenied(Exception):
  
  def __init__(self, context):
    self.message = {'action_denied': context.action}


class RulePrepare(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    values_path = self.config.get('from', 'values.' + str(context.model.get_kind()))
    entity_path = self.config.get('to', 'entities.' + str(context.model.get_kind()))
    skip_user_roles = self.config.get('skip_user_roles', False)  # @todo Not sure if we should rename 'skip_user_roles' to 'skip'?
    strict = self.config.get('strict', False)
    values = get_attr(context, values_path)
    entities = get_attr(context, entity_path)
    util.logger('RulePrepare entity: %s' % entities)
    if isinstance(entities, dict):
      for key, entity in entities.items():
        context.entity = entities.get(key)
        context.value = values.get(key)
        prepare(context, skip_user_roles, strict)
    elif isinstance(entities, list):
      for entity in entities:
        context.entity = entity
        context.value = None
        prepare(context, skip_user_roles, strict)
    else:
      context.entity = entities
      context.value = values
      prepare(context, skip_user_roles, strict)


class RuleRead(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    entities = get_attr(context, entity_path)
    if isinstance(entities, dict):
      for key, entity in entities.items():
        read(entity)
    elif isinstance(entities, list):
      for entity in entities:
        read(entity)
    else:
      read(entities)


class RuleWrite(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    values_path = self.config.get('from', 'values.' + str(context.model.get_kind()))
    entity_path = self.config.get('to', 'entities.' + str(context.model.get_kind()))
    values = get_attr(context, values_path)
    entity = get_attr(context, entity_path)
    if values and entity:
      write(entity, values)


class RuleExec(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    action_path = self.config.get('action', 'action.key_urlsafe')
    entity = get_attr(context, entity_path)
    action = get_attr(context, action_path)
    if entity and hasattr(entity, '_action_permissions'):
      if not entity._action_permissions[action]['executable']:
        raise ActionDenied(context)
    else:
      raise ActionDenied(context)


class DocumentWrite(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    documents = []
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    fields = self.config.get('fields', {})
    max_doc = self.config.get('max_doc', 200)
    entities = get_attr(context, entity_path)
    if isinstance(entities, dict):
      for key, entity in entities.items():
        documents.append(document_from_entity(entity, fields))
    elif isinstance(entities, list):
      for entity in entities:
        documents.append(document_from_entity(entity, fields))
    else:
      documents.append(document_from_entity(entities, fields))
    indexes = documents_to_indexes(documents)
    documents_write(indexes, documents_per_index=max_doc)


class DocumentDelete(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    documents = []
    entity_path = self.config.get('path', 'entities.' + str(context.model.get_kind()))
    max_doc = self.config.get('max_doc', 200)
    entities = get_attr(context, entity_path)
    if isinstance(entities, dict):
      for key, entity in entities.items():
        documents.append(entity)
    elif isinstance(entities, list):
      for entity in entities:
        documents.append(entity)
    else:
      documents.append(entities)
    indexes = entities_to_indexes(documents)
    documents_delete(indexes, documents_per_index=max_doc)


class DocumentSearch(ndb.BaseModel):
  
  config = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.config, dict):
      self.config = {}
    namespace_path = self.config.get('namespace', 'namespace')
    namespace = get_attr(context, namespace_path)
    index_name = self.config.get('index', str(context.model.get_kind()))
    argument_path = self.config.get('argument', 'input.search')
    urlsafe_cursor_path = self.config.get('read_cursor', 'input.search_cursor')
    page_size = self.config.get('page', 10)
    fields = self.config.get('fields', None)
    write_documents_path = self.config.get('write_documents', 'search_documents')
    write_documents_count_path = self.config.get('write_documents_count', 'search_documents_count')
    write_documents_total_matches_path = self.config.get('write_documents_total_matches', 'search_documents_total_matches')
    write_cursor_path = self.config.get('write_cursor', 'search_cursor')
    write_more_path = self.config.get('write_more', 'search_more')
    argument = get_attr(context, argument_path)
    urlsafe_cursor = get_attr(context, urlsafe_cursor_path)
    result = document_search(index_name, argument, page_size=page_size, urlsafe_cursor=urlsafe_cursor, namespace=namespace, fields=fields)
    set_attr(context, write_documents_path, result['documents'])
    set_attr(context, write_documents_count_path, result['documents_count'])
    set_attr(context, write_documents_total_matches_path, result['total_matches'])
    set_attr(context, write_cursor_path, result['search_cursor'])
    set_attr(context, write_more_path, result['search_more'])


class DocumentDictConverter(ndb.BaseModel):
  
  def run(self, context):
    entities = []
    if len(context.search_documents):
      for document in context.search_documents:
        dic = {}
        dic['doc_id'] = document.doc_id
        dic['language'] = document.language
        dic['rank'] = document.rank
        fields = document.fields
        for field in fields:
          dic[field.name] = field.value
        entities.append(dic)
    context.entities = entities


class DocumentEntityConverter(ndb.BaseModel):
  
  def run(self, context):
    if len(context.search_documents):
      context.entities = ndb.get_multi([document.doc_id for document in context.search_documents])