# -*- coding: utf-8 -*-
'''
Created on Aug 25, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime
import collections
import re
import copy

from app import orm
from app.tools.base import *
from app.util import *
from app.models import location, uom, transaction, order  # rule, log


class PluginError(Exception):
  
  def __init__(self, plugin_error):
    self.message = plugin_error


# This is system plugin, which means end user can not use it!
class CartInit(orm.BaseModel):
  
  _kind = 99
  
  _use_rule_engine = False
  
  def run(self, context):
    Group = context.models['48']
    Entry = context.models['50']
    entry_fields = context.model.get_fields()
    entry = Entry.query(entry_fields['journal'] == context.model.journal,
                        entry_fields['party'] == context.user.key,
                        entry_fields['state'].IN(['cart', 'checkout', 'processing']),
                        namespace=context.model.journal._namespace).get()  # we will need composite index for this
    if entry is None:
      context._group = Group(namespace=context.model.journal._namespace)
      entry = Entry(namespace=context.model.journal._namespace, journal=context.model.journal)
      # entry.company_address = # Source of company address required!
      entry.state = 'cart'
      entry.date = datetime.datetime.now()
      entry.party = context.user.key
    else:
      entry.read({'_lines' : {'config' : {'limit': -1}}})  # @todo It is possible that we will have to read more stuff here.
      context._group = entry.parent_entity
    context._group.insert_entry(entry)
    if entry.state != 'cart':
      raise PluginError('entry_not_in_cart_state')


# This is system plugin, which means end user can not use it!
class LinesInit(orm.BaseModel):
  
  _kind = 100
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    if len(entry._lines) == 0:
      Category = context.models['47']
      Line = context.models['51']
      receivable_line = Line(sequence=0, uom=copy.deepcopy(entry.currency), description='Accounts Receivable',
                             debit=format_value('0', entry.currency), credit=format_value('0', entry.currency),
                             categories=[Category.build_key('1102', namespace=context.model.journal._namespace)])  # Debtors (1102) account.
      tax_line = Line(sequence=1, uom=copy.deepcopy(entry.currency), description='Sales Tax',
                      debit=format_value('0', entry.currency), credit=format_value('0', entry.currency),
                      categories=[Category.build_key('121', namespace=context.model.journal._namespace)])  # Tax Received (121) account.
      entry._lines = [receivable_line, tax_line]


# This is system plugin, which means end user can not use it!
class ProductToLine(orm.BaseModel):
  
  _kind = 101
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    product_key = context.input.get('product')
    variant_signature = context.input.get('variant_signature')
    line_exists = False
    for line in entry._lines:
      if hasattr(line, 'product_reference') and line.product_reference == product_key \
      and line.product_variant_signature == variant_signature:
        line._state = 'modified'  # @todo Not sure if this is ok!?
        line.quantity = line.quantity + format_value('1', line.product_uom)
        line_exists = True
        break
    if not line_exists:
      ProductInstance = context.models['39']
      Category = context.models['47']
      Line = context.models['51']
      product = product_key.get()
      product.read({'_product_category': {}})  # more fields probably need to be specified
      product_instance_key = ProductInstance.prepare_key(context.input, parent=product_key)
      product_instance = product_instance_key.get()
      new_line = Line(journal=context.model.journal)  # i generally dont like this
      new_line.sequence = entry._lines[-1].sequence + 1
      new_line.categories = [Category.build_key('200', namespace=context.model.journal._namespace)]  # Product Sales (200) account.
      new_line.uom = copy.deepcopy(entry.currency)
      new_line.product_reference = product_key
      new_line.product_variant_signature = variant_signature
      new_line.product_category_complete_name = product._product_category.complete_name
      new_line.product_category_reference = product.product_category
      new_line.description = product.name
      new_line.code = product.code
      new_line.unit_price = product.unit_price
      new_line.product_uom = product.product_uom.get().get_uom()
      new_line.quantity = format_value('1', new_line.product_uom)
      new_line.discount = format_value('0', uom.UOM(digits=4))
      if hasattr(product, 'weight'):
        new_line._weight = product.weight  # @todo Perhaps we might need to build these fields during certain actions, and not only while adding new lines (to ensure thir life accros carrier plugins)!
        new_line._weight_uom = product.weight_uom
      if hasattr(product, 'volume'):
        new_line._volume = product.volume
        new_line._volume_uom = product.volume_uom
      if product_instance is not None:
        if hasattr(product_instance, 'unit_price'):
          new_line.unit_price = product_instance.unit_price
        if hasattr(product_instance, 'code'):
          new_line.code = product_instance.code
        if hasattr(product_instance, 'weight'):
          new_line._weight = product_instance.weight
          new_line._weight_uom = product_instance.weight_uom
        if hasattr(product_instance, 'volume'):
          new_line._volume = product_instance.volume
          new_line._volume_uom = product_instance.volume_uom
      entry._lines.append(new_line)


# This is system plugin, which means end user can not use it!
# @todo Not sure if need this plugin, since we have field level rule engine, which would be capable of controling which field can be edited!?
class UpdateProductLine(orm.BaseModel):
  
  _kind = 102
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    delete_lines = []
    # @todo It is likely that here we will receive whole lines in input, not just 'quantity' or whatever, so we have to figure how to do formating on values that are set on prop.
    # @answer point is that something will have to do the computations bellow
    quantity = context.input.get('quantity')
    discount = context.input.get('discount')
    for i, line in enumerate(entry._lines):
      if hasattr(line, 'product_reference'):
        if quantity is not None:
          if quantity[i] <= 0:
            line._state = 'deleted'
          else:
            line.quantity = format_value(quantity[i], line.product_uom)
        if discount is not None:
          line.discount = format_value(discount[i], uom.UOM(digits=4))


# This is system plugin, which means end user can not use it!
class EntryFieldAutoUpdate(orm.BaseModel):
  
  _kind = 103
  
  _use_rule_engine = False
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    remove_values = self.cfg.get('rm', [])
    entry = context._group.get_entry(context.model.journal)
    for key, value in static_values.iteritems():
      set_attr(entry, key, value)
    for key, value in dynamic_values.iteritems():
      set_value = get_attr(context, value, Nonexistent)
      if set_value is not Nonexistent:
        set_attr(entry, key, set_value)
    for key in remove_values:
      del_attr(entry, key)


# This is system plugin, which means end user can not use it!
class ProductSubtotalCalculate(orm.BaseModel):
  
  _kind = 104
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    for line in entry._lines:
      if hasattr(line, 'product_reference'):
        line.subtotal = format_value((line.unit_price * line.quantity), line.uom)
        line.discount_subtotal = format_value((line.subtotal - (line.subtotal * line.discount)), line.uom)
        line.debit = format_value('0', line.uom)
        line.credit = format_value(line.discount_subtotal, line.uom)


# This is system plugin, which means end user can not use it!
class OrderTotalCalculate(orm.BaseModel):
  
  _kind = 105
  
  _use_rule_engine = False
  
  # @todo We need receivable calcualtior as well!
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    untaxed_amount = format_value('0', entry.currency)
    tax_amount = format_value('0', entry.currency)
    total_amount = format_value('0', entry.currency)
    for line in entry._lines:
      if hasattr(line, 'product_reference'):
        untaxed_amount += line.subtotal
        tax_amount += line.tax_subtotal
        total_amount += line.subtotal + line.tax_subtotal
    entry.untaxed_amount = format_value(untaxed_amount, entry.currency)
    entry.tax_amount = format_value(tax_amount, entry.currency)
    entry.total_amount = format_value(total_amount, entry.currency)


# Not a plugin!
class Location(orm.BaseModel):
  
  _kind = 106
  
  _use_rule_engine = False
  
  country = orm.SuperKeyProperty('1', kind='15', required=True, indexed=False)
  region = orm.SuperKeyProperty('2', kind='16', indexed=False)
  postal_code_from = orm.SuperStringProperty('3', indexed=False)
  postal_code_to = orm.SuperStringProperty('4', indexed=False)
  city = orm.SuperStringProperty('5', indexed=False)


class AddressRule(orm.BaseModel):
  
  _kind = 107
  
  _use_rule_engine = False
  
  exclusion = orm.SuperBooleanProperty('1', required=True, default=False, indexed=False)
  address_type = orm.SuperStringProperty('2', required=True, default='billing', choices=['billing', 'shipping'], indexed=False)
  locations = orm.SuperLocalStructuredProperty(Location, '3', repeated=True, indexed=False)
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    valid_addresses = collections.OrderedDict()
    default_address = None
    address_reference_key = '%s_address_reference' % self.address_type
    address_key = '%s_address' % self.address_type
    addresses_key = '%s_addresses' % self.address_type
    default_address_key = 'default_%s' % self.address_type
    input_address_reference = context.input.get(address_reference_key)
    entry_address_reference = getattr(entry, address_reference_key, None)
    buyer_addresses = orm.Key('77', entry.partner._id_str, parent=entry.partner).get()
    if buyer_addresses is None:
      raise PluginError('no_address')
    for buyer_address in buyer_addresses.addresses:
      if self.validate_address(buyer_address):
        valid_addresses[buyer_address.key] = buyer_address
        if getattr(buyer_address, default_address_key):
          default_address = buyer_address
    if not len(valid_addresses):
      raise PluginError('no_valid_address')
    context.output[addresses_key] = valid_addresses
    if (default_address is None) and len(valid_addresses):
      default_address = valid_addresses.values()[0]
    if input_address_reference in valid_addresses:
      default_address = valid_addresses[input_address_reference]
    elif entry_address_reference in valid_addresses:
      default_address = valid_addresses[entry_address_reference]
    if default_address:
      setattr(entry, address_reference_key, default_address.key)
      setattr(entry, address_key, location.get_location(default_address))
      context.output[default_address_key] = default_address
    else:
      raise PluginError('no_address_found')
  
  def validate_address(self, address):
    if self.exclusion:
      # Shipping only at the following locations.
      allowed = False
    else:
      # Shipping everywhere except at the following locations.
      allowed = True
    for loc in self.locations:
      if not (loc.region and loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country):
          allowed = self.exclusion
          break
      elif not (loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region):
          allowed = self.exclusion
          break
      elif not (loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
          allowed = self.exclusion
          break
      else:
        if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
          allowed = self.exclusion
          break
    return allowed


# This plugin is incomplete!
class PayPalPayment(orm.BaseModel):
  
  _kind = 108
  
  _use_rule_engine = False
  
  # This plugin will be subscribed to many actions, among which is add_to_cart as well.
  # PayPal Shipping: Prompt for an address, but do not require one,
  # PayPal Shipping: Do not prompt for an address
  # PayPal Shipping: Prompt for an address, and require one
  
  currency = orm.SuperKeyProperty('1', kind=uom.Unit, required=True, indexed=False)
  reciever_email = orm.SuperStringProperty('2', required=True, indexed=False)
  business = orm.SuperStringProperty('3', required=True, indexed=False)
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    # In context of add_to_cart action runner does the following:
    entry.currency = self.currency.get().get_uom()
    entry.paypal_reciever_email = self.reciever_email
    entry.paypal_business = self.business


# This plugin is incomplete!
class Tax(orm.BaseModel):
  
  _kind = 109
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  code = orm.SuperStringProperty('2', required=True, indexed=False)  # @todo Not sure if we need this!
  formula = orm.SuperPickleProperty('3', required=True, indexed=False)  # @todo Formula has to be defined as touple (type, amount) (e.g. ('%', 15))! Or we can make it something different!
  # formula needs to be pickle property, because we completely need to avoid using regex
  # or we can use custom property for it, even better.
  exclusion = orm.SuperBooleanProperty('4', required=True, default=False, indexed=False)
  address_type = orm.SuperStringProperty('5', required=True, default='billing', choices=['billing', 'shipping'], indexed=False)
  locations = orm.SuperLocalStructuredProperty(Location, '6', repeated=True)
  carriers = orm.SuperKeyProperty('7', repeated=True, indexed=False)  # this is now possible since struct props have keys and can be identified.
  product_categories = orm.SuperKeyProperty('8', kind='17', repeated=True, indexed=False)
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    allowed = self.validate_tax(entry)
    for line in entry._lines:
      for tax in line.taxes:
        if tax.key == self.key:
          tax._state = 'deleted'
      if (self.carriers and self.carriers.count(line.carrier_reference)) \
      or (self.product_categories and self.product_categories.count(line.product_category)):  # @todo Have to check if all lines have carrier_reference property??
        if allowed:
          tax_exists = False
          for tax in line.taxes:
            if tax.key == self.key:
              tax.name = self.name
              tax.code = self.code
              tax.formula = self.formula
              tax_exists = True
              break
          if not tax_exists:
            line.taxes.append(order.LineTax(key=self.key, name=self.name, code=self.code, formula=self.formula))
  
  def validate_tax(self, entry):
    address = None
    address_reference_key = '%s_address_reference' % self.address_type
    entry_address_reference = getattr(entry, address_reference_key, None)
    if entry_address_reference is None:  # @todo Is this ok??
      return False
    buyer_addresses = orm.Key('77', entry.partner._id_str, parent=entry.partner).get()
    for buyer_address in buyer_addresses.addresses:
      if buyer_address.key == entry_address_reference:
        address = buyer_address
        break
    if address is None:  # @todo IS this ok??
      return False
    if self.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    for loc in self.locations:
      if not (loc.region and loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country):
          allowed = self.exclusion
          break
      elif not (loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region):
          allowed = self.exclusion
          break
      elif not (loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
          allowed = self.exclusion
          break
      else:
        if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
          allowed = self.exclusion
          break
    # @todo This block need changes!
    if allowed:
      # If tax is configured for carriers then check if the entry references carrier on which the tax applies.
      if self.carriers:
        allowed = False
        if entry.carrier_reference and self.carrieres.count(entry.carrier_reference):
          allowed = True
      # If tax is configured for product categories, then check if the entry contains a line which has product category to which the tax applies.
      elif self.product_categories:
        allowed = False
        for line in entry._lines:
          if self.product_categories.count(line.product_category):
            allowed = True
            break
    return allowed


# This is system plugin, which means end user can not use it!
class TaxSubtotalCalculate(orm.BaseModel):
  
  _kind = 110
  
  _use_rule_engine = False
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    Category = context.models['47']
    Line = context.models['51']
    tax_category_key = Category.build_key('121', namespace=context.model.journal._namespace)  # Tax Received (121) account.
    tax_line = False
    tax_total = format_value('0', entry.currency)
    for line in entry._lines:
      if tax_category_key in line.categories:
        tax_line = line
      tax_subtotal = format_value('0', line.uom)
      for tax_key, tax in line.taxes.items():
        if (tax.formula[0] == 'percent'):
          tax_amount = format_value(tax.formula[1], line.uom) * format_value('0.01', line.uom)  # or "/ DecTools.form('100')"
          tax_subtotal += line.credit * tax_amount
          tax_total += line.credit * tax_amount
        elif (tax.formula[0] == 'amount'):
          tax_amount = format_value(tax.formula[1], line.uom)
          tax_subtotal += tax_amount
          tax_total += tax_amount
      line.tax_subtotal = tax_subtotal
    if tax_line:  # @todo Or we can loop entry._lines again and do the math!
      tax_line.debit = format_value('0', tax_line.uom)
      tax_line.credit = tax_total


# Not a plugin!
class CarrierLineRule(orm.BaseModel):
  
  _kind = 111
  
  _use_rule_engine = False
  
  condition = orm.SuperStringProperty('1', required=True, indexed=False)
  price = orm.SuperStringProperty('2', required=True, indexed=False)


# Not a plugin!
class CarrierLine(orm.BaseModel):
  
  _kind = 112
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  active = orm.SuperBooleanProperty('2', required=True, default=True)
  exclusion = orm.SuperBooleanProperty('3', required=True, default=False)
  locations = orm.SuperLocalStructuredProperty(Location, '4', repeated=True)
  rules = orm.SuperLocalStructuredProperty(CarrierLineRule, '5', repeated=True)


# This plugin is incomplete!
class Carrier(orm.BaseModel):
  
  _kind = 113
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  lines = orm.SuperLocalStructuredProperty(CarrierLine, '2', repeated=True)
  
  def run(self, context):
    entry = context._group.get_entry(context.model.journal)
    valid_lines = []
    for carrier_line in self.lines:
      if self.validate_line(carrier_line, entry):
        valid_lines.append(carrier_line)
    carrier_price = self.calculate_lines(valid_lines, entry)
    if 'carriers' not in context.output:
      context.output['carriers'] = []
    context.output['carriers'].append({'name': self.name,
                                       'price': carrier_price,
                                       'id': self.key.urlsafe()})
  
  def calculate_lines(self, valid_lines, entry):
    weight_uom = uom.Unit.build_key('kilogram').get()
    volume_uom = uom.Unit.build_key('cubic_meter').get()
    weight = format_value('0', weight_uom)
    volume = format_value('0', volume_uom)
    for line in entry._lines:
      line_weight = line._weight
      line_weight_uom = line._weight_uom.get()
      line_volume = line._volume
      line_volume_uom = line._volume_uom.get()
      weight += convert_value(line_weight, line_weight_uom, weight_uom)
      volume += convert_value(line_volume, line_volume_uom, volume_uom)
      carrier_prices = []
      for carrier_line in valid_lines:
        line_prices = []
        for rule in carrier_line.rules:
          condition = rule.condition
          condition = self.format_value(condition)  # @todo this regex needs to go out of here
          price = rule.price
          if safe_eval(condition, {'weight': weight, 'volume': volume, 'price': price}):
            price = self.format_value(price)
            price = safe_eval(price, {'weight': weight, 'volume': volume, 'price': price})
            line_prices.append(price)
        carrier_prices.append(min(line_prices))
      return min(carrier_prices)  # Return the lowest price possible of all lines!
  
  def format_value(self, value):
    def run_format(match):
      matches = match.groups()
      return 'Decimal("%s")' % format_value(matches[0], uom.get_uom(ndb.Key(urlsafe=matches[1])))  # @todo To correct!
      # this regex needs more work
    value = re.sub('\((.*)\,(.*)\)', run_format, value)
    return value
  
  def validate_line(self, carrier_line, entry):
    address = None
    entry_address_reference = getattr(entry, 'shipping_address_reference', None)
    if entry_address_reference is None:  # @todo Is this ok??
      return False
    buyer_addresses = orm.Key('77', entry.partner._id_str, parent=entry.partner).get()
    for buyer_address in buyer_addresses.addresses:
      if buyer_address.internal_id == entry_address_reference:
        address = buyer_address
        break
    if address is None:  # @todo IS this ok??
      return False
    if carrier_line.exclusion:
      # Apply only at the following locations.
      allowed = False
    else:
      # Apply everywhere except at the following locations.
      allowed = True
    for loc in carrier_line.locations:
      if not (loc.region and loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country):
          allowed = carrier_line.exclusion
          break
      elif not (loc.postal_code_from and loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region):
          allowed = carrier_line.exclusion
          break
      elif not (loc.postal_code_to):
        if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
          allowed = carrier_line.exclusion
          break
      else:
        if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
          allowed = carrier_line.exclusion
          break
    if allowed:
      allowed = False
      price = entry.amount_total
      weight_uom = uom.get_uom(uom.Unit.build_key('kg', parent=uom.Measurement.build_key('metric')))  # @todo To correct!
      volume_uom = uom.get_uom(uom.Unit.build_key('m3', parent=uom.Measurement.build_key('metric')))  # @todo To correct!
      weight = format_value('0', weight_uom)
      volume = format_value('0', volume_uom)
      for line in entry._lines:
        line_weight = line._weight[0]
        line_weight_uom = uom.get_uom(ndb.Key(urlsafe=line._weight[1]))  # @todo To correct!
        line_volume = line._volume[0]
        line_volume_uom = uom.get_uom(ndb.Key(urlsafe=line._volume[1]))  # @todo To correct!
        weight += uom.convert_value(line_weight, line_weight_uom, weight_uom)
        volume += uom.convert_value(line_volume, line_volume_uom, volume_uom)
      for rule in carrier_line.rules:
        condition = rule.condition
        condition = self.format_value(condition)
        if safe_eval(condition, {'weight': weight, 'volume': volume, 'price': price}):
          allowed = True
          break
    return allowed


# @todo This will be eventually improved.
# This is system plugin, which means end user can not use it!
class TransactionWrite(orm.BaseModel):
  
  _kind = 114
  
  def run(self, context):
    context._group.write()
    for entry in context._group._entries:
      entry.set_key(None, parent=context._group.key)
    orm.write_multi(context._group._entries)


# This is system plugin, which means end user can not use it!
class CallbackNotify(orm.BaseModel):
  
  _kind = 115
  
  def run(self, context):
    static_data = {}
    entry = context._group.get_entry(context.model.journal)
    static_data.update({'caller_entity': entry.key_urlsafe,
                        'action_id': 'initiate',
                        'action_model': '61'})
    context._callbacks.append(('notify', static_data))

# OLD CODE #


class PayPalInit(orm.BaseModel):
  
  # user plugin, saved in datastore
  
  def run(self, journal, context):
    
    ipns = log.Record.query(ndb.GenericProperty('ipn_txn_id') == context.input['txn_id']).fetch()
    if len(ipns):
      for ipn in ipns:
        if (ipn.payment_status == context.input['payment_status']):
          raise PluginValidationError('duplicate_entry')
      entry = ipns[0].parent_entity
      if context.input['custom']:
         if (entry.key.urlsafe() == context.input['custom']):
           
            kwds = {'log_entity' : False}
            kwds.update(dict([('ipn_%s' % key, value) for key,value in context.input.items()])) # prefix
            context.log.entities.append((entry, kwds))
            
         else:
            raise PluginValidationError('invalid_ipn')
      else:
        raise PluginValidationError('invalid_ipn')
      
    else:    
      
      if not context.input['custom']:
        raise PluginValidationError('invalid_ipn')
      else:
        try:
          entry_key = ndb.Key(urlsafe=context.input['custom']) 
          entry = entry_key.get()
        except Exception as e:
          raise PluginValidationError('invalid_ipn')
        
    if not entry:
      raise PluginValidationError('invalid_ipn')
    
    kwds = {'log_entity' : False}
    kwds.update(dict([('ipn_%s' % key, value) for key,value in context.input.items()])) # prefix
    context.log.entities.append((entry, kwds))
    
    if not context.transaction.group:
       context.transaction.group = entry.parent_entity
       
    context.transaction.entities[journal.key.id()] = entry
    
    if not self.validate_entry(entry, context):
       raise PluginValidationError('fraud_check')
     
    if (entry.paypal_payment_status == context.input['payment_status']):
        return None
      
    update_paypal_payment_status = False  
      
    if (entry.paypal_payment_status == 'Pending'):
        if (context.input['payment_status'] == 'Completed' or context.input == 'Denied'):
            update_paypal_payment_status = True
    elif (entry.paypal_payment_status == 'Completed'):
        if (context.input['payment_status'] == 'Refunded' or context.input['payment_status'] == 'Reversed'):
            update_paypal_payment_status = True
            
    if (update_paypal_payment_status):
        # ovo se verovatno treba jos doterati..
        if (entry.state == 'processing' and context.input['payment_status'] == 'Completed'):
            entry.state = 'completed'
            entry.paypal_payment_status = context.input['payment_status']
            context.log.entities.append((entry,))
        elif (entry.state == 'processing' and context.input['payment_status'] == 'Denied'): # ovo cemo jos da razmotrimo
            entry.state = 'canceled'
            entry.paypal_payment_status = context.input['payment_status']
            context.log.entities.append((entry,))
        elif (entry.state == 'completed'):
            entry.paypal_payment_status = context.input['payment_status']
            context.log.entities.append((entry,))
    
  def validate_entry(self, entry, context):
      
      mismatches = []
      ipn = context.input
      shipping_address = entry.shipping_address
 
      if (entry.paypal_receiver_email != ipn['receiver_email']):
          mismatches.append('receiver_email')
      if (entry.paypal_business != ipn['business']):
          mismatches.append('business_email')
      if (entry.currency.code != ipn['mc_currency']):
          mismatches.append('mc_currency')
      if (entry.total_amount != uom.format_value(ipn['mc_gross'], entry.currency)):
          mismatches.append('mc_gross')
      if (entry.tax_amount != uom.format_value(ipn['tax'], entry.currency)):
          mismatches.append('tax')
          
      if (entry.name != ipn['invoice']): # entry.reference bi mozda mogao da bude user.key.id-entry.key.id ili mozda entry.key.id ?
          mismatches.append('invoice')
      
      if (shipping_address.country != ipn['address_country']):
          mismatches.append('address_country')    
      if (shipping_address.country_code != ipn['address_country_code']):
          mismatches.append('address_country_code')
      if (shipping_address.city != ipn['address_city']):
          mismatches.append('address_city')
      if (shipping_address.name != ipn['address_name']):
          mismatches.append('address_name')
      
      state = shipping_address.region # po defaultu sve ostale drzave koriste name? ili i one isto kod?
      if shipping_address.country_code == 'US': # paypal za ameriku koristi 2 digit iso standard kodove za njegove stateove
         state = shipping_address.region_code
         
      if (state != ipn['address_state']):
          mismatches.append('address_state')
      if (shipping_address.street != ipn['address_street']): 
          # PayPal spaja vrednosti koje su prosledjene u cart upload procesu (address1 i address2), 
          # tako da u povratu putem IPN-a, polje address_street izgleda ovako address1\r\naddress2. 
          # Primer: u'address_street': [u'1 Edi St\r\nApartment 7'], gde je vrednost Street Address 
          # od kupca bilo "Edi St", a vrednost Street Address (Optional) "Apartment 7".
          mismatches.append('address_street')
      if (shipping_address.postal_code != ipn['address_zip']):
          mismatches.append('address_zip')
          
      for line in entry._lines:
          if (line.code != ipn['item_number%s' % str(line.sequence)]): # ovo nije u order funkcijama implementirano tako da ne znamo da li cemo to imati..
              mismatches.append('item_number%s' % str(line.sequence))
          if (line.description != ipn['item_name%s' % str(line.sequence)]):
              mismatches.append('item_name%s' % str(line.sequence))
          if (line.quantity != uom.format_value(ipn['quantity%s' % str(line.sequence)], line.product_uom)):
              mismatches.append('quantity%s' % str(line.sequence))
          if ((line.subtotal + line.tax_subtotal) != uom.format_value(ipn['mc_gross%s' % str(line.sequence)], entry.currency)):
              mismatches.append('mc_gross%s' % str(line.sequence))
      # Ukoliko je doslo do fail-ova u poredjenjima
      # radi se dispatch na notification engine sa detaljima sta se dogodilo, radi se logging i algoritam se prekida.
      if not mismatches:
         return True
      else:
         return False
