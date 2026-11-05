"""Rewrite the OSS section of README.md with the user's latest open or merged PRs to other people's repos."""
import json
import os
import re
import urllib.parse
import urllib.request

USER = os.environ.get("GH_USER", "aliassar")
LIMIT = int(os.environ.get("OSS_LIMIT", "8"))
README = "README.md"

query = f"author:{USER} type:pr is:public -user:{USER} -is:draft"
url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
    {"q": query, "sort": "created", "order": "desc", "per_page": 50}
)
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
if token := os.environ.get("GITHUB_TOKEN"):
    req.add_header("Authorization", f"Bearer {token}")
items = json.load(urllib.request.urlopen(req))["items"]

rows, seen = [], set()
for pr in items:
    merged = pr["pull_request"].get("merged_at")
    if pr["state"] != "open" and not merged:
        continue  # closed without merging: leave it off
    repo = "/".join(pr["repository_url"].split("/")[-2:])
    if repo in seen:
        continue  # one line per project keeps the list varied
    seen.add(repo)
    status = "✅ merged" if merged else "🟡 in review"
    title = pr["title"].replace("|", "\\|")
    rows.append(f"| [{repo}](https://github.com/{repo}) | [{title}]({pr['html_url']}) | {status} |")
    if len(rows) == LIMIT:
        break

total = f"https://github.com/search?q={urllib.parse.quote(query)}&type=pullrequests"
block = "\n".join(
    ["| Project | Pull request | Status |", "|---|---|---|", *rows, "", f"<sub>[All my pull requests →]({total})</sub>"]
)

with open(README, encoding="utf-8") as f:
    text = f.read()
new = re.sub(
    r"(<!-- OSS:START -->).*?(<!-- OSS:END -->)", lambda m: f"{m[1]}\n{block}\n{m[2]}", text, flags=re.S
)
if new != text:
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"Updated with {len(rows)} PRs")
else:
    print("No change")
