#!/usr/bin/env python3
"""Merge the raw imports in _import/ into data/works.json (CSL-JSON).

Run once after an import, then review data/works.json by hand: it is the
source of truth for the site and can be edited directly afterwards.

Order of preference for each field: Crossref (for works with a DOI), then
ORCID, then OpenAlex. Duplicates are merged by DOI and by normalised title.
"""
import html
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMP = ROOT / "_import"
OUT = ROOT / "data" / "works.json"

# DOIs listed as "Relevant publications" on the NICS Lab profile page
SELECTED = {
    "10.23919/nisscps00007.2026.00037", "10.1016/j.bcra.2025.100323",
    "10.1109/jiot.2025.3555026", "10.1109/mcom.001.2300839",
    "10.1109/metacom57706.2023.00056", "10.1109/access.2022.3223430",
    "10.1109/tvt.2020.3046640", "10.1049/iet-ifs.2018.5082",
    "10.1109/csf.2015.27", "10.1145/2714576.2714585",
    "10.1007/s10207-014-0230-4", "10.1016/j.cose.2013.05.004",
}

# Records that are not publications, or are duplicates/preprints of a listed one
EXCLUDE_TITLES = [
    "d8.3 final evaluation report",
    "d8.1 legal, economic and technical evaluation",
    "on segura de componentes software basada en openid",
    "security assurance during the software development process",
    "procedings of the 10th european workshop on public key infrastructures",
    "attacks to a proxy-mediated key agreement protocol based on symmetric encryption",
]
EXCLUDE_DOIS = {
    "10.5555/1385289.1385341",            # ACM copy of the MobiMedia 2007 paper
    "10.4018/9781599040905.ch008.ch000",  # duplicate record of the 2007 chapter
}

CR_TYPE = {
    "journal-article": "article-journal",
    "proceedings-article": "paper-conference",
    "book-chapter": "chapter",
    "book": "book",
    "edited-book": "book",
    "monograph": "book",
}
OA_TYPE = {
    "article": "article-journal",
    "conference-paper": "paper-conference",
    "book-chapter": "chapter",
    "book": "book",
    "dissertation": "thesis",
    "preprint": "article",
}
OR_TYPE = {
    "journal-article": "article-journal",
    "conference-paper": "paper-conference",
    "book-chapter": "chapter",
    "book": "chapter",  # ORCID marks LNCS chapters as "book"
    "dissertation-thesis": "thesis",
}


def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def clean(t):
    if not t:
        return t
    t = html.unescape(html.unescape(re.sub(r"<[^>]+>", "", t)))
    return re.sub(r"\s+", " ", t).strip()


def jats_abstract(a):
    a = re.sub(r"<jats:title>.*?</jats:title>", " ", a or "", flags=re.S)
    a = clean(a)
    return re.sub(r"^(Abstract|ABSTRACT)[\s:.]*", "", a) or None


def openalex_abstract(inv):
    if not inv:
        return None
    pos = {}
    for word, idx in inv.items():
        for i in idx:
            pos[i] = word
    text = " ".join(pos[i] for i in sorted(pos))
    return re.sub(r"^(Abstract|ABSTRACT)[\s:.]*", "", clean(text)) or None


def date_parts(d):
    if not d or not d.get("date-parts") or not d["date-parts"][0] or d["date-parts"][0][0] is None:
        return None
    return [int(x) for x in d["date-parts"][0][:2]]


def person(p):
    if p.get("family"):
        out = {"family": clean(p["family"])}
        if p.get("given"):
            out["given"] = clean(p["given"])
        return out
    return {"literal": clean(p.get("name") or p.get("literal") or "")}


