from django.template import Library
import ast

register = Library()


@register.filter
def get_range(value):
    """
    Filter - returns a list containing range made from given value
    Usage (in template):

    <ul>{% for i in 3|get_range %}
      <li>{{ i }}. Do something</li>
    {% endfor %}</ul>

    Results with the HTML:
    <ul>
      <li>0. Do something</li>
      <li>1. Do something</li>
      <li>2. Do something</li>
    </ul>

    Instead of 3 one may use the variable set in the views

    https://djangosnippets.org/snippets/1357/
  """
    return range(value)


@register.filter
def string_lookup(s, key):
    return ast.literal_eval(s)[key]


@register.filter
def dictionary_length(dictionary):
    length = 0
    for key in dictionary:
        length = length + len(dictionary[key])
    return length


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def multiply(a, b):
    return str(int(a) * int(b))


@register.filter
def subtract(a, b):
    return int(a) - int(b)


@register.filter
def divide(a, b):
    return int(int(a) / int(b))


@register.filter
def current_page(start, rows):
    return int(int(start) / int(rows)) + 1


@register.filter
def is_string(val):
    return isinstance(val, basestring)
