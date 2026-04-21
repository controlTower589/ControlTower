from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .forms import TeamMemberForm
from .models import TeamMember
from .email_utils import send_team_member_email


def _clean_tab(tab: str) -> str:
    return tab if tab in ("active", "inactive") else "active"


def _list_url(request, tab: str) -> str:
    """
    Preserve filters + page while going back.
    """
    q = {
        "tab": tab,
        "first_name": (request.GET.get("first_name") or "").strip(),
        "last_name": (request.GET.get("last_name") or "").strip(),
        "email": (request.GET.get("email") or "").strip(),
        "page": (request.GET.get("page") or "").strip(),
    }
    q = {k: v for k, v in q.items() if v}
    return "/team/members/?" + urlencode(q) if q else f"/team/members/?tab={tab}"


def team_members_list(request):
    tab = _clean_tab(request.GET.get("tab", "active"))

    first_name = (request.GET.get("first_name") or "").strip()
    last_name = (request.GET.get("last_name") or "").strip()
    email = (request.GET.get("email") or "").strip()

    qs = TeamMember.objects.order_by("-id").filter(is_active=(tab == "active"))

    if first_name:
        qs = qs.filter(first_name__icontains=first_name)
    if last_name:
        qs = qs.filter(last_name__icontains=last_name)
    if email:
        qs = qs.filter(email__icontains=email)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    querydict = request.GET.copy()
    if "page" in querydict:
        querydict.pop("page")
    querystring = querydict.urlencode()

    return render(request, "team/members_list.html", {
        "tab": tab,
        "page_obj": page_obj,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "querystring": querystring,
        "active_nav": "team",
    })


def team_member_create(request):
    tab = _clean_tab(request.GET.get("tab", "active"))
    back_url = _list_url(request, tab)

    if request.method == "POST":
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            member = form.save()

            # email (do not block UI)
            try:
                send_team_member_email("ADDED", member.first_name, member.last_name, member.email)
            except Exception as e:
                messages.error(request, f"Member added, but email failed: {e}")

            messages.success(request, "Member added.")
            return redirect(back_url)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TeamMemberForm()

    return render(request, "team/member_form.html", {
        "form": form,
        "mode": "add",
        "tab": tab,
        "active_nav": "team",
        "back_url": back_url,
    })


def team_member_edit(request, member_id: int):
    tab = _clean_tab(request.GET.get("tab", "active"))
    back_url = _list_url(request, tab)

    member = get_object_or_404(TeamMember, id=member_id)

    if request.method == "POST":
        form = TeamMemberForm(request.POST, instance=member)
        if form.is_valid():
            member = form.save()

            try:
                send_team_member_email("EDITED", member.first_name, member.last_name, member.email)
            except Exception as e:
                messages.error(request, f"Member updated, but email failed: {e}")

            messages.success(request, "Member updated.")
            return redirect(back_url)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TeamMemberForm(instance=member)

    return render(request, "team/member_form.html", {
        "form": form,
        "mode": "edit",
        "tab": tab,
        "active_nav": "team",
        "back_url": back_url,
    })


@require_POST
def team_member_toggle(request, member_id: int):
    tab = _clean_tab(request.GET.get("tab", "active"))
    back_url = _list_url(request, tab)

    member = get_object_or_404(TeamMember, id=member_id)
    member.is_active = not member.is_active
    member.save(update_fields=["is_active", "updated_at"])

    # email action based on resulting state
    action = "ENABLED" if member.is_active else "DISABLED"
    try:
        send_team_member_email(action, member.first_name, member.last_name, member.email)
    except Exception as e:
        messages.error(request, f"Status updated, but email failed: {e}")

    messages.success(request, "Member status updated.")
    return redirect(back_url)


@require_POST
def team_member_delete(request, member_id: int):
    tab = _clean_tab(request.GET.get("tab", "active"))
    back_url = _list_url(request, tab)

    member = get_object_or_404(TeamMember, id=member_id)

    # email before delete (after delete you lose fields)
    try:
        send_team_member_email("DELETED", member.first_name, member.last_name, member.email)
    except Exception as e:
        messages.error(request, f"Member deleted, but email failed: {e}")

    member.delete()
    messages.success(request, "Member deleted.")
    return redirect(back_url)