def from_crossref(m):
    item = {
        "type": CR_TYPE.get(m.get("type"), "article"),
        "title": clean((m.get("title") or [""])[0])
        + (": " + clean(m["subtitle"][0]) if m.get("subtitle") and clean(m["subtitle"][0]) else ""),
        "author": [person(a) for a in m.get("author", [])],
        "DOI": m["DOI"].lower(),
    }
    if m.get("editor"):
        item["editor"] = [person(a) for a in m["editor"]]
    ct = [clean(c) for c in m.get("container-title", [])]
    if m.get("type") in ("book-chapter", "proceedings-article") and len(ct) > 1:
        item["collection-title"], item["container-title"] = ct[0], ct[-1]
    elif ct:
        item["container-title"] = ct[-1] if m.get("type") == "proceedings-article" else ct[0]
    for k in ("volume", "issue", "page", "publisher"):
        if m.get(k):
            item[k] = clean(str(m[k]))
    if m.get("event", {}).get("name"):
        item["event-title"] = clean(m["event"]["name"])
    dp = date_parts(m.get("published-print")) or date_parts(m.get("issued"))
    if dp:
        item["issued"] = {"date-parts": [dp]}
    if m.get("abstract"):
        item["abstract"] = jats_abstract(m["abstract"])
    if m.get("ISBN"):
        item["ISBN"] = m["ISBN"][0]
    return item


def slug(item, taken):
    a = (item.get("author") or item.get("editor") or [{"family": "agudo"}])[0]
    fam = a.get("family") or a.get("literal", "x").split()[-1]
    fam = norm_title(fam).split()[0] if norm_title(fam) else "x"
    year = item.get("issued", {}).get("date-parts", [[0]])[0][0]
    stop = {"a", "an", "the", "on", "of", "for", "to", "and", "in", "un", "una", "el", "la", "de", "los", "las"}
    words = [w for w in norm_title(item["title"]).split() if w not in stop] or ["work"]
    base = f"{fam}{year}{words[0]}"
    s, n = base, 2
    while s in taken:
        s, n = f"{base}{n}", n + 1
    taken.add(s)
    return s


crossref = json.loads((IMP / "crossref.json").read_text())
crossref = {k.lower(): v for k, v in crossref.items()}
openalex = json.loads((IMP / "openalex-works.json").read_text())
orcid = json.loads((IMP / "orcid-works.json").read_text())

works = {}      # key -> item
by_title = {}   # normalised title -> key


def add(key, item, extra=None):
    nt = norm_title(item["title"])
    if any(nt.startswith(norm_title(x)) for x in EXCLUDE_TITLES) or item.get("DOI") in EXCLUDE_DOIS:
        return
    existing = by_title.get(nt) or (key if key in works else None)
    if existing:
        cur = works[existing]
        if item.get("language"):
            cur["language"] = item["language"]
        for k, v in item.items():
            if v and not cur.get(k):
                cur[k] = v
        if extra:
            for k, v in extra.items():
                cur.setdefault("custom", {}).setdefault(k, v)
        return
    if extra:
        item["custom"] = dict(extra)
    works[key] = item
    by_title[nt] = key


# 1. ORCID works (the record Isaac maintains)
for g in orcid["group"]:
    s = g["work-summary"][0]
    doi = next((e["external-id-value"].lower() for e in (s.get("external-ids") or {}).get("external-id", [])
                if e["external-id-type"] == "doi"), None)
    pd = s.get("publication-date") or {}
    y = (pd.get("year") or {}).get("value")
    if doi and doi in crossref:
        item = from_crossref(crossref[doi])
        if "issued" not in item and y:
            item["issued"] = {"date-parts": [[int(y)]]}
    else:
        item = {"type": OR_TYPE.get(s["type"], "article"), "title": clean(s["title"]["title"]["value"])}
        if doi:
            item["DOI"] = doi
        if y:
            item["issued"] = {"date-parts": [[int(y)]]}
        if s.get("journal-title"):
            item["container-title"] = clean(s["journal-title"]["value"])
    add(doi or norm_title(item["title"]), item, {"sources": ["orcid"]})

