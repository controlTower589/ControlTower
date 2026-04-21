from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from pathlib import Path

def swagger_ui(request):
    return render(request, "controltower/swagger.html")


def openapi_yaml(request):
    base_dir = Path(settings.BASE_DIR)
    spec_path = base_dir / "openapi.yaml"

    if not spec_path.exists():
        return HttpResponse("openapi.yaml not found", status=404)

    yaml_text = spec_path.read_text(encoding="utf-8")
    return HttpResponse(yaml_text, content_type="application/yaml")
