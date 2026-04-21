from .models import OperationalEvent

def create_event(event_type: str, payload: dict) -> OperationalEvent:
    return OperationalEvent.objects.create(
        event_type=event_type,
        payload=payload,
        status="PENDING",
    )
