from rest_framework import serializers

from apps.tenants.models import WorkFunctionCode


class MembershipWorkFunctionSetSerializer(serializers.Serializer):
    functions = serializers.ListField(
        child=serializers.ChoiceField(choices=WorkFunctionCode.choices),
        allow_empty=True,
        max_length=len(WorkFunctionCode.choices),
    )

    def validate_functions(self, functions):
        if len(functions) != len(set(functions)):
            raise serializers.ValidationError(
                "Duplicate Work Functions are not allowed."
            )
        return functions
