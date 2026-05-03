import random
import re

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

from events.models import OperationalEvent
from dashboard.models import Workspace
from audit.services import log_step

from adapters.matrix_client import create_room, post_message, invite_user
from adapters.ollama_client import (
    ollama_generate,
    extract_text,
    force_json_prompt,
    parse_structured,
    OllamaError,
)

from team.models import TeamMember


def _compute_next_actions(ws: Workspace) -> str:

    actions = []
    if not ws.matrix_room_id:
        actions.append("Create Matrix room")
    return "; ".join(actions) if actions else " No pending actions"


def _build_event_text(event: OperationalEvent, payload: dict) -> str:

    req_type = payload.get("request_type", event.event_type) or "REQUEST"
    first = payload.get("first_name") or ""
    last = payload.get("last_name") or ""
    email = payload.get("email") or ""
    msg = payload.get("message") or ""

    return (
        f"Request Type: {req_type}\n"
        f"Requester Name: {first} {last}\n"
        f"Requester Email: {email}\n\n"
        f"User Message:\n{msg}\n"
    )


def _format_workflow_message(summary: str, next_action: str, steps: list, risks: list) -> str:
    steps_text = "\n".join(
        [
            f"- {s.get('step')} (Owner: {s.get('owner')}, Status: {s.get('status')})"
            for s in steps
        ]
    ) if steps else "- (no steps provided)"

    risks_text = "\n".join([f"- {r}" for r in risks]) if risks else "- (no risks listed)"

    return (
        f"{summary}\n\n"
        f"Next Action: {next_action}\n\n"
        f"Steps:\n{steps_text}\n\n"
        f"Risks:\n{risks_text}\n"
    ).strip()


def _looks_like_simple_question(user_message: str) -> bool:

    if not user_message:
        return False

    msg = user_message.strip()

    if len(msg) <= 140 and ("?" in msg):
        return True

    starters = (
        "what", "where", "when", "why", "how", "who", "which",
        "is ", "are ", "do ", "does ", "can ",
        "give me", "list", "tell me", "top "
    )

    return msg.lower().startswith(starters) and len(msg) <= 250


def _answer_has_ellipsis(s: str) -> bool:
    if not s:
        return False
    low = s.lower()
    return ("..." in s) or ("and so on" in low) or ("etc" in low)


def _last_numbered_index(text: str) -> int:

    nums = re.findall(r"\b(\d+)\.\s", text)
    return int(nums[-1]) if nums else 0


def _format_answer_items(answer_to_user: str, answer_items: list) -> str:

    if answer_items and isinstance(answer_items, list):
        lines = []
        for i, item in enumerate(answer_items, start=1):
            lines.append(f"{i}. {item}")

        prefix = (answer_to_user.strip() + "\n\n") if answer_to_user else ""
        return (prefix + "\n".join(lines)).strip()

    return (answer_to_user or "").strip()


def _strip_trailing_ellipsis(text: str) -> str:

    text = re.sub(r"\.\.\.\s*$", "", text).strip()
    text = re.sub(r"(and so on|etc)\.?$", "", text, flags=re.IGNORECASE).strip()
    return text


