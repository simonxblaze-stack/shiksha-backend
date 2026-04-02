import json
from datetime import timedelta

from django.conf import settings
from livekit.api import AccessToken, VideoGrants


def generate_livekit_token(
    user,
    session,
    is_teacher=False,
    display_name=None,
    allow_publish=None,
):
    """
    Generate a LiveKit access token.

    Works for both LiveSession (regular livestream) and
    PrivateSession — both have .room_name.

    Args:
        user:           The Django user joining.
        session:        Any object with a .room_name attribute.
        is_teacher:     Whether this user is the teacher/host.
        display_name:   Override display name. If None, uses
                        profile.full_name → get_full_name() → username.
        allow_publish:  Override publish permission. If None, defaults
                        to is_teacher (only teacher publishes in livestreams).
    """
    token = AccessToken(
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
    )

    token.with_identity(str(user.id))

    # Resolve display name
    if display_name is None:
        profile = getattr(user, "profile", None)
        if profile and getattr(profile, "full_name", None):
            display_name = profile.full_name
        else:
            display_name = user.get_full_name() or user.username
    token.with_name(display_name)

    token.with_metadata(json.dumps({
        "role": "teacher" if is_teacher else "student",
        "user_id": str(user.id),
    }))

    token.with_ttl(timedelta(minutes=10))

    # Resolve publish permission
    can_publish = allow_publish if allow_publish is not None else is_teacher

    grants = VideoGrants(
        room_join=True,
        room=session.room_name,
        can_publish=can_publish,
        can_subscribe=True,
    )

    token.with_grants(grants)

    return token.to_jwt()