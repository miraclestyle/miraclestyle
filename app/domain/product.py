# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import itertools
import hashlib
 
from app import ndb, util
from app.domain.marketing import Catalog
from app.domain.acl import NamespaceDomain
from app.core.misc import Image

# done!
class Content(ndb.BaseModel, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 43
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # composite index: ancestor:yes - title
    title = ndb.SuperStringProperty('1', required=True)
    body = ndb.SuperTextProperty('2', required=True)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
    }

    @classmethod
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
                 
                  if not entity.key.parent().get().is_usable:
                     return response.error('catalog', 'not_unpublished') 
                       
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response
    
    @classmethod
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
 
            response.process_input(kwds, cls, convert=[('catalog', Catalog, True)])
          
            if response.has_error():
               return response
 
                   
            entity = cls.get_or_prepare(kwds, parent=kwds.get('catalog'))
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
                 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               if not entity.key.parent().get().is_usable:
                  return response.error('catalog', 'not_unpublished') 
                   
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response  
     
  

# done!
class Variant(ndb.BaseModel, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 42
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # http://v6apps.openerp.com/addon/1809
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    description = ndb.SuperTextProperty('2')# soft limit 64kb
    options = ndb.SuperStringProperty('3', repeated=True, indexed=False)# soft limit 1000x
    allow_custom_value = ndb.SuperBooleanProperty('4', default=False, indexed=False)# ovu vrednost buyer upisuje u definisano polje a ona se dalje prepisuje u order line description prilikom Add to Cart
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
    }
    
    @classmethod
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
                 
                  if not entity.key.parent().get().is_usable:
                     return response.error('catalog', 'not_unpublished') 
                       
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response
    
    @classmethod
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
 
            response.process_input(kwds, cls, convert=[('catalog', Catalog, True)])
          
            if response.has_error():
               return response
 
                   
            entity = cls.get_or_prepare(kwds, parent=kwds.get('catalog'))
            
            if entity is None:
               return response.not_found()
             
            if entity and entity.loaded():
                 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               if not entity.key.parent().get().is_usable:
                  return response.error('catalog', 'not_unpublished') 
                   
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response

