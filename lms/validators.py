import re

from rest_framework.exceptions import ValidationError

# Находим все ссылки вида http://... / https://... в тексте
URL_RE = re.compile(r'https?://[^\s<>"\'()\[\]]+', re.IGNORECASE)

# Разрешён только домен youtube.com (в т.ч. www.youtube.com, m.youtube.com).
# Похоже-поддельные домены (evilyoutube.com, youtube.com.evil.ru) не проходят.
ALLOWED_URL_RE = re.compile(
    r'^https?://(?:[a-z0-9-]+\.)*youtube\.com(?:/|\?|#|$)',
    re.IGNORECASE,
)


def validate_youtube_url(value):
    """
    Проверяет, что в значении нет ссылок на сторонние ресурсы.
    Подходит и для поля с одной ссылкой (URLField),
    и для текстового поля с описанием (TextField).
    """
    if not value:
        return value

    for url in URL_RE.findall(str(value)):
        if not ALLOWED_URL_RE.match(url):
            raise ValidationError(
                f'Ссылка «{url}» недопустима. В материалах урока или курса '
                f'можно размещать ссылки только на youtube.com.'
            )
    return value