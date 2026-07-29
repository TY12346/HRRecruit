from rest_framework import serializers


class ReadableIdModelSerializer(serializers.ModelSerializer):
    """Expose the stable public ID without breaking numeric FK API contracts."""

    def get_field_names(self, declared_fields, info):
        field_names = list(super().get_field_names(declared_fields, info))
        if 'public_id' not in field_names:
            field_names.insert(field_names.index('id') + 1 if 'id' in field_names else 0, 'public_id')
        return field_names

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        extra_kwargs.setdefault('public_id', {})['read_only'] = True
        return extra_kwargs
