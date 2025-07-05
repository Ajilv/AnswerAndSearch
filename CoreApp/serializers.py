from rest_framework import serializers
from .models import KnowledgeDocument

class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = ['id', 'title', 'file', 'uploaded_at']


class AskQuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
