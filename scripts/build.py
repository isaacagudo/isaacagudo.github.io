#!/usr/bin/env python3
"""Generate the site from data/*.json.

Outputs, all at the site root:
  index.html, index.md            the human page and its Markdown twin
  publications/<id>/index.html    one page per publication (with citation_* tags)
  publications/<id>/index.md      its Markdown twin
  llms.txt, llms-full.txt         entry points for language models
  publications.json, patents.json CSL-JSON data
  publications.bib                BibTeX for publications and patents
  sitemap.xml, robots.txt

Standard library only. Run: python3 scripts/build.py
"""
import datetime
import html
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://isaacagudo.github.io"
TODAY = datetime.date.today()

profile = json.loads((ROOT / "data/profile.json").read_text())
works = [w for w in json.loads((ROOT / "data/works.json").read_text())
         if not w.get("custom", {}).get("hidden") and w["type"] != "thesis"]
patents = json.loads((ROOT / "data/patents.json").read_text())
PERSON_ID = f"{SITE}/#person"
ME = {"Agudo", "Agudo Ruiz"}

TYPE_LABEL = {
    "article-journal": "Journal article",
    "paper-conference": "Conference paper",
    "chapter": "Book chapter",
    "book": "Edited volume",
    "thesis": "PhD thesis",
    "article-magazine": "Magazine article",
    "article": "Preprint",
    "patent": "Patent",
}
SCHEMA_TYPE = {
    "article-journal": "ScholarlyArticle",
    "paper-conference": "ScholarlyArticle",
    "chapter": "Chapter",
    "book": "Book",
    "thesis": "Thesis",
    "article-magazine": "Article",
    "article": "ScholarlyArticle",
}
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

e = html.escape


# --- formatting helpers -------------------------------------------------------

def year(w):
    return (w.get("issued") or {}).get("date-parts", [[None]])[0][0]


def iso(dp):
    if not dp:
        return None
    parts = dp.get("date-parts", [[None]])[0]
    return "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts) if p)


def pname(p):
    return p.get("literal") or f"{p.get('given', '')} {p.get('family', '')}".strip()


def is_me(p):
    return p.get("family") in ME and p.get("given", "").startswith("Isaac")


def names_html(people):
    out = [f'<span class="me">{e(pname(p))}</span>' if is_me(p) else e(pname(p)) for p in people or []]
    return ", ".join(out)


def names_text(people):
    return ", ".join(pname(p) for p in people or [])


def pages(w):
    pg = (w.get("page") or "").replace("--", "-")
    return "" if pg in ("1", "0") else pg.replace("-", "–")


def venue_parts(w):
    """Return (lead, container, rest) describing where a work appeared."""
    t, ct = w["type"], w.get("container-title")
    rest = []
    if t == "article-journal":
        vol = w.get("volume", "")
        if vol and w.get("issue"):
            vol += f"({w['issue']})"
        if vol:
            rest.append(vol)
        if pages(w):
            rest.append(pages(w))
    elif t in ("paper-conference", "chapter"):
        if t == "chapter" and w.get("editor"):
            rest.append(f"edited by {names_text(w['editor'])}")
        if w.get("publisher") and t == "chapter":
            rest.append(w["publisher"])
        if pages(w):
            rest.append(f"pp. {pages(w)}")
    elif t == "book":
        if w.get("publisher"):
            rest.append(w["publisher"])
    elif t == "thesis":
        return ("PhD thesis, " + w.get("publisher", "University of Málaga"), "", [])
    elif t == "article" and w.get("number"):
        rest.append(f"Paper {w['number']}")
    lead = {"article-journal": "Journal article in", "paper-conference": "Conference paper in",
            "chapter": "Chapter in", "book": "Edited volume in", "article-magazine": "Magazine article in",
            "article": "Preprint in"}[t]
    if t == "book":
        ct = w.get("container-title")
    if not ct:
        lead = TYPE_LABEL[t]
    return (lead, ct or "", rest)


def venue_html(w, with_year=True):
    lead, ct, rest = venue_parts(w)
    s = e(lead)
    if ct:
        s += f" <cite>{e(ct)}</cite>"
    if rest:
        s += ", " + ", ".join(e(r) for r in rest)
    if with_year and year(w):
        s += f", {year(w)}"
    return s + "."


def venue_text(w, with_year=True):
    lead, ct, rest = venue_parts(w)
    s = lead + (f" *{ct}*" if ct else "")
    if rest:
        s += ", " + ", ".join(rest)
    if with_year and year(w):
        s += f", {year(w)}"
    return s + "."


