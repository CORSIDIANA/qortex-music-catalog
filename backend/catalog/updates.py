from django.http import Http404


def update_existing(instance, fields):
    """Write validated metadata without Model.save()'s fallback insert after deletion."""
    queryset = type(instance).objects.filter(pk=instance.pk)
    exists = queryset.update(**fields) if fields else queryset.exists()
    if not exists:
        raise Http404("This item was deleted. Reload the catalog.")
    for field, value in fields.items():
        setattr(instance, field, value)
    return instance
