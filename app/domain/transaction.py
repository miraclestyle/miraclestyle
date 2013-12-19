# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

################################################################################
# /domain/transaction.py - ako ce se sve transakcije raditi iz perspektive
# company, tj. iz perspektive domain-a onda ima smisla da se nadje u /domain/ folderu
################################################################################

# upiti sa strane usera, ako je na grupi postavljen namespace, ce se resavati odvojenim recordima
# koji ce cuvati kljuceve na recorde a biti vezani ancestor pathom na usera.

# ima uticaj na class-e: Order, BillingOrder, BillingLog, BillingCreditAdjustment
# analytical account entry lines should be treated as expense/revenue lines, where debit is expense, credit is revenue, 
# and no counter entry lines will exist, that is entry will be allowed to remain unbalanced!

# prvo definisati minimalne pasivne modele: category
# definisati im osnovne funkcije i indexe
# potom definisati transakcione modele: group, entry, line
# definisati im osnovne funkcije i indexe
# nakon toga definisati aktivne kompozitne indexe
# pregledati order modele i prepraviti ih da rade sa transakcionim modelima

# App Engine clock times are always expressed in coordinated universal time (UTC). 
# This becomes relevant if you use the current date or time (datetime.datetime.now()) 
# as a value or convert between datetime objects and POSIX timestamps or time tuples. 
# However, no explicit time zone information is stored in the Datastore, 
# so if you are careful you can use these to represent local times in any timezone—if you use the current time or the conversions.
# https://developers.google.com/appengine/docs/python/ndb/properties#Date_and_Time

