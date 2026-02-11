from django.core.exceptions import ValidationError
from urllib.parse import urlparse

def validate_youtube_url(value):
    """
    Разрешает только ссылки на youtube.com или youtu.be
    """
    if not value:
        return

    parsed = urlparse(value)
    allowed_domains = {'www.youtube.com', 'youtube.com', 'youtu.be'}

    if parsed.netloc not in allowed_domains:
        raise ValidationError(
            'Разрешены только ссылки на YouTube (youtube.com или youtu.be)'
        )