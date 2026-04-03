from rest_framework import serializers
from .models import StudyMaterial, MaterialFile


class MaterialFileSerializer(serializers.ModelSerializer):

    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = MaterialFile
        fields = ["id", "file_url", "file_name","file_size"]

    def get_file_name(self, obj):
        return obj.filename()

    def get_file_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
    def get_file_size(self, obj):
        size = obj.file.size  # bytes


class StudyMaterialSerializer(serializers.ModelSerializer):

    files = serializers.SerializerMethodField()

    # ✅ FIELD
    chapter_title = serializers.SerializerMethodField()

    class Meta:
        model = StudyMaterial
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "chapter_title",
            "files"
        ]

    def get_files(self, obj):
        request = self.context.get("request")
        return MaterialFileSerializer(
            obj.files.all(),
            many=True,
            context={"request": request}
        ).data

    # ✅ FIXED METHOD
    def get_chapter_title(self, obj):
        if obj.chapter:
            return obj.chapter.title
        return obj.custom_chapter or "No chapter"