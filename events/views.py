from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .forms import IntakeRequestForm
from events.services import create_event

def create_request(request):
    if request.method == "POST":
        form = IntakeRequestForm(request.POST)
        if form.is_valid():
            obj = form.save()

            payload = {
                "intake_id": obj.id,
                "request_type": obj.request_type,
                "first_name": obj.first_name,
                "last_name": obj.last_name,
                "email": obj.email,
                "message": obj.message,
            }

            event = create_event(obj.request_type, payload)

            return render(request, "intake/success.html", {"obj": obj, "event": event})
    else:
        form = IntakeRequestForm()

    return render(request, "intake/create_request.html", {"form": form})
