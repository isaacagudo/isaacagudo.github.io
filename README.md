# isaacagudo.github.io

Personal website of Isaac Agudo, published with GitHub Pages at <https://isaacagudo.github.io>.

The site is plain HTML and CSS with no build step on GitHub's side. Fonts are self-hosted in `fonts/` (Petrona and Hanken Grotesk, both under the SIL Open Font License).

## How it is made

The content lives in three data files:

- `data/profile.json`: position, research lines, education and profile links
- `data/works.json`: every publication, in CSL-JSON. Entries with `custom.hidden` are kept but not shown; `custom.selected` marks the selected publications
- `data/patents.json`: patent families, in CSL-JSON

`python3 scripts/build.py` regenerates everything else from them: the page itself, one page per publication, the Markdown versions, `llms.txt`, `llms-full.txt`, `publications.json`, `patents.json`, `publications.bib`, `sitemap.xml` and `robots.txt`. Commit the generated files together with the data.

`scripts/merge_sources.py` rebuilds `data/works.json` from a fresh import of ORCID, OpenAlex and Crossref. The import itself runs as a GitHub Action on the `data-import` branch.

## For machines

- `llms.txt` and `llms-full.txt` follow the [llms.txt](https://llmstxt.org) convention
- Every page carries schema.org JSON-LD, and every publication page carries the `citation_*` tags that Google Scholar reads
- Every HTML page has a Markdown twin at the same path, ending in `index.md`