def links(w):
    out = []
    if w.get("DOI"):
        out.append(("DOI " + w["DOI"], f"https://doi.org/{w['DOI']}"))
    if not w.get("DOI") and w.get("URL"):
        out.append(("ePrint " + w["number"] if "eprint.iacr.org" in w["URL"] else "Source", w["URL"]))
    oa = w.get("custom", {}).get("oa_url")
    if oa and (not w.get("DOI") or w["DOI"] not in oa):
        out.append(("PDF" if oa.lower().endswith(".pdf") else "Open-access copy", oa))
    return out


def work_url(w):
    return f"{SITE}/publications/{w['id']}/"


def date_long(s):
    y, m, d = (int(x) for x in s.split("-"))
    return f"{d} {MONTHS[m - 1]} {y}"


# --- BibTeX -------------------------------------------------------------------

BIB_TYPE = {"article-journal": "article", "paper-conference": "inproceedings", "chapter": "incollection",
            "book": "proceedings", "thesis": "phdthesis", "article-magazine": "article", "article": "misc",
            "patent": "patent"}


def bib_escape(s):
    return s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")


def bibtex(w):
    t = w["type"]
    f = {}
    f["title"] = "{" + bib_escape(w["title"]) + "}"
    if w.get("author"):
        f["author"] = " and ".join(
            p.get("literal") or f"{p.get('family', '')}, {p.get('given', '')}".strip(", ") for p in w["author"])
    if w.get("editor"):
        f["editor"] = " and ".join(f"{p.get('family', '')}, {p.get('given', '')}".strip(", ") for p in w["editor"])
    ct = w.get("container-title")
    if ct:
        key = {"article-journal": "journal", "article-magazine": "journal", "paper-conference": "booktitle",
               "chapter": "booktitle", "book": "series"}.get(t, "howpublished")
        f[key] = bib_escape(ct)
    for k in ("volume", "number", "publisher"):
        src = "issue" if k == "number" else k
        if w.get(src):
            f[k] = bib_escape(str(w[src]))
    if w.get("page"):
        f["pages"] = w["page"].replace("–", "--").replace("-", "--").replace("----", "--")
    if t == "thesis":
        f["school"] = w.get("publisher", "")
    if t == "article" and w.get("number") and ct:
        f["howpublished"] = bib_escape(f"{ct}, Paper {w['number']}")
        f["url"] = w.get("URL", "")
    if t == "patent":
        f["number"] = w["number"]
        f["holder"] = w["custom"]["assignee"]
        f["url"] = w["URL"]
    if year(w):
        f["year"] = str(year(w))
    if w.get("DOI"):
        f["doi"] = w["DOI"]
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in f.items() if v)
    return f"@{BIB_TYPE.get(t, 'misc')}{{{w['id']},\n{body}\n}}"


# --- JSON-LD ------------------------------------------------------------------

def person_ld(p):
    if is_me(p):
        return {"@id": PERSON_ID}
    return {"@type": "Person", "name": pname(p)}


def work_ld(w):
    t = SCHEMA_TYPE.get(w["type"], "CreativeWork")
    d = {"@type": t, "@id": work_url(w) + "#work", "url": work_url(w), "name": w["title"], "headline": w["title"][:110]}
    if w.get("author"):
        d["author"] = [person_ld(p) for p in w["author"]]
    if w.get("editor"):
        d["editor"] = [person_ld(p) for p in w["editor"]]
    if iso(w.get("issued")):
        d["datePublished"] = iso(w["issued"])
    ct = w.get("container-title")
    if ct:
        part = {"article-journal": "Periodical", "article-magazine": "Periodical", "chapter": "Book",
                "paper-conference": "Book", "book": "BookSeries"}.get(w["type"], "CreativeWork")
        d["isPartOf"] = {"@type": part, "name": ct}
        if w["type"] == "article-journal" and w.get("volume"):
            d["isPartOf"] = {"@type": "PublicationVolume", "volumeNumber": w["volume"],
                             "isPartOf": {"@type": "Periodical", "name": ct}}
    if w.get("publisher"):
        d["publisher"] = {"@type": "Organization", "name": w["publisher"]}
    if w.get("page"):
        d["pagination"] = w["page"]
    if w.get("DOI"):
        d["identifier"] = {"@type": "PropertyValue", "propertyID": "DOI", "value": w["DOI"]}
        d["sameAs"] = f"https://doi.org/{w['DOI']}"
    elif w.get("URL"):
        d["sameAs"] = w["URL"]
        if w.get("number"):
            d["identifier"] = {"@type": "PropertyValue", "propertyID": "IACR ePrint", "value": w["number"]}
            d["creativeWorkStatus"] = "Preprint"
    if w.get("abstract"):
        d["abstract"] = w["abstract"]
    d["inLanguage"] = w.get("language", "en")
    if w["type"] == "thesis":
        d["inSupportOf"] = "PhD in Computer Science"
        d["sourceOrganization"] = {"@type": "CollegeOrUniversity", "name": w.get("publisher", "")}
    oa = w.get("custom", {}).get("oa_url")
    if oa:
        d["isAccessibleForFree"] = True
        d["encoding"] = {"@type": "MediaObject", "contentUrl": oa}
    return d


