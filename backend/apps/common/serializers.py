from rest_framework import serializers


class PublicIdRelatedField(serializers.SlugRelatedField):
    """Represent model relationships with public IDs, accepting legacy PKs temporarily."""

    def __init__(self, **kwargs):
        kwargs.setdefault('slug_field', 'public_id')
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            if isinstance(data, int) or (isinstance(data, str) and data.isdecimal()):
                try:
                    return self.get_queryset().get(pk=data)
                except (TypeError, ValueError, self.get_queryset().model.DoesNotExist):
                    pass
            self.fail('does_not_exist', slug_name=self.slug_field, value=data)


class ReadableIdModelSerializer(serializers.ModelSerializer):
    """Use the typed public ID as the canonical ID at the API boundary."""

    serializer_related_field = PublicIdRelatedField

    def get_fields(self):
        fields = super().get_fields()
        if 'id' in fields:
            fields['id'] = serializers.CharField(source='public_id', read_only=True)
        return fields