# 2. OpenAlex works (fills gaps: recent papers, abstracts, open-access links)
for w in openalex:
    doi = (w.get("doi") or "").replace("https://doi.org/", "").lower() or None
    if doi in EXCLUDE_DOIS:
        continue
    if doi and doi in crossref:
        item = from_crossref(crossref[doi])
    else:
        item = {"type": OA_TYPE.get(w.get("type"), "article"), "title": clean(w.get("title") or "")}
        if not item["title"]:
            continue
        item["author"] = [{"literal": clean(a["author"]["display_name"])} for a in w.get("authorships", [])]
        if doi:
            item["DOI"] = doi
        if w.get("publication_year"):
            item["issued"] = {"date-parts": [[w["publication_year"]]]}
        src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        if src and "dialnet" not in src.lower() and "aisel" not in src.lower():
            item["container-title"] = clean(src)
        b = w.get("biblio") or {}
        for k, ck in (("volume", "volume"), ("issue", "issue")):
            if b.get(k):
                item[ck] = b[k]
        if b.get("first_page"):
            item["page"] = b["first_page"] + (f"-{b['last_page']}" if b.get("last_page") else "")
        if w.get("language"):
            item["language"] = w["language"]
    if w.get("language"):
        item["language"] = w["language"]
    if not item.get("abstract"):
        item["abstract"] = openalex_abstract(w.get("abstract_inverted_index"))
    extra = {"openalex": w["id"].rsplit("/", 1)[-1]}
    oa = w.get("best_oa_location") or {}
    if oa.get("pdf_url") or oa.get("landing_page_url"):
        if (w.get("open_access") or {}).get("is_oa"):
            extra["oa_url"] = oa.get("pdf_url") or oa.get("landing_page_url")
    add(doi or norm_title(item["title"]), item, extra)

# 3. Works missing from every source, entered by hand
add("10.1007/978-3-031-91405-8_11", {
    "type": "chapter",
    "title": "Web3 Security",
    "author": [{"family": "Ramírez", "given": "José Carlos"}, {"family": "Agudo", "given": "Isaac"}],
    "editor": [{"family": "Prinz", "given": "Wolfgang"}, {"family": "Trauth", "given": "Daniel"}],
    "container-title": "Tokenizing the Future: A Guide to Web3 and the Metaverse",
    "publisher": "Springer",
    "page": "163-172",
    "issued": {"date-parts": [[2025]]},
    "DOI": "10.1007/978-3-031-91405-8_11",
}, {"sources": ["manual"]})


# Curation -------------------------------------------------------------------
# Canonical spelling of co-authors whose names some databases strip of accents
CANONICAL = {
    "Javier Lopez": ("López", "Javier"), "Javier López": ("López", "Javier"),
    "David Nuñez": ("Núñez", "David"), "David Nunez": ("Núñez", "David"), "David Núñez": ("Núñez", "David"),
    "Ruben Rios": ("Rios", "Ruben"), "Rubén Ríos": ("Rios", "Ruben"),
    "Carmen Fernandez-Gago": ("Fernández-Gago", "Carmen"), "Carmen Fernandez‐Gago": ("Fernández-Gago", "Carmen"),
    "Carmen Fernández-Gago": ("Fernández-Gago", "Carmen"),
    "Jose A. Montenegro": ("Montenegro", "José A."), "José Antonio Montenegro": ("Montenegro", "José A."),
    "Pablo Sanchez-Serrano": ("Sánchez-Serrano", "Pablo"),
    "Carlos Pares-Pulido": ("Parés-Pulido", "Carlos"),
    "Manuel Montenegro-Gomez": ("Montenegro-Gómez", "Manuel"),
    "Isaac Agudo": ("Agudo", "Isaac"),
}


def canon(p):
    full = (p.get("literal") or f"{p.get('given', '')} {p.get('family', '')}").strip()
    if full in CANONICAL:
        fam, giv = CANONICAL[full]
        return {"family": fam, "given": giv}
    return p


