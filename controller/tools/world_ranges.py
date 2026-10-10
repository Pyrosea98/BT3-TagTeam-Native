"""Convert configured 1x-map distances to effective guest world units."""
def map_scale(settings):
    return 2.0 if settings.get('expanded_maps', False) else 1.0


def effective(settings, key):
    return float(settings[key])*map_scale(settings)
