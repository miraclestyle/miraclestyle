# -*- coding: utf-8 -*-
'''
Created on Apr 15, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import json
import copy
import hashlib

from google.appengine.datastore.datastore_query import Cursor

from app import ndb, util, settings  # @todo settings has to GET OUT OF HERE!!!
from app.tools.base import _blob_alter_image
from app.tools.manipulator import set_attr, get_attr, sort_by_list


def build_key_from_signature(context):
  variant_signature = context.input.get('variant_signature')
  key_id = hashlib.md5(json.dumps(variant_signature)).hexdigest()
  product_instance_key = ndb.Key('39', key_id, parent=context.input.get('parent'))
  return product_instance_key


class InstancePrepare(ndb.BaseModel):
  
  def run(self, context):
    product_instance_key = build_key_from_signature(context)
    context.entities[context.model.get_kind()]._instance = context.models['39'](key=product_instance_key)
    context.values[context.model.get_kind()]._instance = context.models['39'](key=product_instance_key)


class InstanceRead(ndb.BaseModel):
  
  def run(self, context):
    product_instance_key = build_key_from_signature(context)
    product_instance = product_instance_key.get()
    context.entities[context.model.get_kind()]._instance = product_instance
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])


class InstanceWrite(ndb.BaseModel):
  
  def run(self, context):
    _instance = context.entities[context.model.get_kind()]._instance
    _instance.put()
    context.records.append((_instance, ))


class InstanceDelete(ndb.BaseModel):
  
  def run(self, context):
    _instance = context.entities[context.model.get_kind()]._instance
    context.records.append((_instance, ))
    _instance.key.delete()


class InstanceUploadImagesSet(ndb.BaseModel):
  
  def run(self, context):
    images = context.input.get('images')
    if not images:
      raise ndb.TerminateAction()
    context.values[context.model.get_kind()]._instance.images.extend(images)


class InstanceUpdateSet(ndb.BaseModel):
  
  def run(self, context):
    entity_images = context.entities[context.model.get_kind()]._instance.images
    updated_images, delete_images = sort_by_list(entity_images, context.input.get('sort_images'), 'image')
    for image in delete_images:
      context.blob_delete.append(image.image)
      updated_images.remove(image)
    context.values[context.model.get_kind()]._instance.images = updated_images


class InstanceWriteImages(ndb.BaseModel):
  
  def run(self, context):
    context.blob_write = [image.image for image in context.entities[context.model.get_kind()]._instance.images]
    if not context.entities[context.model.get_kind()]._field_permissions['_instance']['images']['writable']:
      context.blob_delete = []


class InstanceProcessImages(ndb.BaseModel):
  
  def run(self, context):
    images = context.values[context.model.get_kind()]._instance.images
    if len(images):
      images = ndb.validate_images(images)
      context.blob_delete.extend([image.image for image in images])
      context.values[context.model.get_kind()]._instance.images = images


class InstanceDeleteImages(ndb.BaseModel):
  
  def run(self, context):
    context.blob_delete = [image.image for image in context.entities[context.model.get_kind()]._instance.images]


class TemplateReadInstances(ndb.BaseModel):
  
  page_size = ndb.SuperIntegerProperty('1', indexed=False, required=True, default=10)
  read_all = ndb.SuperBooleanProperty('2', indexed=False, default=False)
  
  def run(self, context):
    Instance = context.models['39']
    ancestor = context.entities[context.model.get_kind()].key
    cursor = Cursor(urlsafe=context.input.get('instances_cursor'))
    if self.read_all:
      _instances = []
      more = True
      offset = 0
      limit = 1000
      while more:
        entities = Instance.query(ancestor=ancestor).fetch(limit=limit, offset=offset)
        if len(entities):
          _instances.extend(entities)
          offset = offset + limit
        else:
          more = False
    else:
      _instances, cursor, more = Instance.query(ancestor=ancestor).fetch_page(self.page_size, start_cursor=cursor)
    if cursor:
      cursor = cursor.urlsafe()
      context.tmp['instances_cursor'] = cursor
    if _instances:
      context.entities[context.model.get_kind()]._instances = _instances
    else:
      context.entities[context.model.get_kind()]._instances = []
    context.values[context.model.get_kind()] = copy.deepcopy(context.entities[context.model.get_kind()])
    context.tmp['instances_more'] = more


class TemplateDelete(ndb.BaseModel):
  
  def run(self, context):
    instance_images = []
    instance_images.extend([instance.images for instance in context.entities[context.model.get_kind()]._instances])
    context.records.extend([(instance, ) for instance in context.entities[context.model.get_kind()]._instances])
    context.blob_delete = [image.image for image in instance_images]
    ndb.delete_multi([instance.key for instance in context.entities[context.model.get_kind()]._instances])


class DuplicateWrite(ndb.BaseModel):
  
  def run(self, context):
    def copy_images(source, destination):
      @ndb.tasklet
      def alter_image_async(source, destination):
        @ndb.tasklet
        def generate():
          original_image = get_attr(context, source)
          results = _blob_alter_image(original_image, copy=True, sufix='copy')
          if results.get('blob_delete'):
            context.blob_delete.append(results['blob_delete'])
          if results.get('new_image'):
            set_attr(context, destination, results['new_image'])
          raise ndb.Return(True)
        yield generate()
        raise ndb.Return(True)
      
      futures = []
      images = get_attr(context, source)
      for i, image in enumerate(images):
        future = alter_image_async('%s.%s' % (source, i), '%s.%s' % (destination, i))
        futures.append(future)
      return ndb.Future.wait_all(futures)
    
    @ndb.tasklet
    def copy_istance_async(instance, source, destination):
      @ndb.tasklet
      def generate():
        copy_images(source, destination)
        instance.set_key(instance.key.id(), parent=copy_template.key)
        context.records.append((instance, ))
        raise ndb.Return(True)
      yield generate()
      raise ndb.Return(True)
    
    def copy_instance_mapper(instances):
      futures = []
      for i, instance in enumerate(instances):
        source = 'entities.%s._instances.%s.images' % (context.model.get_kind(), i)
        destination = 'tmp.new_template._instances.%s.images' % i
        futures.append(copy_istance_async(instance, source, destination))
      return ndb.Future.wait_all(futures)
    
    template = context.entities[context.model.get_kind()]
    copy_template = copy.deepcopy(template)
    copy_template.set_key(None, parent=template.key.parent(), namespace=template.key.namespace())
    copy_template.put()
    context.records.append((copy_template, ))
    context.tmp['copy_template'] = copy_template
    copy_images('entities.%s.images' % context.model.get_kind(), 'tmp.copy_template.images')
    copy_instance_mapper(copy_template._instances)
    ndb.put_multi(copy_template._instances)


class UploadImagesSet(ndb.BaseModel):
  
  def run(self, context):
    images = context.input.get('images')
    if not images:
      raise ndb.TerminateAction()
    context.values[context.model.get_kind()].images.extend(images)


class UpdateSet(ndb.BaseModel):
  
  def run(self, context):
    entity_images = context.entities[context.model.get_kind()].images
    updated_images, delete_images = sort_by_list(entity_images, context.input.get('sort_images'), 'image')
    for image in delete_images:
      context.blob_delete.append(image.image)
      updated_images.remove(image)
    context.values[context.model.get_kind()].images = updated_images


class WriteImages(ndb.BaseModel):
  
  def run(self, context):
    context.blob_write = [image.image for image in context.entities[context.model.get_kind()].images]
    if not context.entities[context.model.get_kind()]._field_permissions['images']['writable']:
      context.blob_delete = []


class ProcessImages(ndb.BaseModel):
  
  def run(self, context):
    images = context.values[context.model.get_kind()].images
    if len(images):
      images = ndb.validate_images(images)
      context.blob_delete.extend([image.image for image in images])
      context.values[context.model.get_kind()].images = images


class DeleteImages(ndb.BaseModel):
  
  def run(self, context):
    context.blob_delete = [image.image for image in context.entities[context.model.get_kind()].images]


class CategoryUpdate(ndb.BaseModel):
  
  cfg = ndb.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    # this code builds leaf categories for selection with complete names, 3.8k of them
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    if not update_file_path:
      raise ndb.TerminateAction()
    Category = context.models['17']
    data = []
    with file(update_file_path) as f:
      for line in f:
        if not line.startswith('#'):
          data.append(line.replace('\n', ''))
    write_data = []
    sep = ' > '
    parent = None
    dig = 0
    for i, item in enumerate(data):
      if i == 100 and settings.DEBUG:
        break
      new_cat = {}
      current = item.split(sep)
      try:
        next = data[i+1].split(sep)
      except IndexError as e:
        next = current
      if len(next) == len(current):
        current_total = len(current)-1
        last = current[current_total]
        parent = current[current_total-1]
        new_cat['id'] = hashlib.md5(last).hexdigest()
        new_cat['parent_record'] = Category.build_key(hashlib.md5(parent).hexdigest())
        new_cat['name'] = last
        new_cat['complete_name'] = ' / '.join(current[:current_total+1])
        new_cat['state'] = 'indexable'
        write_data.append(Category(**new_cat))
    ndb.put_multi(write_data)