# Per-title fixes: type, venue, casing. Keys are normalised titles (prefix match).
FIXES = {
    "personalized computer security tasks with automatic evaluation": {
        "type": "paper-conference",
        "title": "Personalized Computer Security Tasks with Automatic Evaluation and Feedback",
        "container-title": "Proceedings of the 2019 AIS SIGED International Conference on Information Systems Education and Research",
    },
    "comunicaciones voip cifradas usando intel sgx": {
        "type": "paper-conference",
        "container-title": "Actas de las V Jornadas Nacionales de Investigación en Ciberseguridad (JNIC 2019)",
        "event-place": "Cáceres, Spain",
    },
    "identidades digitalesy": {
        "type": "article-magazine",
        "title": "Identidades digitales y tecnologías de gestión de identidad",
        "container-title": "Novática",
    },
    "a graphical delegation solution for x 509": {"type": "article-magazine", "container-title": "ERCIM News"},
    "la seguridad de la informacion en los nuevos grados eees": {
        "type": "article-magazine", "container-title": "Red Seguridad"},
    "un marco de delegacion de privilegios": {
        "type": "thesis", "genre": "PhD thesis", "publisher": "University of Málaga"},
    "leveraging privacy in identity management as a service": {
        "type": "paper-conference",
        "container-title": "PhD Symposium of the European Conference on Service-Oriented and Cloud Computing (ESOCC 2013)",
        "event-place": "Málaga, Spain"},
    "strong authentication of humans and machines": {"type": "paper-conference"},
}
# Found with no venue in any source: kept in the data but hidden from the site until confirmed
HIDDEN = [
    "authentication and delegation in internet aplications",
    "nuevas nociones de seguridad y transformaciones genericas",
    "sistema de acceso delegado a informacion cifrada para apache hadoop",
    "como proteger la privacidad de los usuarios en internet",
    "distribucion segura de componentes software basada en openid",
    "implementacion de un esquema de localizacion privada",
    "politicas de delegacion para credenciales ponderadas",
    "delegation perspective of practical authorization schemes",
    "especificacion formal y verificacion de requisitos de seguridad",
    "entornos virtuales y presenciales de ensenanza aprendizaje",
]
SERIES = re.compile(r"Lecture Notes|IFIP Advances|Communications in Computer", re.I)

for key, it in works.items():
    nt = norm_title(it["title"])
    for prefix, fix in FIXES.items():
        if nt.startswith(norm_title(prefix)):
            it.update(fix)
    for role in ("author", "editor"):
        if it.get(role):
            it[role] = [canon(p) for p in it[role]]
    # Springer proceedings come through Crossref as book chapters
    if it["type"] == "chapter" and SERIES.search(it.get("collection-title", "") + it.get("container-title", "")):
        it["type"] = "paper-conference"
    if any(nt.startswith(norm_title(h)) for h in HIDDEN):
        it.setdefault("custom", {})["hidden"] = "venue unknown: confirm or remove"

# Finalise: ids, selected flag, language, ordering
taken = set()
items = []
for key, it in works.items():
    it = {k: v for k, v in it.items() if v not in (None, "", [], {})}
    if it.get("DOI") in SELECTED:
        it.setdefault("custom", {})["selected"] = True
    if "language" not in it:
        it["language"] = "es" if re.search(r"[áéíóúñ]|\b(de|la|el|para|en|y)\b", it["title"].lower()) else "en"
    # Edited proceedings: Isaac appears as editor, not author
    if it["type"] == "book" and not it.get("author") and it.get("editor"):
        pass
    it["id"] = slug(it, taken)
    items.append(it)

items.sort(key=lambda i: (-(i.get("issued", {}).get("date-parts", [[0]])[0][0] or 0), i["title"].lower()))
ordered = []
for it in items:
    o = {"id": it.pop("id"), "type": it.pop("type"), "title": it.pop("title")}
    o.update(it)
    ordered.append(o)
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n")
print(f"{len(ordered)} works -> {OUT.relative_to(ROOT)}", file=sys.stderr)
