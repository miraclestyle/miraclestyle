# -*- coding: utf-8 -*-
'''
Created on Apr 24, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import dis
from decimal import Decimal, ROUND_HALF_EVEN


def prepare_attr(entity, field_path):
  fields = str(field_path).split('.')
  last_field = fields[-1]
  drill = fields[:-1]
  i = -1
  while not last_field:
    i = i - 1
    last_field = fields[i]
    drill = fields[:i]
  for field in drill:
    if field:
      if isinstance(entity, dict):
        try:
          entity = entity[field]
        except KeyError as e:
          return None
      elif isinstance(entity, list):
        try:
          entity = entity[int(field)]
        except IndexError as e:
          return None
      else:
        try:
          entity = getattr(entity, field)
        except ValueError as e:
          return None
  return (entity, last_field)


def set_attr(entity, field_path, value):
  result = prepare_attr(entity, field_path)
  if result == None:
    return None
  entity, last_field = result
  if isinstance(entity, dict):
    entity[last_field] = value
  elif isinstance(entity, list):
    try:
      entity[int(last_field)] = value
    except:
      return None
  else:
    setattr(entity, last_field, value)


def get_attr(entity, field_path, default_value=None):
  result = prepare_attr(entity, field_path)
  if result == None:
    return default_value
  entity, last_field = result
  if isinstance(entity, dict):
    return entity.get(last_field, default_value)
  elif isinstance(entity, list):
    try:
      return entity[int(last_field)]
    except:
      return default_value
  else:
    return getattr(entity, last_field, default_value)


def get_meta(entity, field_path):
  result = prepare_attr(entity, field_path)
  if result == None:
    return None
  entity, last_field = result
  if not isinstance(entity, dict) and not isinstance(entity, list):
    return getattr(entity.__class__, last_field)


def normalize(source):
  if isinstance(source, list):
    return source
  if isinstance(source, tuple):
    return list(source)
  if isinstance(source, basestring):
    return [source]
  if isinstance(source, dict):
    return [item for key, item in source.items()]
  try:
    items = iter(source)
    return [item for item in items]
  except ValueError as e:
    pass
  finally:
    return [source]


def sort_by_list(unsorted_list, sorting_list, field):
  total = len(unsorted_list) + 1
  to_delete = []
  def sorting_function(item):
    try:
      ii = sorting_list.index(get_attr(item, field)) + 1
    except ValueError as e:
      to_delete.append(item)
      ii = total
    return ii
  return (sorted(unsorted_list, key=sorting_function), to_delete)


_CODES = ['POP_TOP', 'ROT_TWO', 'ROT_THREE', 'ROT_FOUR', 'DUP_TOP', 'BUILD_LIST',
          'BUILD_MAP', 'BUILD_TUPLE', 'LOAD_CONST', 'RETURN_VALUE',
          'STORE_SUBSCR', 'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT',
          'UNARY_INVERT', 'BINARY_POWER', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
          'BINARY_FLOOR_DIVIDE', 'BINARY_TRUE_DIVIDE', 'BINARY_MODULO',
          'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
          'BINARY_AND', 'BINARY_XOR', 'BINARY_OR', 'STORE_MAP', 'LOAD_NAME',
          'COMPARE_OP', 'LOAD_ATTR', 'STORE_NAME', 'GET_ITER',
          'FOR_ITER', 'LIST_APPEND', 'JUMP_ABSOLUTE', 'DELETE_NAME',
          'JUMP_IF_TRUE', 'JUMP_IF_FALSE', 'JUMP_IF_FALSE_OR_POP',
          'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
          'BINARY_SUBSCR', 'JUMP_FORWARD']


_ALLOWED_CODES = set(dis.opmap[x] for x in _CODES if x in dis.opmap)


def _compile_source(source):
  comp = compile(source, '', 'eval')
  codes = []
  co_code = comp.co_code
  i = 0
  while i < len(co_code):
    code = ord(co_code[i])
    codes.append(code)
    if code >= dis.HAVE_ARGUMENT:
      i += 3
    else:
      i += 1
  for code in codes:
    if code not in _ALLOWED_CODES:
      raise ValueError('opcode %s not allowed' % dis.opname[code])
  return comp


def safe_eval(source, data=None):
  if '__subclasses__' in source:
    raise ValueError('__subclasses__ not allowed')
  comp = _compile_source(source)
  try:
    return eval(comp, {'__builtins__': {'True': True, 'False': False, 'str': str,
                                        'globals': locals, 'locals': locals, 'bool': bool,
                                        'dict': dict, 'round': round, 'Decimal': Decimal}}, data)
  except Exception as e:
    raise Exception('Failed to process code "%s" error: %s' % ((source, data), e))


########## Unit manipulation functions! ##########


def convert_value(value, value_uom, conversion_uom):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(value_uom, 'measurement'):
    raise Exception('no_measurement_in_value_uom')
  if not hasattr(conversion_uom, 'measurement'):
    raise Exception('no_measurement_in_conversion_uom')
  if not hasattr(value_uom, 'rate') or not isinstance(value_uom.rate, Decimal):
    raise Exception('no_rate_in_value_uom')
  if not hasattr(conversion_uom, 'rate') or not isinstance(conversion_uom.rate, Decimal):
    raise Exception('no_rate_in_conversion_uom')
  if (value_uom.measurement == conversion_uom.measurement):
    return (value / value_uom.rate) * conversion_uom.rate
  else:
    raise Exception('incompatible_units')


def round_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'rounding') or not isinstance(uom.rounding, Decimal):
    raise Exception('no_rounding_in_uom')
  return (value / uom.rounding).quantize(Decimal('1.'), rounding=rounding) * uom.rounding


def format_value(value, uom, rounding=ROUND_HALF_EVEN):
  if not isinstance(value, Decimal):
    value = Decimal(value)
  if not hasattr(uom, 'digits') or not isinstance(uom.digits, (int, long)):
    raise Exception('no_digits_in_uom')
  places = Decimal(10) ** -uom.digits
  return (value).quantize(places, rounding=rounding)