class Unit(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 19
    
    # ancestor ProductUOMCategory
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    # composite index: ancestor:no - active,name
    measurement = ndb.SuperStringProperty('1', required=True)
    name = ndb.SuperStringProperty('2', required=True)
    symbol = ndb.SuperStringProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    rate = ndb.SuperDecimalProperty('4', required=True, indexed=False)# The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12)
    factor = ndb.SuperDecimalProperty('5', required=True, indexed=False)# The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12)
    rounding = ndb.SuperDecimalProperty('6', required=True, indexed=False)# Rounding Precision - digits=(12, 12)
    digits = ndb.SuperIntegerProperty('7', required=True, indexed=False)
     
    EXPANDO_FIELDS = {
        'code' : ndb.SuperStringProperty('8', required=True, indexed=False),# ukljuciti index ako bude trebao za projection query
        'numeric_code' : ndb.SuperStringProperty('9', indexed=False),
        'grouping' : ndb.SuperStringProperty('10', required=True, indexed=False),
        'decimal_separator' : ndb.SuperStringProperty('11', required=True, indexed=False),
        'thousands_separator' : ndb.SuperStringProperty('12', indexed=False),
        'positive_sign_position' : ndb.SuperIntegerProperty('13', required=True, indexed=False),
        'negative_sign_position' : ndb.SuperIntegerProperty('14', required=True, indexed=False),
        'positive_sign' : ndb.SuperStringProperty('15', indexed=False),
        'negative_sign' : ndb.SuperStringProperty('16', indexed=False),
        'positive_currency_symbol_precedes' : ndb.SuperBooleanProperty('17', default=True, indexed=False),
        'negative_currency_symbol_precedes' : ndb.SuperBooleanProperty('18', default=True, indexed=False),
        'positive_separate_by_space' : ndb.SuperBooleanProperty('19', default=True, indexed=False),
        'negative_separate_by_space' : ndb.SuperBooleanProperty('20', default=True, indexed=False),
    }

# done!
class CategoryBalance(ndb.BaseModel):
  # LocalStructuredProperty model
  # ovaj model dozvoljava da se radi feedback trending per month per year
  # mozda bi se mogla povecati granulacija per week, tako da imamo oko 52 instance per year, ali mislim da je to nepotrebno!
  # ovde treba voditi racuna u scenarijima kao sto je napr. promena feedback-a iz negative u positive state,
  # tako da se za taj record uradi negative_feedback_count - 1 i positive_feedback_count + 1
  # najbolje je raditi update jednom dnevno, ne treba vise od toga, tako da bi mozda cron ili task queue bilo resenje za agregaciju
  from_date = ndb.SuperDateTimeProperty('1', auto_now_add=True, required=True)
  to_date = ndb.SuperDateTimeProperty('2', auto_now_add=True, required=True)
  debit = ndb.SuperDecimalProperty('3', required=True, indexed=False)# debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = ndb.SuperDecimalProperty('4', required=True, indexed=False)
  balance = ndb.SuperDecimalProperty('5', required=True, indexed=False)
  uom = ndb.SuperLocalStructuredProperty(Unit, '6', required=True)


class Category(ndb.BaseExpando):
    
  KIND_ID = 47

  # root (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L448
  # http://hg.tryton.org/modules/account/file/933f85b58a36/account.py#l525
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/account.py#l19
  # composite index: 
  # ancestor:no - active,name;
  # ancestor:no - active,code;
  # ancestor:no - active,company,name; ?
  # ancestor:no - active,company,code; ?
  parent_record = ndb.SuperKeyProperty('1', kind='47', required=True)
  name = ndb.SuperStringProperty('2', required=True)
  code = ndb.SuperStringProperty('3', required=True)
  active = ndb.SuperBooleanProperty('4', default=True)
  company = ndb.SuperKeyProperty('5', kind='app.domain.business.Company', required=True)
  complete_name = ndb.SuperTextProperty('6', required=True)# da je ovo indexable bilo bi idealno za projection query
  # Expando
  # description = ndb.TextProperty('7', required=True)# soft limit 16kb
  # balances = ndb.LocalStructuredProperty(CategoryBalance, '8', repeated=True)# soft limit 120x
  
  EXPANDO_FIELDS = {
     'description' : ndb.SuperTextProperty('7'),
     'balances' : ndb.SuperLocalStructuredProperty(CategoryBalance, '8', repeated=True)  
  }
 
  
class Group(ndb.BaseExpando):
  
  KIND_ID = 48  
    
  pass
  
  # root (namespace Domain)
  # verovatno cemo ostaviti da bude expando za svaki slucaj!
  
class Journal(ndb.BaseModel):
  
  KIND_ID = 49
  
  # root (namespace Domain)
  # key.id() = code.code
  company = ndb.SuperKeyProperty('1', kind='app.domain.business.Company', required=True)
  sequence = ndb.SuperIntegerProperty('2', required=True)
  active = ndb.SuperBooleanProperty('3', default=True)
  subscriptions = ndb.SuperStringProperty('4', repeated=True)
  code = ndb.SuperPickleProperty('5', required=True, compressed=False)
  # sequencing counter....
  
  
class Entry(ndb.BaseExpando):
    
  KIND_ID = 50
  
  # ancestor Group (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L1279
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l38
  # composite index: 
  # ancestor:no - journal,company,state,date:desc;
  # ancestor:no - journal,company,state,created:desc;
  # ancestor:no - journal,company,state,updated:desc;
  # ancestor:no - journal,company,state,party,date:desc; ?
  # ancestor:no - journal,company,state,party,created:desc; ?
  # ancestor:no - journal,company,state,party,updated:desc; ?
  name = ndb.SuperStringProperty('1', required=True)
  journal = ndb.SuperKeyProperty('2', kind=Journal, required=True)
  company = ndb.SuperKeyProperty('3', kind='app.domain.business.Company', required=True)
  state = ndb.SuperIntegerProperty('4', required=True)
  date = ndb.SuperDateTimeProperty('5', required=True)# updated on specific state or manually
  created = ndb.SuperDateTimeProperty('6', auto_now_add=True, required=True)
  updated = ndb.SuperDateTimeProperty('7', auto_now=True, required=True)
  # Expando
  # 
  # party = ndb.KeyProperty('8') mozda ovaj field vratimo u Model ukoliko query sa expando ne bude zadovoljavao performanse
  # expando indexi se programski ukljucuju ili gase po potrebi

  EXPANDO_FIELDS = {
     'party' : ndb.SuperKeyProperty('8'),
  }
  
class Line(ndb.BaseExpando):
  
  KIND_ID = 51  
  
  # ancestor Entry (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_move_line.py#L432
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_analytic_line.py#L29
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l486
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/line.py#l14
  # uvek se prvo sekvencionisu linije koje imaju debit>0 a onda iza njih slede linije koje imaju credit>0
  # u slucaju da je Entry balanced=True, zbir svih debit vrednosti u linijama mora biti jednak zbiru credit vrednosti
  # composite index: 
  # ancestor:yes - sequence;
  # ancestor:no - journal, company, state, categories, uom, date
  journal = ndb.SuperKeyProperty('1', kind=Journal, required=True)
  company = ndb.SuperKeyProperty('2', kind='app.domain.business.Company', required=True)
  state = ndb.SuperIntegerProperty('3', required=True)
  date = ndb.SuperDateTimeProperty('4', required=True)# updated on specific state or manually
  sequence = ndb.SuperIntegerProperty('5', required=True)
  categories = ndb.SuperKeyProperty('6', kind=Category, repeated=True) # ? mozda staviti samo jednu kategoriju i onda u expando prosirivati
  debit = ndb.SuperDecimalProperty('7', required=True, indexed=False)# debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = ndb.SuperDecimalProperty('8', required=True, indexed=False)# credit=0 u slucaju da je debit>0, negativne vrednosti su zabranjene
  uom = ndb.SuperLocalStructuredProperty(Unit, '9', required=True)
  # Expando
  # neki upiti na Line zahtevaju "join" sa Entry poljima
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopiranjem polja iz Entry-ja u Line-ove




  
class Bot(ndb.BaseModel):
  
  KIND_ID = 52
  
  # ancestor Journal (namespace Domain)
  # composite index: ancestor:yes - sequence
  sequence = ndb.SuperIntegerProperty('1', required=True)
  active = ndb.SuperBooleanProperty('2', default=True)
  subscriptions = ndb.SuperStringProperty('3', repeated=True)
  code = ndb.SuperPickleProperty('4', required=True, compressed=False)

  