def _pretty_matrix_message(structured: dict, fallback_text: str) -> str:
    if not structured or not isinstance(structured, dict):
        return fallback_text

    summary = (structured.get("summary") or "").strip()
    next_action = (structured.get("next_action") or "").strip()
    steps = structured.get("steps") or []
    risks = structured.get("risks") or []

    out = []

    if summary:
        out.append(" Summary")
        out.append(summary)
        out.append("")

    if next_action:
        out.append(" Next Action")
        out.append(next_action)
        out.append("")

    out.append(" Steps")
    if steps:
        for i, s in enumerate(steps, start=1):
            step = s.get("step", "")
            owner = s.get("owner", "")
            status = s.get("status", "")
            out.append(f"{i}. {step} (Owner: {owner}, Status: {status})")
    else:
        out.append("- (no steps provided)")

    out.append("")
    out.append(" Risks")

    if risks:
        for r in risks:
            out.append(f"- {r}")
    else:
        out.append("- (no risks listed)")

    return "\n".join(out).strip()


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def process_event(self, event_id):
    event = OperationalEvent.objects.get(id=event_id)
    cid = str(event.correlation_id)
    payload = event.payload  # dict/JSONField

    log_step(
        cid,
        "REQUESTER",
        "SUCCESS",
        f"intake_id={payload.get('intake_id')} "
        f"type={payload.get('request_type')} "
        f"name={payload.get('first_name')} {payload.get('last_name')} "
        f"email={payload.get('email')}",
    )

    def _get_ws():
        return Workspace.objects.filter(correlation_id=cid).order_by("-id").first()

    try:
        log_step(cid, "EVENT_RECEIVED", "SUCCESS", f"event_id={event.id}")
        event.status = "PROCESSING"
        event.save(update_fields=["status"])
        log_step(cid, "EVENT_STATUS", "SUCCESS", "PROCESSING")


        ws, created = Workspace.objects.get_or_create(
            correlation_id=cid,
            defaults={
                "event_type": event.event_type,
                "status": "IN_PROGRESS",
                "latest_summary": "Workflow started",
                "next_actions": "Create Matrix room",
                "intake_id": payload.get("intake_id"),
                "requester_first_name": payload.get("first_name") or "",
                "requester_last_name": payload.get("last_name") or "",
                "requester_email": payload.get("email") or "",
                "webui_session_id": f"ollama-session-{payload.get('intake_id') or event.id}",
                "structured_output": None,
                "owner_name": "None",
                "owner_member": None,
            },
        )


        if not created:
            ws.event_type = event.event_type
            ws.status = "IN_PROGRESS"
            ws.latest_summary = "Retrying workflow"
            ws.intake_id = payload.get("intake_id")
            ws.requester_first_name = payload.get("first_name") or ""
            ws.requester_last_name = payload.get("last_name") or ""
            ws.requester_email = payload.get("email") or ""
            if not ws.webui_session_id:
                ws.webui_session_id = f"ollama-session-{ws.intake_id or event.id}"

        ws.next_actions = _compute_next_actions(ws)

        if created:
            active_owner = _pick_random_active_member()

            if active_owner:
                ws.owner_member = active_owner
                ws.owner_name = f"{active_owner.first_name} {active_owner.last_name}".strip()
            else:
                ws.owner_member = None
                ws.owner_name = "None"

        ws.save(
            update_fields=[
                "event_type",
                "status",
                "latest_summary",
                "next_actions",
                "intake_id",
                "requester_first_name",
                "requester_last_name",
                "requester_email",
                "webui_session_id",
                "updated_at",
                "owner_member",
                "owner_name",
            ]
        )
        log_step(cid, "WORKSPACE_CREATED", "SUCCESS", f"workspace_id={ws.id} created={created}")


        if not ws.matrix_room_id:
            invitees = getattr(settings, "MATRIX_DEFAULT_INVITEES", []) or []
            room_id = create_room(f"ct-{cid}", invitees=invitees)
            ws.matrix_room_id = room_id
            ws.next_actions = _compute_next_actions(ws)
            ws.save(update_fields=["matrix_room_id", "next_actions", "updated_at"])
            log_step(cid, "MATRIX_ROOM_CREATE", "SUCCESS", room_id)


            try:
                post_message(room_id, " Workflow started. AI response will be posted here shortly.")
            except Exception as e:
                log_step(cid, "MATRIX_POST_START", "FAILED", str(e))
        else:
            room_id = ws.matrix_room_id


        if ws.webui_session_id and ws.webui_session_id.startswith("ollama-session-"):
            log_step(cid, "AI_SESSION_CREATE", "SUCCESS", ws.webui_session_id)
        else:
            ws.webui_session_id = f"ollama-session-{ws.id}"
            ws.save(update_fields=["webui_session_id", "updated_at"])
            log_step(cid, "AI_SESSION_CREATE", "SUCCESS", ws.webui_session_id)


        user_message = (payload.get("message") or "").strip()
        event_text = _build_event_text(event, payload)
        prompt = force_json_prompt(event_text)
        structured = None

        try:
            raw = ollama_generate(prompt, model="llama3")
            text = extract_text(raw)
            structured = parse_structured(text)

            summary = (structured.get("summary") or "").strip()
            answer_to_user = (structured.get("answer_to_user") or "").strip()
            answer_items = structured.get("answer_items") or []
            next_action = (structured.get("next_action") or "").strip()
            steps = structured.get("steps") or []
            risks = structured.get("risks") or []

            none_actions = {"NONE", "NO_ACTION", "N/A", ""}
            is_none_action = (next_action or "").strip().upper() in none_actions

            direct_answer_text = _format_answer_items(answer_to_user, answer_items)

            if direct_answer_text or is_none_action or _looks_like_simple_question(user_message):
                ai_response = direct_answer_text or summary or "Answered."
                ws.latest_summary = summary or "Answered directly"
                ws.next_actions = " No pending actions"

                if _answer_has_ellipsis(ai_response):
                    ai_response = _strip_trailing_ellipsis(ai_response)
                    last_i = _last_numbered_index(ai_response)
                    cont_from = last_i + 1 if last_i > 0 else 1

                    cont_prompt = (
                        "You MUST respond in STRICT JSON only. No extra text.\n\n"
                        "Continue the SAME answer WITHOUT using '...','etc','and so on'.\n"
                        f"Continue from item {cont_from} and complete until item 20.\n\n"
                        "Return EXACT JSON:\n"
                        "{\n"
                        ' "summary": "continuation",\n'
                        ' "answer_to_user": "",\n'
                        ' "answer_items": [],\n'
                        ' "next_action": "NONE",\n'
                        ' "steps": [],\n'
                        ' "risks": []\n'
                        "}\n\n"
                        f"Original user request:\n{user_message}\n"
                    )

                    raw2 = ollama_generate(cont_prompt, model="llama3")
                    text2 = extract_text(raw2)
                    structured2 = parse_structured(text2)

                    more_items = structured2.get("answer_items") or []
                    more_text = (structured2.get("answer_to_user") or "").strip()

                    if more_items and isinstance(more_items, list):
                        appended = "\n".join(
                            [f"{i}. {it}" for i, it in enumerate(more_items, start=cont_from)]
                        )
                        ai_response = (ai_response + "\n" + appended).strip()
                    elif more_text:
                        ai_response = (ai_response + "\n" + more_text).strip()

            else:
                ai_response = _format_workflow_message(summary, next_action, steps, risks)
                ws.latest_summary = summary or "Workflow created"
                ws.next_actions = next_action or "No pending actions"

            ws.structured_output = structured
            ws.save(update_fields=["structured_output", "latest_summary", "next_actions", "updated_at"])
            log_step(cid, "AI_RESPONSE_GENERATED", "SUCCESS", ai_response[:200])

        except (OllamaError, Exception) as ai_err:
            ai_response = (
                "We received your request, but the AI service (local Ollama) failed to generate a response. "
                "A team member will follow up shortly."
            )
            ws.status = "AI_FAILED"
            ws.structured_output = None
            ws.latest_summary = "AI failed (Ollama). Response queued for human."
            ws.next_actions = "Retry later or investigate audit logs"
            ws.save(update_fields=["status", "structured_output", "latest_summary", "next_actions", "updated_at"])
            log_step(cid, "AI_RESPONSE_GENERATED", "FAILED", repr(ai_err))


        matrix_text = _pretty_matrix_message(structured or {}, ai_response)
        try:
            post_message(room_id, matrix_text)
        except Exception as e:
            log_step(cid, "MATRIX_POST_AI", "FAILED", str(e))


        to_email = (ws.requester_email or payload.get("email") or "").strip()

        #later we can change this based on requirement
        CC_EMAILS = [
            "brahmendra.jayaraju67@gmail.com",
            "uscan.regions@gmail.com",
        ]

        if to_email:
            try:
                first_name = (ws.requester_first_name or payload.get("first_name") or "").strip() or "there"
                email_body = (
                    f"Hi {first_name},\n\n"
                    f"{ai_response}\n\n"
                    f"Thank you,\n"
                    f"Control Center\n"
                )
                msg = EmailMessage(
                    subject=f"Control Tower Update: {event.event_type}",
                    body=email_body,
                    from_email=None,
                    to=[to_email],
                    cc=CC_EMAILS,
                )
                msg.send(fail_silently=False)
                log_step(cid, "EMAIL_SENT", "SUCCESS", f"to={to_email} cc={','.join(CC_EMAILS)}")


                try:
                    post_message(room_id, f"📧 Email successfully sent to {to_email} (CC: {', '.join(CC_EMAILS)})")
                except Exception as e:
                    log_step(cid, "MATRIX_POST_EMAIL", "FAILED", str(e))

            except Exception as mail_err:
                log_step(cid, "EMAIL_FAILED", "FAILED", repr(mail_err))
        else:
            log_step(cid, "EMAIL_SKIPPED", "FAILED", "No requester_email found")

        event.status = "DONE"
        event.save(update_fields=["status"])
        log_step(cid, "EVENT_STATUS", "SUCCESS", "DONE")


        if ws.status == "AI_FAILED":
            final_status = "AI_FAILED"
        elif (ws.next_actions or "").strip() != " No pending actions":
            final_status = "READY"
        else:
            final_status = "DONE"

        ws.status = final_status
        ws.save(update_fields=["status", "updated_at"])
        log_step(cid, "WORKSPACE_STATUS", "SUCCESS", final_status)

        return ws.id

    except Exception as e:
        log_step(cid, "WORKFLOW_EXCEPTION", "FAILED", repr(e))
        event.status = "FAILED"
        event.save(update_fields=["status"])
        log_step(cid, "EVENT_STATUS", "FAILED", "FAILED")

        ws = _get_ws()
        if ws:
            ws.status = "FAILED"
            ws.latest_summary = "Workflow failed"
            ws.next_actions = "Retry later or investigate audit logs"
            ws.structured_output = None
            ws.save(update_fields=["status", "latest_summary", "next_actions", "structured_output", "updated_at"])
            log_step(cid, "WORKSPACE_STATUS", "FAILED", "FAILED")

        raise



def _pick_random_active_member():
    members = list(TeamMember.objects.filter(is_active=True))
    if not members:
        return None
    return random.choice(members)

