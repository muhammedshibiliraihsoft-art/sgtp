from rest_framework import serializers

from apps.clients.models import Client, RelatedPerson


class ContactSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    phone_normalized = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        fields = (
            "id",
            "name",
            "phone",
            "phone_normalized",
            "email",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name must not be blank.")
        return value


class ClientSerializer(ContactSerializer):
    class Meta(ContactSerializer.Meta):
        model = Client


class RelatedPersonSerializer(ContactSerializer):
    primary_client_id = serializers.UUIDField(read_only=True)

    class Meta(ContactSerializer.Meta):
        model = RelatedPerson
        fields = ContactSerializer.Meta.fields + ("primary_client_id",)


class DuplicateMatchSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class DuplicateWarningSerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=("possible_duplicate",))
    field = serializers.ChoiceField(choices=("phone", "email"))
    matches = DuplicateMatchSerializer(many=True)


class ContactWriteResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    phone = serializers.CharField(allow_blank=True)
    phone_normalized = serializers.CharField(allow_blank=True)
    email = serializers.EmailField(allow_blank=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    warnings = DuplicateWarningSerializer(many=True)


class RelatedPersonWriteResponseSerializer(ContactWriteResponseSerializer):
    primary_client_id = serializers.UUIDField()
