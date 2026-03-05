from django.contrib.contenttypes.models import ContentType
from .models import Activity


def create_activity(user, obj, type, title, due_date=None):

    content_type = ContentType.objects.get_for_model(obj)

    Activity.objects.create(
        user=user,
        type=type,
        title=title,
        content_type=content_type,
        object_id=obj.id,
        due_date=due_date
    )
