from .models import AuditLog

def log_step(correlation_id: str, step_name: str, status: str, message: str = ""):
    AuditLog.objects.create(
        correlation_id=correlation_id,
        step_name=step_name,
        status=status,
        message=message,
    )
