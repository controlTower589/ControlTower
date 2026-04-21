from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from .models import Event, AgentRun
from .ollama_client import call_ollama


def build_prompt(event_text: str) -> str:
    return f"""
You are an operations agent.
Convert the event into a structured workflow.

Return STRICT JSON only (no markdown, no extra text) with keys:
summary (string),
category (string),
steps (array of objects with: step, owner, status),
next_action (string),
risks (array of strings)

Event: {event_text}
""".strip()


def extract_json_maybe(text: str):
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None
    return None


@csrf_exempt
def create_event(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body or "{}")
    event_text = (body.get("event_text") or "").strip()
    title = (body.get("title") or "").strip()

    if not event_text:
        return JsonResponse({"error": "event_text is required"}, status=400)

    ev = Event.objects.create(title=title, event_text=event_text)
    return JsonResponse({"id": ev.id, "status": ev.status})


@csrf_exempt
def run_event_agent(request, event_id: int):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    ev = get_object_or_404(Event, id=event_id)
    ev.status = "RUNNING"
    ev.save(update_fields=["status"])

    prompt = build_prompt(ev.event_text)

    try:
        result = call_ollama(prompt, model="llama3")
        raw = (result.get("response") or "").strip()
        structured = extract_json_maybe(raw)

        AgentRun.objects.create(
            event=ev,
            model_name=result.get("model", "llama3"),
            prompt=prompt,
            raw_response=raw,
            structured_output=structured,
            success=structured is not None,
            error="" if structured is not None else "Could not parse JSON from model output",
        )

        ev.status = "DONE" if structured is not None else "FAILED"
        ev.save(update_fields=["status"])

        return JsonResponse({
            "event_id": ev.id,
            "status": ev.status,
            "structured_output": structured,
            "raw_response": raw,
        })

    except Exception as e:
        AgentRun.objects.create(
            event=ev,
            model_name="llama3",
            prompt=prompt,
            raw_response="",
            structured_output=None,
            success=False,
            error=str(e),
        )
        ev.status = "FAILED"
        ev.save(update_fields=["status"])
        return JsonResponse({"event_id": ev.id, "status": "FAILED", "error": str(e)}, status=500)

def control_tower_dashboard(request):
    events = Event.objects.all().order_by("-created_at")

    data = []
    for ev in events:
        latest_run = ev.runs.order_by("-created_at").first()
        structured = latest_run.structured_output if latest_run else None

        # ✅ Use latest run to decide display status
        display_status = ev.status
        if latest_run:
            if latest_run.success:
                display_status = "DONE"
                # optional: heal DB status if stuck
                if ev.status != "DONE":
                    ev.status = "DONE"
                    ev.save(update_fields=["status"])
            else:
                display_status = "FAILED"
                if ev.status != "FAILED":
                    ev.status = "FAILED"
                    ev.save(update_fields=["status"])

        data.append({
            "id": ev.id,
            "title": ev.title,
            "status": display_status,
            "summary": structured.get("summary") if structured else None,
            "next_action": structured.get("next_action") if structured else None,
        })

    return render(request, "controltower/dashboard.html", {"events": data})


def event_detail(request, event_id: int):
    ev = get_object_or_404(Event, id=event_id)
    latest_run = ev.runs.order_by("-created_at").first()

    # If last run succeeded, mark DONE; if failed, mark FAILED
    if latest_run:
        if latest_run.success and ev.status != "DONE":
            ev.status = "DONE"
            ev.save(update_fields=["status"])
        elif (not latest_run.success) and ev.status != "FAILED":
            ev.status = "FAILED"
            ev.save(update_fields=["status"])

    structured = latest_run.structured_output if latest_run else None

    return render(request, "controltower/event_detail.html", {
        "event": ev,
        "latest_run": latest_run,
        "structured": structured,
        "runs": ev.runs.order_by("-created_at"),
    })


def run_agent_from_ui(request, event_id: int):
    if request.method != "POST":
        return redirect("/control-tower/")

    # Run the agent by calling the same endpoint internally
    run_event_agent(request, event_id)

    # After run completes (status updated in DB), redirect to detail page
    return redirect(f"/control-tower/events/{event_id}/")

from django.views.decorators.csrf import csrf_protect

@csrf_protect
def create_event_ui(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        event_text = (request.POST.get("event_text") or "").strip()

        if event_text:
            ev = Event.objects.create(title=title or "Untitled Event", event_text=event_text)
            return redirect(f"/control-tower/events/{ev.id}/")

    return render(request, "controltower/create_event.html")



