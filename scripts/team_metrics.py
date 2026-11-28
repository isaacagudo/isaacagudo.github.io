#!/usr/bin/env python3
"""Fetch comparable research metrics for the EM-SENSE founding team.

Raw responses go to _import/team/. Standard library only; every request may
fail without stopping the rest.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

UA_API = "isaacagudo.github.io team metrics (+https://isaacagudo.github.io)"
UA_WEB = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/124.0 Safari/537.36")
out = pathlib.Path("_import/team")
out.mkdir(parents=True, exist_ok=True)
log = []


def get(url, accept="application/json", ua=UA_API):
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": accept,
                                                       "Accept-Language": "en-US,en;q=0.8"})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                log.append({"url": url, "status": r.status, "bytes": len(body)})
                return body
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    log.append({"url": url, "error": repr(err)})
    return None


def as_json(b):
    try:
        return json.loads(b) if b else None
    except Exception:  # noqa: BLE001
        return None


def save(name, obj):
    if obj is None:
        return
    p = out / name
    if isinstance(obj, (bytes, bytearray)):
        p.write_bytes(obj)
    else:
        p.write_text(json.dumps(obj, indent=1, ensure_ascii=False))


# Round 2: ORCID records and OpenAlex works for the identified profiles
ids = {"isaac": ("0000-0002-2911-2300", "A5053752266"),
       "ruben": ("0000-0002-6251-4897", "A5070742888"),
       "antonio": ("0000-0002-6751-0625", "A5101720746"),
       "sergio": ("0009-0000-2655-6718", "A5128206455")}
for key, (orc, oa) in ids.items():
    save(f"orcid-record-{key}.json", as_json(get(f"https://pub.orcid.org/v3.0/{orc}/record")))
    works, cursor = [], "*"
    while cursor:
        page = as_json(get("https://api.openalex.org/works?" + urllib.parse.urlencode({
            "filter": f"author.id:{oa}", "per-page": "200", "cursor": cursor,
            "select": "id,doi,title,type,publication_year,cited_by_count,primary_location,authorships"})))
        if not page or not page.get("results"):
            break
        works += page["results"]
        cursor = page.get("meta", {}).get("next_cursor")
    save(f"openalex-works-{key}.json", works)
    time.sleep(0.5)

patents = {}
for q in ('inventor:"Ruben Rios"', 'inventor:"Rios del Pozo"', 'inventor:"Antonio Munoz Gallego"',
          'inventor:"Sergio Lopez Flores"'):
    inner = urllib.parse.urlencode({"q": q, "num": "100"})
    patents[q] = as_json(get("https://patents.google.com/xhr/query?" + urllib.parse.urlencode({"url": inner, "exp": ""})))
    time.sleep(5)
save("google-patents-2.json", patents)

(out / "log.json").write_text(json.dumps(log, indent=1))
for e in log:
    print(e)