def patent_ld(p):
    c = p["custom"]
    return {
        "@type": "CreativeWork",
        "@id": f"{SITE}/#{p['id']}",
        "additionalType": "https://www.wikidata.org/wiki/Q253623",
        "genre": "patent",
        "name": p["title"],
        "creator": [person_ld(a) for a in p["author"]],
        "identifier": [{"@type": "PropertyValue", "propertyID": "patent publication number", "value": f["number"]}
                       for f in c["family"]],
        "sameAs": [f["url"] for f in c["family"]],
        "dateCreated": c["family"][0].get("filed"),
        "datePublished": c["family"][0].get("granted") or c["family"][0].get("published"),
        "sourceOrganization": {"@type": "Organization", "name": c["assignee"]},
        "creativeWorkStatus": c["status"],
        "abstract": p["abstract"],
        "url": p["URL"],
    }


def person_full_ld():
    pr = profile
    uni = {"@type": "CollegeOrUniversity", "@id": f"{SITE}/#uma", "name": pr["university"]["name"],
           "alternateName": pr["university"]["alternateName"], "url": pr["university"]["url"]}
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": pr["name"],
        "alternateName": pr["alternateName"],
        "givenName": pr["givenName"],
        "familyName": pr["familyName"],
        "url": pr["url"],
        "description": pr["summary"],
        "jobTitle": pr["jobTitle"],
        "worksFor": uni,
        "affiliation": [
            {"@type": "ResearchOrganization", "name": pr["lab"]["name"], "alternateName": pr["lab"]["alternateName"],
             "url": pr["lab"]["url"], "parentOrganization": {"@id": f"{SITE}/#uma"}},
            {"@type": "Organization", "@id": f"{SITE}/#company", "name": pr["company"]["name"],
             "url": pr["company"]["url"], "founder": {"@id": PERSON_ID},
             "sameAs": [pr["company"]["github"]]},
        ],
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": ed["institution"]} for ed in pr["education"]],
        "knowsAbout": pr["knowsAbout"],
        "identifier": [
            {"@type": "PropertyValue", "propertyID": "ORCID", "value": pr["identifiers"]["orcid"]},
            {"@type": "PropertyValue", "propertyID": "Scopus Author ID", "value": pr["identifiers"]["scopus"]},
            {"@type": "PropertyValue", "propertyID": "ResearcherID", "value": pr["identifiers"]["researcherid"]},
            {"@type": "PropertyValue", "propertyID": "DBLP", "value": pr["identifiers"]["dblp"]},
        ],
        "sameAs": [x["url"] for x in pr["profiles"]],
    }


def jsonld_script(obj):
    s = json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{s}\n</script>'


# --- PhD supervision -----------------------------------------------------------

def sup_when(t):
    parts = t["date"].split("-")
    if len(parts) == 3:
        return date_long(t["date"])
    return f"{MONTHS[int(parts[1]) - 1]} {parts[0]}" if len(parts) == 2 else parts[0]


def supervision_li(t):
    co = f" Co-supervised with {', '.join(t['co_supervisors'])}." if t.get("co_supervisors") else ""
    aw = f" {'; '.join(t['awards'])}." if t.get("awards") else ""
    return f"""<li class="patent thesis">
          <h3 class="w-title"><a href="{e(t['url'])}">{e(t['title'])}</a></h3>
          <span class="w-authors">{e(t['student'])}</span>
          <span class="w-venue">PhD thesis, {e(t['university'])}, defended {e(sup_when(t))}.{e(co)}{e(aw)}</span>
        </li>"""


