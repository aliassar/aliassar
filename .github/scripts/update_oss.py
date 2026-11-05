"""Rewrite the OSS section of README.md with the user's merged or approved PRs to other people's repos."""
import json
import os
import re
import urllib.parse
import urllib.request

USER = os.environ.get("GH_USER", "aliassar")
LIMIT = int(os.environ.get("OSS_LIMIT", "8"))
README = "README.md"


def search(qualifier):
    query = f"author:{USER} type:pr is:public -user:{USER} {qualifier}"
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
        {"q": query, "sort": "created", "order": "desc", "per_page": 50}
    )
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    return json.load(urllib.request.urlopen(req))["items"]


# the search API has no OR across qualifiers, so merge the two result sets
prs = {pr["html_url"]: pr for pr in search("is:merged") + search("review:approved")}
items = sorted(prs.values(), key=lambda pr: pr["created_at"], reverse=True)

rows = []
for pr in items[:LIMIT]:
    repo = "/".join(pr["repository_url"].split("/")[-2:])
    status = "merged" if pr["pull_request"].get("merged_at") else "approved"
    rows.append(f"- **[{repo}](https://github.com/{repo})**: [{pr['title']}]({pr['html_url']}) ({status})")
block = "\n".join(rows) or "<sub>Coming soon.</sub>"

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