class Template(ndb.BaseExpando, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 38
    
    # ancestor DomainCatalog (future - root / namespace Domain)
    # composite index: ancestor:yes - name
    product_category = ndb.SuperKeyProperty('1', kind='app.core.misc.ProductCategory', required=True, indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    description = ndb.SuperTextProperty('3', required=True)# soft limit 64kb
    product_uom = ndb.SuperKeyProperty('4', kind='app.core.misc.ProductUOM', required=True, indexed=False)
    unit_price = ndb.SuperDecimalProperty('5', required=True)
    availability = ndb.SuperIntegerProperty('6', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    
    # availability: - ovo cemo pojasniti
    # 'in stock'
    # 'available for order'
    # 'out of stock'
    # 'preorder'
    # 'auto manage inventory - available for order' (poduct is 'available for order' when inventory balance is <= 0)
    # 'auto manage inventory - out of stock' (poduct is 'out of stock' when inventory balance is <= 0)
    # https://support.google.com/merchants/answer/188494?hl=en&ref_topic=2473824
    
    _default_indexed = False
    
    EXPANDO_FIELDS = {
      'variants' : ndb.SuperKeyProperty('7', kind='app.domain.product.Variant', repeated=True),# soft limit 100x
      'contents' : ndb.SuperKeyProperty('8', kind=Content, repeated=True),# soft limit 100x
      'images' : ndb.SuperLocalStructuredProperty(Image, '9', repeated=True),# soft limit 100x
      'weight' : ndb.SuperStringProperty('10'),# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
      'volume' : ndb.SuperStringProperty('11'),# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
      'low_stock_quantity' : ndb.SuperDecimalProperty('12', default='0.00'),# notify store manager when qty drops below X quantity
      'product_instance_count' : ndb.SuperIntegerProperty('13') # cuvanje ovog podatka moze biti od koristi zbog prakticnog limita broja instanci na sistemu
 
    }
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
       'generate_product_instances' : 4,
    }
    
    @classmethod
    def generate_product_instances(cls, **kwds):
        
        response = ndb.Response()
        
        @ndb.transactional(xg=True)
        def transaction():
            
            current = cls.get_current_user()
            
            response.process_input(kwds, cls, convert=[('template', Template)])
            
            if response.has_error():
               return response
           
            product_template_key = kwds.get('template')
            product_template = product_template_key.get()
           
            if current.has_permission('generate_product_instances', product_template):
            
                ndb.delete_multi(Instance.query(ancestor=product_template_key).fetch(keys_only=True))
                
                ndb.delete_multi(InventoryLog.query(ancestor=product_template_key).fetch(keys_only=True))
                
                ndb.delete_multi(InventoryAdjustment.query(ancestor=product_template_key).fetch(keys_only=True))
                 
                variants = ndb.get_multi(product_template.variants)
                packer = list()
                
                for v in variants:
                    packer.append(v.options)
                    
                if not packer:
                   return response.error('generator', 'empty_generator')
                    
                create_variations = itertools.product(*packer)
                
                response['instances'] = list()
                
                i = 1
                for c in create_variations:
                    code = '%s_%s' % (product_template_key.urlsafe(), i)
                    compiled = Instance.md5_variation_combination(product_template_key, c)
                    inst = Instance(parent=product_template_key, id=compiled, code=code)
                    inst.put()
                    inst.new_action('create')
                    inst.record_action()
                    i += 1
                    
                    response['instances'].append(inst)
                 
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
        
        return response
    
    
    @classmethod
    def delete(cls, **kwds):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = cls.get_current_user()
               
               entity = cls.get_or_prepare(kwds, only=False, populate=False)
               
               if entity and entity.loaded():
                  
                  if not entity.domain_is_active:
                     return response.error('domain', 'not_active')
                 
                  if not entity.key.parent().get().is_usable:
                     return response.error('catalog', 'not_unpublished') 
                       
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response
    
    @classmethod
    def manage(cls, **kwds):
        
        response = ndb.Response()
        
        do_not_delete = []

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
            
            skip = ('low_stock_quantity', 'images', 'product_instance_count')
            response.process_input(kwds, cls, skip=skip, convert=[('catalog', Catalog, True)])
          
            if response.has_error():
               return response
           
            entity = cls.get_or_prepare(kwds, parent=kwds.get('catalog'))
            
            if entity is None:
               return response.not_found()
           
            if current.has_permission(('update', 'create'), entity):
            
                images = kwds.get('images')
                if images:
                   sq = 0
                   for img in images:
                      
                       infodata = {'image' : img}
                       delete_file = True
                       response.process_input(infodata, Image, only=('image',), prefix='images_%s' % sq)
                       
                       if not response.has_error():
                          try: 
                              new_image = ndb.BlobManager.field_storage_get_image_sizes(img)
                              entity.images.append(Image(sequence=sq, **new_image))
                              sq += 1
                              delete_file = False
                          except Exception as e:
                              util.logger(e, 'exception')
                              delete_file = True
                              
                       if not delete_file:
                           do_not_delete.append(img)
    
            if entity and entity.loaded():
                 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
              
               if not entity.key.parent().get().is_usable:
                  return response.error('catalog', 'not_unpublished') 
                   
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               
               if not kwds.get('catalog'):
                  response.required('catalog') 
                  
               if response.has_error():
                  return response
                
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
            if len(do_not_delete):
               ndb.BlobManager.field_storage_used_blob(do_not_delete)
        except Exception as e:
            response.transaction_error(e)
       
        return response  
     

# done!
class Instance(ndb.BaseExpando, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 39
    
    # ancestor DomainProductTemplate
    #variant_signature se gradi na osnovu ProductVariant entiteta vezanih za ProductTemplate-a (od aktuelne ProductInstance) preko ProductTemplateVariant 
    #key name ce se graditi tako sto se uradi MD5 na variant_signature
    #query ce se graditi tako sto se prvo izgradi variant_signature vrednost na osnovu odabira od strane krajnjeg korisnika a potom se ta vrednost hesira u MD5 i koristi kao key identifier
    #mana ove metode je ta sto se uvek mora izgraditi kompletan variant_signature, tj moraju se sve varijacije odabrati (svaka varianta mora biti mandatory_variant_type)
    #default vrednost code ce se graditi na osnovu sledecih informacija: ancestorkey-n, gde je n incremental integer koji se dodeljuje instanci prilikom njenog kreiranja
    #ukoliko user ne odabere multivariant opciju onda se za ProductTemplate generise samo jedna ProductInstance i njen key se gradi automatski.
    # composite index: ancestor:yes - code
    code = ndb.SuperStringProperty('1', required=True)
    
    _default_indexed = False
 
    EXPANDO_FIELDS = {
      'availability' : ndb.SuperIntegerProperty('2', required=True), # overide availability vrednosti sa product_template-a, inventory se uvek prati na nivou instanci, state je stavljen na template kako bi se olaksala kontrola state-ova. 
      'description'  : ndb.SuperTextProperty('3', required=True), # soft limit 64kb
      'unit_price' : ndb.SuperDecimalProperty('4', required=True),
      'contents' : ndb.SuperKeyProperty('5', kind=Content, repeated=True), # soft limit 100x
      'images' : ndb.SuperLocalStructuredProperty(Image, '6', repeated=True), # soft limit 100x
      'low_stock_quantity' : ndb.SuperDecimalProperty('7', default='0.00'), # notify store manager when qty drops below X quantity
      'weight' : ndb.SuperStringProperty('8'), # prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
      'volume' : ndb.SuperStringProperty('9'), # prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
      'variant_signature' : ndb.SuperTextProperty('10', required=True),# soft limit 64kb - ova vrednost kao i vrednosti koje kupac manuelno upise kao opcije variante se prepisuju u order line description prilikom Add to Cart
    }
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'update' : 1,
       'create' : 2,
    }
  
    @classmethod
    def md5_variation_combination(cls, product_template_key, codes):
        codes = list(codes)
        codes.insert(0, product_template_key.urlsafe())
        return hashlib.md5(u'-'.join(codes)).hexdigest()
    
    @classmethod
    def manage(cls, **kwds):
        
        response = ndb.Response()
        do_not_delete = []

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
            
            only = ('availability', 'description', 'unit_price', 'contents',
                    'low_stock_quantity', 'weight', 'volume')
 
            response.process_input(kwds, cls, only=only)
          
            if response.has_error():
               return response
  
            entity = cls.get_or_prepare(kwds)
             
            if entity is None:
               return response.not_found()
           
            product_template = entity.key.parent().get()
            catalog = product_template.parent().get()
           
            if not catalog.is_usable:
                entity = cls.get_or_prepare(kwds, cls, only=('availability', 'low_stock_quantity'))
             
            if entity and entity.loaded():
                 
               if not entity.domain_is_active:
                  return response.error('domain', 'not_active') 
               
               if current.has_permission('update', entity):
                   images = kwds.get('images')
                   if images:
                       sq = 0
                       for img in images:
                 
                           infodata = {'image' : img}
                           delete_file = True
                           response.process_input(infodata, Image, only=('image',), prefix='images_%s' % sq)
                           
                           if not response.has_error():
                              try: 
                                  new_image = ndb.BlobManager.field_storage_get_image_sizes(img)
                                  entity.images.append(Image(sequence=sq, **new_image))
                                  sq += 1
                                  delete_file = False
                              except Exception as e:
                                  util.logger(e, 'exception')
                                  
                           if not delete_file:
                              do_not_delete.append(img)
                          
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
            if len(do_not_delete):
               ndb.BlobManager.field_storage_used_blob(do_not_delete)
        except Exception as e:
            response.transaction_error(e)
 
        return response  

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class InventoryLog(ndb.BaseModel, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 40
    
    # ancestor DomainProductInstance (namespace Domain)
    # key za DomainProductInventoryLog ce se graditi na sledeci nacin:
    # key: parent=domain_product_instance.key, id=str(reference_key) ili mozda neki drugi destiled id iz key-a
    # idempotency je moguc ako se pre inserta proverava da li postoji record sa id-jem reference_key
    # not logged
    # composite index: ancestor:yes - logged:desc
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True)
    quantity = ndb.SuperDecimalProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = ndb.SuperDecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query

# done!
class InventoryAdjustment(ndb.BaseModel, ndb.Workflow, NamespaceDomain):
    
    KIND_ID = 41
    
    # ancestor DomainProductInstance (namespace Domain)
    # not logged ?
    adjusted = ndb.SuperDateTimeProperty('1', auto_now_add=True, indexed=False)
    agent = ndb.SuperKeyProperty('2', kind='app.core.acl.User', required=True, indexed=False)
    quantity = ndb.SuperDecimalProperty('3', required=True, indexed=False)
    comment = ndb.SuperStringProperty('4', required=True, indexed=False)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }
    
    """
        # Ova akcija azurira product inventory.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainProductInventoryAdjustment'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'published'. - mozda budemo dozvolili adjustment bez obzira na catalog.state
        product_inventory_adjustment = DomainProductInventoryAdjustment(parent=product_instance_key, agent=agent_key, quantity=var_quantity, comment=var_comment)
        product_inventory_adjustment_key = product_inventory_adjustment.put()
        object_log = ObjectLog(parent=product_inventory_adjustment_key, agent=agent_key, action='create', state='none', log=product_inventory_adjustment)
        object_log.put()
        # ovo bi trebalo ici preko task queue
        # idempotency je moguc ako se pre inserta proverava da li je record sa tim reference-om upisan
        product_inventory_log = DomainProductInventoryLog.query().order(-DomainProductInventoryLog.logged).fetch(1)
        new_product_inventory_log = DomainProductInventoryLog(parent=product_instance_key, id=str(product_inventory_adjustment_key), quantity=product_inventory_adjustment.quantity, balance=product_inventory_log.balance + product_inventory_adjustment.quantity)
        new_product_inventory_log.put()
    """
    
    @classmethod
    def manage(cls, **kwds):
        pass

