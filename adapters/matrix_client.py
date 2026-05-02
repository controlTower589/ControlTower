import time
import requests
from django.conf import settings

class MatrixError(Exception):
    pass

def _enabled() -> bool:
    return bool(getattr(settings, "MATRIX_ACCESS_TOKEN", "")) and bool(getattr(settings, "MATRIX_HOMESERVER_URL", ""))

def _headers():
    return {
        "Authorization": f"Bearer {settings.MATRIX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
         }

def create_room(name: str, invitees: list[str] | None = None) -> str:
    if not _enabled():
        raise MatrixError("Matrix not configured.")

    url = settings.MATRIX_HOMESERVER_URL.rstrip("/") + "/_matrix/client/v3/createRoom"

    payload = {
        "name": name,
        "preset": "private_chat",
        "is_direct": False,
    }

    # 🔥 DEBUG
    print("AUTO INVITE FLAG:", getattr(settings, "AUTO_INVITE_ALL_USERS", False))

    if getattr(settings, "AUTO_INVITE_ALL_USERS", False):

        users_url = settings.MATRIX_HOMESERVER_URL.rstrip("/") + "/_synapse/admin/v2/users?limit=1000"
        res = requests.get(users_url, headers=_headers())

        print("USERS RESPONSE STATUS:", res.status_code)

        users = res.json().get("users", [])
        auto_invite = []

        for u in users:
            user_id = u.get("name")

            if not user_id:
                continue

            # skip bot
            if "controltower-bot" in user_id:
                continue

            # TEMP: invite ALL users (no filter)
            auto_invite.append(user_id)

        print("AUTO INVITE LIST:", auto_invite)

        payload["invite"] = auto_invite

    elif invitees:
        payload["invite"] = invitees

    r = requests.post(url, json=payload, headers=_headers(), timeout=30)

    if r.status_code >= 400:
        print("CREATE ROOM ERROR:", r.text)
        raise MatrixError(f"Matrix createRoom failed: {r.status_code} {r.text}")

    return r.json()["room_id"]

def invite_user(room_id: str, user_id: str) -> None:
    if not _enabled():
        raise MatrixError("Matrix not configured.")

    url = settings.MATRIX_HOMESERVER_URL.rstrip("/") + f"/_matrix/client/v3/rooms/{room_id}/invite"
    payload = {"user_id": user_id}

    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    if r.status_code >= 400:
        raise MatrixError(f"Matrix invite failed: {r.status_code} {r.text}")

def post_message(room_id: str, text: str) -> None:
    if not _enabled():
        raise MatrixError("Matrix not configured. Set MATRIX_HOMESERVER_URL and MATRIX_ACCESS_TOKEN.")

    txn_id = str(int(time.time() * 1000))
    url = settings.MATRIX_HOMESERVER_URL.rstrip("/") + f"/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}"
    payload = {"msgtype": "m.text", "body": text}

    r = requests.put(url, json=payload, headers=_headers(), timeout=30)
    if r.status_code >= 400:
        raise MatrixError(f"Matrix send failed: {r.status_code} {r.text}")
