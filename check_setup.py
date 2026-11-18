"""
check_setup.py - make sure both halves work before you run the agent.

  1. Your NaviGator key: lists the models it can use and checks that the
     chosen model can call a tool (agents need this).
  2. Your WordPress sign-in: reads your site's name and counts its pages.

Nothing is changed on your site.

Run:  python check_setup.py
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ok = True
model = os.getenv("NAVIGATOR_MODEL", "gpt-oss-120b")

print("1) NaviGator key")
try:
    llm = OpenAI(api_key=os.environ["NAVIGATOR_API_KEY"],
                 base_url=os.getenv("NAVIGATOR_BASE_URL", "https://api.navigator.ai.ufl.edu/v1"))
    models = [m.id for m in llm.models.list().data]
    print(f"   Key works. Models on this key: {', '.join(models)}")
    tool = {"type": "function", "function": {
        "name": "get_weather", "description": "Get the weather for a city",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}
    r = llm.chat.completions.create(model=model, tools=[tool], tool_choice="auto",
                                    messages=[{"role": "user", "content": "What's the weather in Gainesville?"}])
    calls = r.choices[0].message.tool_calls
    if calls:
        print(f"   {model} can call tools: {calls[0].function.name}({calls[0].function.arguments})")
    else:
        ok = False
        print(f"   {model} answered without calling the tool. Try another model with --model.")
except KeyError:
    ok = False
    print("   NAVIGATOR_API_KEY is missing from .env")
except Exception as e:
    ok = False
    print(f"   Problem: {e}")

print("2) WordPress sign-in")
blog, token = os.getenv("WP_BLOG_ID"), os.getenv("WP_TOKEN")
if not (blog and token):
    ok = False
    print("   Not signed in yet. Run: python navipress.py login")
else:
    h = {"Authorization": f"Bearer {token}"}
    site = requests.get(f"https://public-api.wordpress.com/rest/v1.1/sites/{blog}", headers=h, timeout=30)
    pages = requests.get(f"https://public-api.wordpress.com/wp/v2/sites/{blog}/pages",
                         headers=h, params={"per_page": 100, "status": "publish,draft",
                                            "context": "edit", "_fields": "id"}, timeout=30)
    if site.ok and pages.ok:
        print(f"   Signed in to \"{site.json().get('name')}\" ({site.json().get('URL')}), "
              f"{len(pages.json())} pages, edit access confirmed.")
    else:
        ok = False
        print(f"   Problem: site {site.status_code}, pages {pages.status_code}: {pages.text[:200]}")

print("\nAll set. Next: python navipress.py pull-site, then see README Step 2." if ok else "\nFix the problems above first.")
