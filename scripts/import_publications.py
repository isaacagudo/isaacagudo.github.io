#!/usr/bin/env python3
"""Fetch Isaac Agudo's publication and patent metadata from public sources.

Writes the raw responses into an output folder so they can be reviewed and
turned into the site's curated data files. Standard library only; every
request is allowed to fail without stopping the others.
"""
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ORCID = "0000-0002-2911-2300"
DBLP_PID = "23/6961"
UA = "isaacagudo.github.io publication import (+https://isaacagudo.github.io)"

out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_import")
out.mkdir(parents=True, exist_ok=True)
log = []


def get(url, accept="application/json", tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                log.append({"url": url, "status": r.status, "bytes": len(body)})
                return body
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    log.append({"url": url, "error": repr(last)})
    return None


def save(name, body):
    if body is not None:
        (out / name).write_bytes(body)


def as_json(body):
    try:
        return json.loads(body) if body else None
    except Exception:  # noqa: BLE001
        return None


# ORCID public record and works
save("orcid-record.json", get(f"https://pub.orcid.org/v3.0/{ORCID}/record"))
save("orcid-works.json", get(f"https://pub.orcid.org/v3.0/{ORCID}/works"))

# DBLP person: BibTeX and XML, trying the mirrors in turn
for kind, accept in (("bib", "application/x-bibtex"), ("xml", "application/xml")):
    for host in ("dblp.org", "dblp.uni-trier.de", "dblp.dagstuhl.de"):
        body = get(f"https://{host}/pid/{DBLP_PID}.{kind}", accept=accept, tries=2)
        if body and not body.lstrip().startswith(b"<!DOCTYPE html"):
            save(f"dblp.{kind}", body)
            break

# OpenAlex author and works (includes abstracts as inverted indexes)
author = as_json(get(f"https://api.openalex.org/authors/orcid:{ORCID}"))
save("openalex-author.json", json.dumps(author, indent=1).encode() if author else None)
if author and author.get("id"):
    aid = author["id"].rsplit("/", 1)[-1]
    works, cursor = [], "*"
    while cursor:
        page = as_json(get(
            f"https://api.openalex.org/works?filter=author.id:{aid}&per-page=200"
            f"&cursor={urllib.parse.quote(cursor)}"))
        if not page:
            break
        works += page.get("results", [])
        cursor = page.get("meta", {}).get("next_cursor")
        if not page.get("results"):
            break
    save("openalex-works.json", json.dumps(works, indent=1).encode())

# Collect DOIs from every source, then ask Crossref for each one
dois = set()
for name in ("orcid-works.json", "openalex-works.json"):
    p = out / name
    if p.exists():
        dois |= {d.lower() for d in re.findall(r'10\.\d{4,9}/[^\s"<>]+', p.read_text(errors="ignore"))}
p = out / "dblp.bib"
if p.exists():
    dois |= {d.lower() for d in re.findall(r'doi\s*=\s*\{(10\.[^}]+)\}', p.read_text(errors="ignore"))}
dois = sorted({d.rstrip(".,;") for d in dois})
crossref = {}
for d in dois:
    j = as_json(get(f"https://api.crossref.org/works/{urllib.parse.quote(d, safe='/')}"))
    if j and j.get("message"):
        crossref[d] = j["message"]
    time.sleep(0.2)
save("crossref.json", json.dumps(crossref, indent=1).encode())

# Google Patents: search by inventor name variants
patents = {}
for q in ('inventor:"Isaac Agudo"', 'inventor:"Agudo Ruiz"', 'inventor:"Isaac Agudo Ruiz"'):
    inner = urllib.parse.urlencode({"q": q, "num": "100"})
    url = "https://patents.google.com/xhr/query?" + urllib.parse.urlencode({"url": inner, "exp": ""})
    patents[q] = as_json(get(url))
    time.sleep(1)
save("google-patents.json", json.dumps(patents, indent=1).encode())

# Google Patents: full page of each relevant publication (inventors, abstract, status)
for num in ("US10691817B2", "US20180091301A1", "WO2018102382A1", "US10581603B2",
            "WO2018208786A1", "US10574440B2", "WO2018208787A1", "ES3075470A1",
            "WO2026162858A1", "EP2809027B1"):
    save(f"patent-{num}.html", get(f"https://patents.google.com/patent/{num}/en", accept="text/html"))
    time.sleep(1)

# DBLP search API (the person pages sit behind a bot check)
save("dblp-search.json", get("https://dblp.org/search/publ/api?" + urllib.parse.urlencode(
    {"q": "author:Isaac_Agudo:", "format": "json", "h": "1000"})))

# Semantic Scholar author papers
ss = as_json(get("https://api.semanticscholar.org/graph/v1/author/search?" + urllib.parse.urlencode(
    {"query": "Isaac Agudo", "fields": "name,affiliations,paperCount,externalIds"})))
save("s2-authors.json", json.dumps(ss, indent=1).encode() if ss else None)

# University of Malaga research portal, publications list (all pages)
for page in range(1, 6):
    save(f"uma-portal-{page}.html", get(
        f"https://portaldelainvestigacion.uma.es/investigadores/1241243/publicaciones?lang=en&page={page}",
        accept="text/html"))

# Individual pages for works no database lists yet (e.g. recent ePrint preprints)
for url in ("https://eprint.iacr.org/2026/1804",):
    name = re.sub(r"[^a-z0-9]+", "-", url.split("://", 1)[1].lower()).strip("-")
    save(f"page-{name}.html", get(url, accept="text/html"))

# ORCID public search for PhD students without an iD in any paper metadata
students = {}
for key, q in (
    ("marco-lopez", 'given-names:Marco AND family-name:L*pez AND affiliation-org-name:M*laga'),
    ("fran-zafra", 'family-name:Zafra AND affiliation-org-name:M*laga'),
    ("fran-zafra-any", 'given-names:(Fran OR Francisco) AND family-name:Zafra'),
    ("alvaro-lopez", 'given-names:(*lvaro) AND family-name:L*pez AND affiliation-org-name:M*laga'),
):
    students[key] = as_json(get("https://pub.orcid.org/v3.0/expanded-search/?" + urllib.parse.urlencode({"q": q, "rows": "50"})))
save("orcid-student-search.json", json.dumps(students, indent=1, ensure_ascii=False).encode())

(out / "log.json").write_text(json.dumps(log, indent=1))
print(f"{len(dois)} DOIs, {len(crossref)} Crossref records")
for e in log:
    print(e)
