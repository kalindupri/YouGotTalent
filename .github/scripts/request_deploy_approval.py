"""Posts a UAT deploy's change set to Discord and polls for a human reply of "approved"
before letting the pipeline merge uat -> main. Stdlib-only (urllib) so CI needs no pip
install step. Mirrors the REST approach in backend/app/core/discord_bot.py, but this script
runs standalone in CI and can't import that module (different process, no app settings).

Reads: DISCORD_BOT_TOKEN, DISCORD_DEPLOY_CHANNEL_ID, CHANGE_SET (multiline commit summary),
UAT_URL, POLL_TIMEOUT_MINUTES (default 240) from the environment.
Writes "approved=true"/"approved=false" to $GITHUB_OUTPUT so the next job can gate on it.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

DISCORD_API = "https://discord.com/api/v10"
POLL_INTERVAL_SECONDS = 60


def _headers(token: str) -> dict:
    # Cloudflare (fronting discord.com) blocks requests with urllib's default
    # "Python-urllib/3.x" User-Agent from cloud/CI IP ranges with a 1010 error before they
    # ever reach Discord's API -- a descriptive User-Agent (Discord's own recommended format
    # for bots) avoids that.
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://github.com/kalindupri/YouGotTalent, 1.0)",
    }


def _post(url: str, token: str, payload: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=_headers(token), method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _get(url: str, token: str, params: dict) -> list:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"{url}?{query}", headers=_headers(token), method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def main() -> None:
    token = os.environ["DISCORD_BOT_TOKEN"]
    channel_id = os.environ["DISCORD_DEPLOY_CHANNEL_ID"]
    change_set = os.environ.get("CHANGE_SET", "(no commit summary provided)")
    uat_url = os.environ.get("UAT_URL", "https://test.yougottalent.lk")
    timeout_minutes = int(os.environ.get("POLL_TIMEOUT_MINUTES", "240"))

    content = (
        "**New UAT deploy ready for production review**\n\n"
        f"Tests: backend unit tests + Playwright E2E all passed.\n"
        f"UAT: {uat_url}\n\n"
        f"Changes:\n{change_set}\n\n"
        'Reply **"Approved"** in this thread to merge to `main` and deploy to production.'
    )

    try:
        message = _post(f"{DISCORD_API}/channels/{channel_id}/messages", token, {"content": content})
    except urllib.error.HTTPError as exc:
        print(f"Failed to post to Discord: {exc.code} {exc.read().decode()}", file=sys.stderr)
        _write_output(False)
        sys.exit(1)

    message_id = message["id"]
    print(f"Posted approval request (message {message_id}). Polling for up to {timeout_minutes} minutes...")

    bot_user_id = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{DISCORD_API}/users/@me", headers=_headers(token)), timeout=15
        ).read()
    )["id"]

    deadline = time.time() + timeout_minutes * 60
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)
        try:
            messages = _get(
                f"{DISCORD_API}/channels/{channel_id}/messages", token, {"after": message_id, "limit": 50}
            )
        except urllib.error.HTTPError as exc:
            print(f"Poll failed (will retry): {exc.code}", file=sys.stderr)
            continue

        human_replies = [
            m for m in messages if m["author"]["id"] != bot_user_id and not m["author"].get("bot")
        ]
        for reply in sorted(human_replies, key=lambda m: int(m["id"])):
            if reply.get("content", "").strip().lower() == "approved":
                print(f"Approved by {reply['author'].get('username', 'unknown')}.")
                _write_output(True)
                return

    print("Timed out waiting for approval. Re-run this workflow once someone has replied.")
    _write_output(False)


def _write_output(approved: bool) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    line = f"approved={'true' if approved else 'false'}\n"
    if output_path:
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(line)
    else:
        print(line)


if __name__ == "__main__":
    main()
