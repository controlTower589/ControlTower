from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import AuditLog
from django.http import JsonResponse

def audit_for_correlation(request, correlation_id: str):
    logs = AuditLog.objects.filter(correlation_id=correlation_id).order_by("created_at")
    return render(request, "audit/logs.html", {"logs": logs, "correlation_id": correlation_id})





from django.http import JsonResponse
from .models import AuditLog

def audit_for_correlation_api(request, correlation_id: str):
    logs = AuditLog.objects.filter(correlation_id=correlation_id).order_by("created_at")

    data = [
        {
            "created_at": l.created_at.isoformat(),
            "step_name": l.step_name,
            "status": l.status,
            "message": l.message,
        }
        for l in logs
    ]

    return JsonResponse({"correlation_id": correlation_id, "logs": data})
