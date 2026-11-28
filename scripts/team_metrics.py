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


# OpenAlex: authors by ORCID where known, by name search otherwise
people = {
    "isaac": {"orcid": "0000-0002-2911-2300", "search": "Isaac Agudo"},
    "ruben": {"orcid": "0000-0002-6251-4897", "search": "Ruben Rios"},
    "antonio": {"orcid": None, "search": "Antonio Muñoz Gallego"},
    "sergio": {"orcid": None, "search": "Sergio López Flores"},
}
for key, p in people.items():
    res = {}
    if p["orcid"]:
        res["by_orcid"] = as_json(get(f"https://api.openalex.org/authors/orcid:{p['orcid']}"))
    res["search"] = as_json(get("https://api.openalex.org/authors?" + urllib.parse.urlencode(
        {"search": p["search"], "per-page": "25"})))
    save(f"openalex-{key}.json", res)
    time.sleep(0.5)

# Extra name variants that OpenAlex may hold
for key, q in (("antonio2", "Antonio Muñoz"), ("antonio3", "Antonio J. Muñoz"), ("sergio2", "Sergio López")):
    save(f"openalex-{key}.json", {"search": as_json(get("https://api.openalex.org/authors?" + urllib.parse.urlencode(
        {"search": q, "filter": "last_known_institutions.country_code:ES", "per-page": "50"})))})

# ORCID directory
orcid = {}
for key, q in (
    ("antonio", 'given-names:Antonio AND family-name:(Mu*oz) AND affiliation-org-name:M*laga'),
    ("sergio", 'given-names:Sergio AND family-name:(L*pez) AND affiliation-org-name:M*laga'),
    ("ruben", 'family-name:R*os AND given-names:Rub*n AND affiliation-org-name:M*laga'),
):
    orcid[key] = as_json(get("https://pub.orcid.org/v3.0/expanded-search/?" + urllib.parse.urlencode({"q": q, "rows": "50"})))
save("orcid-search.json", orcid)

# Google Patents by inventor
patents = {}
for q in ('inventor:"Ruben Rios"', 'inventor:"Rios del Pozo"', 'inventor:"Antonio Munoz Gallego"',
          'inventor:"Antonio Muñoz Gallego"', 'inventor:"Sergio Lopez Flores"', 'inventor:"Isaac Agudo"'):
    inner = urllib.parse.urlencode({"q": q, "num": "100"})
    patents[q] = as_json(get("https://patents.google.com/xhr/query?" + urllib.parse.urlencode({"url": inner, "exp": ""})))
    time.sleep(1)
save("google-patents.json", patents)

# Google Scholar: profile pages (may be blocked)
scholar = {}
save("scholar-isaac.html", get("https://scholar.google.com/citations?user=JGd3lHkAAAAJ&hl=en", accept="text/html", ua=UA_WEB))
for key, q in (("ruben", "Ruben Rios Malaga"), ("antonio", "Antonio Muñoz Malaga"), ("sergio", "Sergio López Flores")):
    save(f"scholar-search-{key}.html", get("https://scholar.google.com/citations?" + urllib.parse.urlencode(
        {"view_op": "search_authors", "mauthors": q, "hl": "en"}), accept="text/html", ua=UA_WEB))
    time.sleep(3)

# NICS Lab people pages (names, positions)
save("nics-people.html", get("https://www.nics.uma.es/people/", accept="text/html", ua=UA_WEB))

(out / "log.json").write_text(json.dumps(log, indent=1))
for e in log:
    print(e)
