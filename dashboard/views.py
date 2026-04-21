import json
from django.db import models
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from events.models import OperationalEvent
from audit.services import log_step
from .models import Workspace
from workflows.tasks import process_event

from adapters.matrix_client import create_room as matrix_create_room


def dashboard_home(request):
    qs = Workspace.objects.order_by("-updated_at")

    # ✅ Filters
    event_type = (request.GET.get("event_type") or "").strip()
    status = (request.GET.get("status") or "").strip()
    first_name = (request.GET.get("first_name") or "").strip()
    last_name = (request.GET.get("last_name") or "").strip()
    email = (request.GET.get("email") or "").strip()
    next_actions = (request.GET.get("next_actions") or "").strip()
    matrix_room = (request.GET.get("matrix_room") or "").strip()

    # ✅ NEW: Owner search (one search bar)
    owner = (request.GET.get("owner") or "").strip()
    if owner:
        qs = qs.filter(
            models.Q(owner__first_name__icontains=owner) |
            models.Q(owner__last_name__icontains=owner) |
            models.Q(owner__email__icontains=owner)
        )

    if event_type:
        qs = qs.filter(event_type__icontains=event_type)
    if status:
        qs = qs.filter(status__icontains=status)
    if first_name:
        qs = qs.filter(requester_first_name__icontains=first_name)
    if last_name:
        qs = qs.filter(requester_last_name__icontains=last_name)
    if email:
        qs = qs.filter(requester_email__icontains=email)
    if next_actions:
        qs = qs.filter(next_actions__icontains=next_actions)
    if matrix_room:
        qs = qs.filter(matrix_room_id__icontains=matrix_room)

    # ✅ Owner filter across owner_first_name/owner_last_name/owner_email
    if owner:
        qs = qs.filter(
            Q(owner_first_name__icontains=owner)
            | Q(owner_last_name__icontains=owner)
            | Q(owner_email__icontains=owner)
        )

    # ✅ Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ✅ For pagination links: keep all filters except "page"
    querydict = request.GET.copy()
    if "page" in querydict:
        querydict.pop("page")
    querystring = querydict.urlencode()

    filters = {
        "event_type": event_type,
        "status": status,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "next_actions": next_actions,
        "matrix_room": matrix_room,
        "owner": owner,  # ✅ NEW
    }

    return render(request, "dashboard/index.html", {
        "page_obj": page_obj,
        "workspaces": page_obj,   # ✅ keeps your existing template loop working
        "active_nav": "dashboard",
        "filters": filters,
        "querystring": querystring,  # ✅ used by Prev/Next links
    })


@require_POST
def retry_workflow(request, workspace_id: int):
    ws = get_object_or_404(Workspace, id=workspace_id)

    event = OperationalEvent.objects.filter(
        correlation_id=ws.correlation_id
    ).order_by("-id").first()

    if not event:
        log_step(str(ws.correlation_id), "RETRY_REQUESTED", "FAILED", "No OperationalEvent found")
        ws.latest_summary = "Retry requested, but no event found. Check audit logs."
        ws.next_actions = "Investigate audit logs"
        ws.save(update_fields=["latest_summary", "next_actions", "updated_at"])
        return redirect("workspace_detail", workspace_id=ws.id)

    # ✅ Immediately show it is being worked on
    ws.status = "IN_PROGRESS"
    ws.latest_summary = "Retry requested. Workflow re-queued."
    ws.next_actions = "Waiting for workflow results"
    ws.save(update_fields=["status", "latest_summary", "next_actions", "updated_at"])

    log_step(str(ws.correlation_id), "RETRY_REQUESTED", "SUCCESS", f"workspace_id={ws.id}, event_id={event.id}")
    process_event.delay(event.id)

    return redirect("workspace_detail", workspace_id=ws.id)


def _safe_structured_output(ws: Workspace) -> dict:
    structured = ws.structured_output or {}
    if isinstance(structured, str):
        try:
            structured = json.loads(structured)
        except Exception:
            structured = {}
    if not isinstance(structured, dict):
        structured = {}
    return structured


def _format_answer(answer_to_user: str, answer_items: list) -> str:
    answer_to_user = (answer_to_user or "").strip()

    if isinstance(answer_items, list) and len(answer_items) > 0:
        lines = []
        for i, item in enumerate(answer_items, start=1):
            lines.append(f"{i}. {item}")

        if answer_to_user:
            return (answer_to_user + "\n\n" + "\n".join(lines)).strip()
        return "\n".join(lines).strip()

    return answer_to_user


def workspace_detail(request, workspace_id: int):
    ws = get_object_or_404(Workspace, id=workspace_id)

    event = OperationalEvent.objects.filter(
        correlation_id=ws.correlation_id
    ).order_by("-id").first()

    # ✅ Get the exact user typed text
    user_request = ""
    if event and isinstance(getattr(event, "payload", None), dict):
        p = event.payload
        # try common keys
        user_request = (p.get("message") or p.get("chat") or p.get("text") or "").strip()

    # Matrix URL
    matrix_url = ""
    if ws.matrix_room_id and getattr(settings, "MATRIX_WEB_URL", ""):
        matrix_url = f"{settings.MATRIX_WEB_URL}/#/room/{ws.matrix_room_id}"

    structured = _safe_structured_output(ws)
    steps = structured.get("steps") or []
    risks = structured.get("risks") or []
    answer_to_user_raw = structured.get("answer_to_user") or ""
    answer_items = structured.get("answer_items") or []
    answer_to_user = _format_answer(answer_to_user_raw, answer_items)

    summary_text = (ws.latest_summary or "").lower()
    ai_failed = (
        ws.status in {"FAILED", "AI_FAILED"}
        or "ai failed" in summary_text
        or ("ollama" in summary_text and "failed" in summary_text)
    )

    return render(
        request,
        "dashboard/detail.html",
        {
            "ws": ws,
            "matrix_url": matrix_url,
            "answer_to_user": answer_to_user,
            "steps": steps,
            "risks": risks,
            "ai_failed": ai_failed,

            # ✅ only this (not full payload)
            "user_request": user_request,
            "active_nav": "dashboard",



        }
    )



@require_POST
def create_matrix_room(request, workspace_id: int):
    ws = get_object_or_404(Workspace, id=workspace_id)
    log_step(str(ws.correlation_id), "MATRIX_ROOM_CREATE", "STARTED", f"workspace_id={ws.id}")

    try:
        created_now = False

        if not ws.matrix_room_id:
            ws.matrix_room_id = matrix_create_room(f"ct-{ws.correlation_id}")
            created_now = True

        ws.next_actions = "✅ No pending actions" if ws.matrix_room_id else "Create Matrix room"
        if created_now:
            ws.latest_summary = "Matrix room created"

        ws.save(update_fields=["matrix_room_id", "next_actions", "latest_summary", "updated_at"])
        log_step(str(ws.correlation_id), "MATRIX_ROOM_CREATE", "SUCCESS", f"room_id={ws.matrix_room_id}")

    except Exception as e:
        ws.status = "FAILED"
        ws.latest_summary = "Matrix room creation failed"
        ws.next_actions = "Retry later or investigate audit logs"
        ws.save(update_fields=["status", "latest_summary", "next_actions", "updated_at"])
        log_step(str(ws.correlation_id), "MATRIX_ROOM_CREATE", "FAILED", str(e))

    return redirect("workspace_detail", workspace_id=ws.id)
