#!/usr/bin/env python3
"""Save the UMA research-portal funding pages of the EM-SENSE founders.

For each researcher, fetch the 'financiacion' tab, follow every project link
and save the raw HTML to _import/uma/. Parsing happens offline.
"""
import json
import pathlib
import re
import time
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
BASE = "https://portaldelainvestigacion.uma.es"
PEOPLE = {"isaac": 1241243, "ruben": 1241180, "antonio": 1241695}
out = pathlib.Path("_import/uma")
out.mkdir(parents=True, exist_ok=True)
log = []


def get(url):
    err = None
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html",
                                                       "Accept-Language": "es-ES,es;q=0.9"})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                log.append({"url": url, "status": r.status, "bytes": len(body)})
                return body.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(3 * (i + 1))
    log.append({"url": url, "error": repr(err)})
    return None


projects = {}
for who, rid in PEOPLE.items():
    for page in range(0, 5):
        url = f"{BASE}/investigadores/{rid}/financiacion" + (f"?page={page}" if page else "")
        html = get(url)
        if not html:
            break
        (out / f"financiacion-{who}-{page}.html").write_text(html)
        ids = sorted(set(re.findall(r"/proyectos/(\d+)/detalle", html)))
        new = [i for i in ids if i not in projects.get(who, [])]
        projects.setdefault(who, [])
        projects[who] += new
        if not new or "page=" + str(page + 1) not in html:
            break
        time.sleep(1.5)

all_ids = sorted({i for ids in projects.values() for i in ids})
for pid in all_ids:
    html = get(f"{BASE}/proyectos/{pid}/detalle")
    if html:
        (out / f"proyecto-{pid}.html").write_text(html)
    time.sleep(1.5)

(out / "index.json").write_text(json.dumps({"projects": projects, "log": log}, indent=1))
print(json.dumps({k: len(v) for k, v in projects.items()}), sum(1 for x in log if "error" in x), "errors")
