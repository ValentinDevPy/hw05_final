from django.utils import timezone

from django.http import HttpRequest


def year(request: HttpRequest) -> dict:
    """Добавляет переменную с текущим годом."""
    current_year = timezone.now().year
    return {
        'year': current_year
    }
