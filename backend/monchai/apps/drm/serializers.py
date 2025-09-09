from rest_framework import serializers
from .models import DRMExport


class DRMExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DRMExport
        fields = [
            'id', 'domaine', 'periode', 'chemin_csv', 'chemin_pdf',
            'checksums', 'data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
