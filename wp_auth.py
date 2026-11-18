"""
wp_auth.py - sign in to WordPress.com once and save an access token.

Run:  python navipress.py login

Your browser opens a WordPress.com page asking you to approve the app for
one site. After you click Approve, WordPress sends you back to this script,
which swaps the approval code for a token and saves it in .env.
You never type your WordPress password into this program.

If the browser can't load the localhost page afterwards, run
  python navipress.py login --manual
and paste the address from your browser's address bar when asked.
"""

import http.server
import os
import secrets
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"
load_dotenv(ENV)

CLIENT_ID = os.getenv("WPCOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("WPCOM_CLIENT_SECRET")
REDIRECT_URI = os.getenv("WPCOM_REDIRECT_URI", "http://localhost:8765/callback")
SITE = os.getenv("WP_SITE")

if not (CLIENT_ID and CLIENT_SECRET and SITE):
    sys.exit("Fill in WPCOM_CLIENT_ID, WPCOM_CLIENT_SECRET and WP_SITE in .env first.")

state = secrets.token_urlsafe(16)
authorize_url = "https://public-api.wordpress.com/oauth2/authorize?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI, "response_type": "code",
    "state": state, "blog": SITE,
})


def code_from_url(url: str) -> str:
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if q.get("error"):
        sys.exit(f"WordPress said: {q['error'][0]} {q.get('error_description', [''])[0]}")
    if q.get("state", [""])[0] != state:
        sys.exit("The sign-in response didn't match this request. Run wp_auth.py again.")
    return q["code"][0]


def wait_for_redirect() -> str:
    port = urllib.parse.urlparse(REDIRECT_URI).port or 80
    holder = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            holder["url"] = "http://localhost" + self.path
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h2>Signed in. You can close this tab and go back to the terminal.</h2>")

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("localhost", port), Handler)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    print("Opening your browser. Approve the app for your site, then come back here.")
    webbrowser.open(authorize_url)
    print(f"(If it didn't open, visit this address yourself:)\n{authorize_url}\n")
    while "url" not in holder:
        threading.Event().wait(0.5)
    srv.server_close()
    return holder["url"]


if "--manual" in sys.argv:
    print(f"Open this address, approve the app, then copy the address you land on:\n\n{authorize_url}\n")
    returned = input("Paste the full address here: ").strip()
else:
    returned = wait_for_redirect()

resp = requests.post("https://public-api.wordpress.com/oauth2/token", data={
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "redirect_uri": REDIRECT_URI,
    "code": code_from_url(returned), "grant_type": "authorization_code",
}, timeout=30)
if resp.status_code != 200:
    sys.exit(f"Token exchange failed ({resp.status_code}): {resp.text[:300]}")

data = resp.json()
set_key(str(ENV), "WP_TOKEN", data["access_token"])
set_key(str(ENV), "WP_BLOG_ID", str(data["blog_id"]))
print(f"Done. Token saved to .env for {data.get('blog_url')} (blog ID {data['blog_id']}).")
print("Keep .env private: anyone with that token can edit this site.")