def supervision_ld(t):
    d = {"@type": "Thesis", "name": t["title"], "author": {"@type": "Person", "name": t["student"]},
         "inSupportOf": "PhD", "datePublished": t["date"], "url": t["url"], "inLanguage": t.get("language", "en"),
         "sourceOrganization": {"@type": "CollegeOrUniversity", "name": t["university"]},
         "contributor": [{"@type": "Role", "roleName": "PhD supervisor", "contributor": {"@id": PERSON_ID}}]
         + [{"@type": "Role", "roleName": "PhD supervisor", "contributor": {"@type": "Person", "name": n}}
            for n in t.get("co_supervisors", [])]}
    if t.get("awards"):
        d["award"] = t["awards"]
    return d


def supervision_md():
    out = ["## PhD theses supervised", ""]
    for t in profile.get("supervision", []):
        co = f", co-supervised with {', '.join(t['co_supervisors'])}" if t.get("co_supervisors") else ""
        aw = f". Awards: {'; '.join(t['awards'])}" if t.get("awards") else ""
        out.append(f"- {t['student']}, *{t['title']}*, {t['university']}, defended {sup_when(t)}{co}{aw}. {t['url']}")
    return "\n".join(out) + "\n"


# --- HTML ---------------------------------------------------------------------

def head(title, description, path, extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="author" content="{e(profile['name'])}">
  <meta name="theme-color" content="#F7FAFA">
  <link rel="canonical" href="{SITE}{path}">
  <link rel="alternate" type="text/markdown" href="{SITE}{path}index.md" title="Markdown version">
  <link rel="alternate" type="text/plain" href="{SITE}/llms.txt" title="llms.txt">
  <link rel="preload" href="/fonts/petrona-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/assets/site.css">
{extra}</head>"""


def footer():
    month = f"{MONTHS[TODAY.month - 1]} {TODAY.year}"
    prof = " ".join(f'<a href="{e(x["url"])}">{e(x["name"])}</a>' for x in profile["profiles"])
    return f"""  <footer class="site-footer">
    <nav aria-label="Research profiles" class="profiles">{prof}</nav>
    <p>© {TODAY.year} {e(profile['name'])}. Last updated <time datetime="{TODAY.isoformat()}">{month}</time>.</p>
  </footer>"""


def short_venue(w):
    """A compact venue label for the one-line row."""
    if w["type"] == "thesis":
        return "PhD thesis"
    ct = w.get("container-title") or ""
    m = re.search(r"\(([^()]{2,20})\)\s*$", ct)
    if m:
        return m.group(1)
    ct = re.sub(r"^Proceedings of the\s+", "", ct)
    ct = re.sub(r"^\d{4}\s+", "", ct)
    ct = re.sub(r"^(IEEE\s+)?\d+(st|nd|rd|th)\s+", r"\1", ct)
    return ct or TYPE_LABEL[w["type"]]


def work_li(w, with_year=True, id_prefix=""):
    """One publication as a single-line row that opens to show the details."""
    lk = [f'<a href="/publications/{w["id"]}/">Publication page</a>']
    lk += [f'<a href="{e(u)}">{e(t)}</a>' for t, u in links(w)]
    lang = f' lang="{w["language"]}"' if w.get("language") and w["language"] != "en" else ""
    sv = short_venue(w)
    meta = sv + (f", {year(w)}" if with_year and year(w) and str(year(w)) not in sv else "")
    eds = " (eds.)" if not w.get("author") and w.get("editor") else ""
    abstract = (f'<p class="w-abstract"{lang}>{e(w["abstract"])}</p>' if w.get("abstract")
                else '<p class="w-abstract none">No abstract available.</p>')
    return f"""<li class="work" id="{id_prefix}{w['id']}">
          <details>
            <summary><span class="w-title"{lang}>{e(w['title'])}</span><span class="w-meta">{e(meta)}</span></summary>
            <div class="w-body">
              <p class="w-authors">{names_html(w.get('author') or w.get('editor'))}{eds}</p>
              <p class="w-venue">{venue_html(w)}</p>
              {abstract}
              <p class="w-links">{' '.join(lk)}</p>
            </div>
          </details>
        </li>"""


def patent_li(p):
    """One patent family as a single-line row, like the publications."""
    c = p["custom"]
    fam = []
    for f in c["family"]:
        when = []
        if f.get("filed"):
            when.append(f"filed {date_long(f['filed'])}")
        if f.get("granted"):
            when.append(f"granted {date_long(f['granted'])}")
        elif f.get("published"):
            when.append(f"published {date_long(f['published'])}")
        fam.append(f'<li><a href="{e(f["url"])}">{e(f["number"])}</a>, {e(f["label"])}'
                   f'{", " + ", ".join(when) if when else ""}.</li>')
    meta = f"{p['number']}, {year(p)}"
    return f"""<li class="work" id="{p['id']}">
          <details>
            <summary><span class="w-title">{e(p['title'])}</span><span class="w-meta">{e(meta)}</span></summary>
            <div class="w-body">
              <p class="w-authors">{names_html(p['author'])}</p>
              <p class="w-venue">{e(c['status'])}. Applicant: {e(c['assignee'].rstrip('.'))}.</p>
              <ul class="family">{''.join(fam)}</ul>
              <p class="w-abstract">{e(p['abstract'])}</p>
            </div>
          </details>
        </li>"""


def build_index():
    pr = profile
    selected = [w for w in works if w.get("custom", {}).get("selected")]
    english = [w for w in works if w.get("language", "en") != "es"]
    spanish = [w for w in works if w.get("language") == "es"]
    by_year = {}
    for w in english:
        by_year.setdefault(year(w) or 0, []).append(w)
    years_html = []
    for y in sorted(by_year, reverse=True):
        items = "\n        ".join(work_li(w, with_year=False) for w in by_year[y])
        years_html.append(f"""<section class="year" aria-labelledby="y{y}">
      <h3 id="y{y}" class="year-label">{y or 'Undated'}</h3>
      <ol class="works">
        {items}
      </ol>
    </section>""")
    research = "\n".join(
        f'      <div class="line"><dt>{e(r["name"])}</dt><dd>{e(r["text"])}</dd></div>' for r in pr["research"])
    edu = "\n".join(f'      <li>{e(ed["degree"])}, {e(ed["institution"])}, {ed["year"]}.'
                     + (f' Thesis: <cite lang="es">{e(ed["thesis"])}</cite>.' if ed.get("thesis") else "") + '</li>'
                     for ed in pr["education"])
    counts = {}
    for w in english:
        counts[w["type"]] = counts.get(w["type"], 0) + 1
    spanish_html = "\n        ".join(work_li(w) for w in spanish)
    graph = {"@context": "https://schema.org", "@graph": [
        {"@type": "ProfilePage", "@id": f"{SITE}/#page", "url": f"{SITE}/", "name": pr["name"],
         "mainEntity": {"@id": PERSON_ID}, "dateModified": TODAY.isoformat(), "inLanguage": "en"},
        person_full_ld(),
        *[work_ld(w) for w in works],
        *[patent_ld(p) for p in patents],
        *[supervision_ld(t) for t in pr.get("supervision", [])],
    ]}
    desc = f"{pr['name']}: {pr['summary']} Publications, patents and research lines."
    page = f"""{head(pr['name'] + ' · Applied cryptography, University of Málaga', desc, '/', '  ' + jsonld_script(graph) + chr(10))}
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <a class="home" href="/">{e(pr['name'])}</a>
    <nav aria-label="Sections">
      <a href="#research">Research</a>
      <a href="#publications">Publications</a>
      <a href="#patents">Patents</a>
      <a href="#data">Data</a>
    </nav>
  </header>
  <main id="main">
    <div class="intro">
      <h1>{e(pr['name'])}</h1>
      <p class="lede">{e(pr['lede']).replace('NICS Lab', '<a href="' + pr['lab']['url'] + '">NICS Lab</a>').replace('Decentralized Security', '<a href="' + pr['company']['url'] + '">Decentralized Security</a>')}</p>
      <nav class="hero-links" aria-label="Profiles">{' '.join(f'<a href="{e(x["url"])}">{e(x["label"])}</a>' for x in pr.get('hero_links', []))}</nav>
    </div>

    <section class="block" id="research" aria-labelledby="research-h">
      <h2 id="research-h">Research</h2>
      <dl class="lines">
{research}
      </dl>
    </section>

    <section class="block" id="publications" aria-labelledby="pub-h">
      <h2 id="pub-h">Selected publications</h2>
      <ol class="works">
        {chr(10).join('        ' + work_li(w, id_prefix="selected-") for w in selected).strip()}
      </ol>
    </section>

    <section class="block" id="patents" aria-labelledby="pat-h">
      <h2 id="pat-h">Patents</h2>
      <ol class="works">
        {chr(10).join('        ' + patent_li(p) for p in patents).strip()}
      </ol>
    </section>

    <section class="block" id="supervision" aria-labelledby="sup-h">
      <h2 id="sup-h">PhD supervision</h2>
      <ol class="works patents">
        {chr(10).join('        ' + supervision_li(t) for t in pr.get('supervision', [])).strip()}
      </ol>
    </section>

    <section class="block" id="all" aria-labelledby="all-h">
      <h2 id="all-h">All publications</h2>
      <p class="count">{len(english)} publications in English: {counts.get('article-journal', 0)} journal articles, {counts.get('paper-conference', 0)} conference papers, {counts.get('chapter', 0)} book chapters, {counts.get('book', 0)} edited volumes, {counts.get('article-magazine', 0)} magazine article{'s' if counts.get('article-magazine', 0) != 1 else ''} and {counts.get('article', 0)} preprint{'s' if counts.get('article', 0) != 1 else ''}. Open any entry to read its abstract.</p>
    {chr(10).join('    ' + y for y in years_html).strip()}
    </section>

    <section class="block" id="spanish" aria-label="Publications in Spanish" lang="en">
      <details class="lang-group">
        <summary><h2>Publications in Spanish</h2><span class="w-meta">{len(spanish)}</span></summary>
        <ol class="works">
        {spanish_html}
        </ol>
      </details>
    </section>

    <section class="block" id="education" aria-labelledby="edu-h">
      <h2 id="edu-h">Education</h2>
      <ul class="plain">
{edu}
      </ul>
    </section>

    <section class="block data-note" id="data" aria-labelledby="data-h">
      <h2 id="data-h">Readable by people and by machines</h2>
      <p>Every publication and patent on this page is also published as structured data for citation managers, search engines and AI assistants: <a href="/llms.txt">llms.txt</a>, <a href="/llms-full.txt">llms-full.txt</a> with every abstract in one file, <a href="/publications.bib">BibTeX</a>, and CSL-JSON for <a href="/publications.json">publications</a> and <a href="/patents.json">patents</a>.</p>
    </section>
  </main>
{footer()}
</body>
</html>
"""
    (ROOT / "index.html").write_text(page)


def citation_meta(w):
    m = [("citation_title", w["title"])]
    for p in w.get("author") or []:
        m.append(("citation_author", pname(p)))
    if w.get("issued"):
        m.append(("citation_publication_date", iso(w["issued"]).replace("-", "/")))
    ct = w.get("container-title")
    key = {"article-journal": "citation_journal_title", "article-magazine": "citation_journal_title",
           "paper-conference": "citation_conference_title", "chapter": "citation_inbook_title"}.get(w["type"])
    if ct and key:
        m.append((key, ct))
    if w["type"] == "thesis":
        m.append(("citation_dissertation_institution", w.get("publisher", "")))
    for k, ck in (("volume", "citation_volume"), ("issue", "citation_issue"), ("publisher", "citation_publisher")):
        if w.get(k):
            m.append((ck, str(w[k])))
    if w.get("page"):
        pg = re.split(r"[-–]+", w["page"])
        m.append(("citation_firstpage", pg[0]))
        if len(pg) > 1:
            m.append(("citation_lastpage", pg[-1]))
    if w.get("DOI"):
        m.append(("citation_doi", w["DOI"]))
    oa = w.get("custom", {}).get("oa_url", "")
    if oa.lower().endswith(".pdf"):
        m.append(("citation_pdf_url", oa))
    m.append(("citation_abstract_html_url", work_url(w)))
    m.append(("citation_language", w.get("language", "en")))
    return "\n".join(f'  <meta name="{k}" content="{e(v)}">' for k, v in m) + "\n"


def build_work_pages():
    out = ROOT / "publications"
    if out.exists():
        shutil.rmtree(out)
    for w in works:
        d = out / w["id"]
        d.mkdir(parents=True)
        ld = {"@context": "https://schema.org", "@graph": [work_ld(w), person_full_ld()]}
        lang = f' lang="{w["language"]}"' if w.get("language") and w["language"] != "en" else ""
        abstract = (f'<section class="abstract" aria-labelledby="abs-h"><h2 id="abs-h">Abstract</h2>'
                    f'<p{lang}>{e(w["abstract"])}</p></section>') if w.get("abstract") else ""
        lk = "".join(f'<li><a href="{e(u)}">{e(t)}</a></li>' for t, u in links(w))
        desc = (w.get("abstract") or f"{w['title']}. {venue_text(w)}")[:300]
        page = f"""{head(w['title'] + ' · ' + profile['name'], desc, '/publications/' + w['id'] + '/', citation_meta(w) + '  ' + jsonld_script(ld) + chr(10))}
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <a class="home" href="/">{e(profile['name'])}</a>
    <nav aria-label="Sections">
      <a href="/#research">Research</a>
      <a href="/#publications">Publications</a>
      <a href="/#patents">Patents</a>
      <a href="/#data">Data</a>
    </nav>
  </header>
  <main id="main" class="paper">
    <p class="kind">{e(TYPE_LABEL[w['type']])}, {year(w) or ''}</p>
    <h1{lang}>{e(w['title'])}</h1>
    <p class="w-authors">{names_html(w.get('author') or w.get('editor'))}{' (eds.)' if not w.get('author') and w.get('editor') else ''}</p>
    <p class="w-venue">{venue_html(w)}</p>
    {f'<ul class="paper-links">{lk}</ul>' if lk else ''}
    {abstract}
    <section class="cite" aria-labelledby="cite-h">
      <h2 id="cite-h">Cite</h2>
      <pre><code>{e(bibtex(w))}</code></pre>
    </section>
    <p class="back"><a href="/#{w['id']}">All publications</a></p>
  </main>
{footer()}
</body>
</html>
"""
        (d / "index.html").write_text(page)
        (d / "index.md").write_text(work_md(w, heading="#"))


# --- Markdown -----------------------------------------------------------------

def work_md(w, heading="###"):
    lines = [f"{heading} {w['title']}", "",
             f"- Authors: {names_text(w.get('author') or w.get('editor'))}{' (eds.)' if not w.get('author') and w.get('editor') else ''}",
             f"- Type: {TYPE_LABEL[w['type']]}",
             f"- Language: {'Spanish' if w.get('language') == 'es' else 'English'}",
             f"- Venue: {venue_text(w, with_year=False)}"]
    if year(w):
        lines.append(f"- Year: {year(w)}")
    if w.get("DOI"):
        lines.append(f"- DOI: [{w['DOI']}](https://doi.org/{w['DOI']})")
    if w.get("custom", {}).get("oa_url"):
        lines.append(f"- Open-access copy: {w['custom']['oa_url']}")
    lines.append(f"- Page: {work_url(w)}")
    if w.get("abstract"):
        lines += ["", f"Abstract: {w['abstract']}"]
    return "\n".join(lines) + "\n"


def patent_md(p, heading="###"):
    c = p["custom"]
    lines = [f"{heading} {p['title']}", "",
             f"- Inventors: {names_text(p['author'])}",
             f"- Applicant: {c['assignee']}",
             f"- Status: {c['status']}",
             f"- Priority date: {c['priority_date']}"]
    for f in c["family"]:
        bits = [f["label"]]
        for k in ("filed", "published", "granted"):
            if f.get(k):
                bits.append(f"{k} {f[k]}")
        lines.append(f"- {f['number']} ({', '.join(bits)}): {f['url']}")
    lines += ["", f"Abstract: {p['abstract']}"]
    return "\n".join(lines) + "\n"


def profile_md():
    pr = profile
    out = [f"# {pr['name']}", "", f"> {pr['summary']}", "", pr["lede"], "",
           "## Key facts", "",
           f"- Name: {pr['name']} (full name {pr['alternateName']})",
           f"- Position: {pr['jobTitle']}, {pr['department']}, {pr['university']['name']}",
           f"- Research group: [{pr['lab']['name']}]({pr['lab']['url']}) ({pr['lab']['alternateName']})",
           f"- Company: founder of [{pr['company']['name']}]({pr['company']['url']}), code at {pr['company']['github']}",
           f"- ORCID: [{pr['identifiers']['orcid']}](https://orcid.org/{pr['identifiers']['orcid']})",
           f"- Topics: {', '.join(pr['knowsAbout'])}", "",
           "## Research lines", ""]
    out += [f"- **{r['name']}**: {r['text']}" for r in pr["research"]]
    out += ["", "## Education", ""] + [f"- {ed['degree']}, {ed['institution']}, {ed['year']}"
                                       + (f". Thesis (in Spanish): *{ed['thesis']}*" if ed.get("thesis") else "")
                                       for ed in pr["education"]]
    out += [""] + supervision_md().rstrip("\n").split("\n")
    out += ["", "## Profiles", ""] + [f"- [{x['name']}]({x['url']})" for x in pr["profiles"]]
    return "\n".join(out) + "\n"


def build_markdown():
    selected = [w for w in works if w.get("custom", {}).get("selected")]
    idx = profile_md() + "\n## Selected publications\n\n"
    idx += "\n".join(f"- [{w['title']}]({work_url(w)}index.md). {names_text(w.get('author'))}. {venue_text(w)}"
                     for w in selected)
    idx += "\n\n## Patents\n\n" + "\n".join(
        f"- {p['title']}. {', '.join(f['number'] for f in p['custom']['family'])}. {p['custom']['status']}."
        for p in patents)
    idx += f"\n\nThe full list of {len(works)} publications, with abstracts, is in [llms-full.txt]({SITE}/llms-full.txt).\n"
    (ROOT / "index.md").write_text(idx)

    full = profile_md() + "\n## Patents\n\n" + "\n".join(patent_md(p) for p in patents)
    full += "\n## Publications\n\nNewest first.\n\n" + "\n".join(work_md(w) for w in works)
    (ROOT / "llms-full.txt").write_text(full)

    pr = profile
    llms = [f"# {pr['name']}", "", f"> {pr['summary']}", "",
            f"{pr['name']} ({pr['alternateName']}) works on applied cryptography: secure multi-party computation, "
            "proxy re-encryption, secret sharing, and their use in blockchain, connected vehicles and digital identity. "
            f"This site lists {len(works)} publications, {len(patents)} patent families and "
            f"{len(profile.get('supervision', []))} supervised PhD theses. "
            f"ORCID {pr['identifiers']['orcid']}.", "",
            "## Profile", "",
            f"- [Profile in Markdown]({SITE}/index.md): position, research lines, education and profile links",
            f"- [Everything in one file]({SITE}/llms-full.txt): profile, patents and every publication with its abstract",
            "", "## Data", "",
            f"- [publications.json]({SITE}/publications.json): all publications in CSL-JSON",
            f"- [patents.json]({SITE}/patents.json): patents in CSL-JSON, with family members and abstracts",
            f"- [publications.bib]({SITE}/publications.bib): BibTeX for publications and patents",
            "", "## Selected publications", ""]
    llms += [f"- [{w['title']}]({work_url(w)}index.md): {venue_text(w)}" for w in selected]
    llms += ["", "## Patents", ""]
    llms += [f"- {p['title']}: {', '.join(f['number'] for f in p['custom']['family'])} ({p['custom']['status'].lower()}, "
             f"applicant {p['custom']['assignee']})" for p in patents]
    llms += ["", "## Optional", ""]
    llms += [f"- [{w['title']}]({work_url(w)}index.md): {venue_text(w)}" for w in works if w not in selected]
    (ROOT / "llms.txt").write_text("\n".join(llms) + "\n")


# --- data files, sitemap, robots ----------------------------------------------

def build_data():
    def public(w):
        d = {k: v for k, v in w.items() if k != "custom"}
        d["URL"] = w.get("URL") or work_url(w)
        return d
    (ROOT / "publications.json").write_text(json.dumps([public(w) for w in works], ensure_ascii=False, indent=1) + "\n")
    pats = []
    for p in patents:
        d = dict(p)
        d["custom"] = {k: v for k, v in p["custom"].items()}
        pats.append(d)
    (ROOT / "patents.json").write_text(json.dumps(pats, ensure_ascii=False, indent=1) + "\n")
    (ROOT / "publications.bib").write_text(
        f"% Publications and patents of {profile['name']}\n% {SITE}/  (generated {TODAY.isoformat()})\n\n"
        + "\n\n".join(bibtex(w) for w in works + patents) + "\n")

    urls = [f"{SITE}/", f"{SITE}/llms.txt", f"{SITE}/llms-full.txt"] + [work_url(w) for w in works]
    sm = "\n".join(f"  <url><loc>{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}\n</urlset>\n')
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot",
            "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot"]
    robots = "# Everyone is welcome, including AI crawlers.\nUser-agent: *\nAllow: /\n\n"
    robots += "\n".join(f"User-agent: {b}" for b in bots) + "\nAllow: /\n\n"
    robots += f"Sitemap: {SITE}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(robots)


if __name__ == "__main__":
    build_index()
    build_work_pages()
    build_markdown()
    build_data()
    print(f"Built {len(works)} publication pages, {len(patents)} patents.")
