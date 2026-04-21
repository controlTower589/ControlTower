from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound


def openapi_yaml(request):
    # openapi.yaml is in the same level as manage.py
    spec_path = Path(settings.BASE_DIR) / "openapi.yaml"

    if not spec_path.exists():
        return HttpResponseNotFound(f"openapi.yaml not found at: {spec_path}")

    content = spec_path.read_text(encoding="utf-8")
    return HttpResponse(content, content_type="application/yaml; charset=utf-8")