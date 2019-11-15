from django.template import Library

register = Library()

# https://bitbucket.org/btingle/mets-support/src/6b73cd630a5088f28d983e5ef765f673a860b54c/xslt/view/common/scaleImage.xsl?at=default&fileviewer=file-view-default
@register.filter
def clip_width(dimensions, clip):
    x, y = get_dimensions(dimensions, ':')
    ratio = get_ratio(x, y)
 
    max_x, max_y = get_dimensions(clip, 'x')
    max_ratio = get_ratio(max_x, max_y)

    if (x > max_x) or (y > max_y):
        if ratio > max_ratio: # landscape, x leads
            return max_x
        elif ratio < max_ratio: # portrait, y leads; x is scaled
            return round(max_y * ratio)
        elif ratio == max_ratio: # it's a square
            return max_x
    elif x:
        return x
    else:
        return max_x

@register.filter
def clip_height(dimensions, clip):
    x, y = get_dimensions(dimensions, ':')
    ratio = get_ratio(x, y)

    max_x, max_y = get_dimensions(clip, 'x')
    max_ratio = get_ratio(max_x, max_y)

    if (x > max_x) or (y > max_y):
        if ratio > max_ratio: # landscape, x leads; y is scaled
            return round(max_x / ratio)
        elif ratio < max_ratio: # portrait, y leads
            return max_y
        elif ratio == max_ratio: # it's a square
            return max_x
    elif y:
        return y
    else:
        return max_y


def get_dimensions(text, delimiter):
    dimensions = [int(dimension.strip()) for dimension in text.split(delimiter)]
    x = dimensions[0]
    y = dimensions[1] 
    return x, y

def get_ratio(x, y):
    return float(x) / float(y)

@register.filter
def is_string(val):
    return isinstance(val, str)

@register.filter
def pjax_available(template_names, request):
    try: 
        from easy_pjax.templatetags.pjax_tags import pjax
    except ImportError:
        template_name = template_names.split(",",1)[0]
        return template_name.strip()
    else: 
        return pjax(template_names, request)
