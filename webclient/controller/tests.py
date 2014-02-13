# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular
 
from app import ndb
from app.srv import io

class Reset(Angular):
  
  def respond(self):
    
      from app import srv
      from app import domain
      from app import opt
    
      models = [srv.auth.Domain, srv.auth.User, srv.rule.DomainRole, srv.rule.DomainUser,
                domain.business.Company, domain.business.CompanyContent, domain.marketing.Catalog,
                domain.marketing.CatalogImage, domain.marketing.CatalogPricetag, domain.product.Content,
                domain.product.Instance, domain.product.InventoryAdjustment, domain.product.InventoryLog,
                domain.product.Variant, domain.product.Template, opt.buyer.Address, opt.buyer.Collection, 
                opt.misc.Content, opt.misc.ProductCategory, opt.misc.SupportRequest]
      
      keys = []
      
      for mod in models:
          keys.extend(mod.query().fetch(keys_only=True))
      
      ndb.delete_multi(keys)
      
      return {'models' : [f.__name__ for f in models]}

class Submitter(Angular):
  
    def respond(self):
        return self.render('tests/submitter.html')
      
      
class Endpoint(Angular):
    
    def respond(self):
        output = io.Engine.run(self.get_input())
        return output
      
class Engine(Angular):

    def respond(self):      
        output = io.Engine.taskqueue_run(self.get_input())
        return output
         
 
register(('/endpoint', Endpoint), 
         ('/reset', Reset),
         ('/engine_run', Engine), 
         ('/submitter', Submitter))