#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — regenerates every derived file in this repository.

Single source of truth:  StudentRadios_MYAEGEAN_project.json
Curated extras:          export-meta.json   (list order, ScreamerRadio ids/tags,
                                             Kodi country codes)

Run it after editing either of those two files:

    python build.py

Outputs (all overwritten, never hand-edit them):

    export-formats/M3U_studentradios.m3u
    export-formats/PLS_studentradios.pls
    export-formats/XSPF_studentradios.xspf
    export-formats/ADDTO__kodi.m3u
    export-formats/ADDTO__rhythmdb.xml
    export-formats/ADDTO__ScreamerRadio.json
    map/stations.js

Python 3.6+, standard library only.
"""

import json
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "StudentRadios_MYAEGEAN_project.json")
META = os.path.join(HERE, "export-meta.json")
EXPORTS = os.path.join(HERE, "export-formats")
MAP = os.path.join(HERE, "map")

GROUP_TITLE = "Greek University Radios"


def load():
    with open(DATA, encoding="utf-8") as fh:
        project = json.load(fh)
    with open(META, encoding="utf-8") as fh:
        meta = json.load(fh)

    stations = project["stations"]
    order = {alias: i for i, alias in enumerate(meta)}
    unknown = [s["station_alias"] for s in stations if s["station_alias"] not in order]
    if unknown:
        sys.exit(
            "export-meta.json has no entry for: %s\n"
            "Add one (order matters - it is the listing order of every export)."
            % ", ".join(unknown)
        )
    stations.sort(key=lambda s: order[s["station_alias"]])
    return project, meta, stations


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("  wrote %s (%d bytes)" % (os.path.relpath(path, HERE), len(text.encode("utf-8"))))


# --------------------------------------------------------------------------- #
# playlist formats
# --------------------------------------------------------------------------- #

def build_m3u(stations):
    out = ["#EXTM3U"]
    for s in stations:
        out.append("#EXTINF:-1,%s" % s["station_name"])
        out.append(s["stream_URI"])
        out.append("")
    return "\n".join(out)


def build_pls(stations):
    out = ["[playlist]", ""]
    for i, s in enumerate(stations, 1):
        out.append("File%d=%s" % (i, s["stream_URI"]))
        out.append("Title%d=%s" % (i, s["station_name"]))
        out.append("Length%d=-1" % i)
        out.append("")
    out.append("NumberOfEntries=%d" % len(stations))
    out.append("Version=2")
    out.append("")
    return "\n".join(out)


def build_xspf(stations):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<playlist version="1" xmlns="http://xspf.org/ns/0/">',
           "\t<trackList>",
           "\t"]
    for s in stations:
        out.append("\t\t<track>")
        out.append("\t\t\t<title>%s</title>" % escape(s["station_name"]))
        out.append("\t\t\t<location>%s</location>" % escape(s["stream_URI"]))
        out.append("\t\t</track>")
        out.append("\t")
    out.append("\t</trackList>")
    out.append("</playlist>")
    out.append("")
    return "\n".join(out)


def build_kodi(stations, meta):
    out = ["#EXTM3U"]
    for s in stations:
        m = meta[s["station_alias"]]
        out.append(
            '#EXTINF:-1 radio="true" tvg-country="%s" group-title="%s" tvg-logo="%s",%s'
            % (m.get("kodi_country") or "GR",
               m.get("kodi_group") or GROUP_TITLE,
               s["logotype"],
               s["station_name"])
        )
        out.append(s["stream_URI"])
        out.append("")
    return "\n".join(out)


def build_rhythmdb(stations):
    out = ['<?xml version="1.0" standalone="yes"?>',
           '<rhythmdb version="2.0">',
           ""]
    for s in stations:
        out.append('<entry type="iradio">')
        out.append("\t<title>%s</title>" % escape(s["station_name"]))
        out.append("\t<genre>College Radio</genre>")
        out.append("\t<location>%s</location>" % escape(s["stream_URI"]))
        out.append("\t<media-type>application/octet-stream</media-type>")
        out.append("  </entry>")
        out.append("  ")
        out.append("")
    out.append("</rhythmdb>")
    out.append("")
    return "\n".join(out)


def build_screamer(stations, meta):
    entries = []
    for s in stations:
        m = meta[s["station_alias"]]
        entries.append({
            "id": m["screamer_id"],
            "title": s["station_name"],
            "websiteUrl": m.get("screamer_websiteUrl") or s["website_URI"],
            "tags": m.get("screamer_tags") or ["University", "College", "StudentRadio"],
            "sources": [s["stream_URI"]],
        })
    return json.dumps(entries, ensure_ascii=False, indent=2) + "\n"


# --------------------------------------------------------------------------- #
# map data mirror
# --------------------------------------------------------------------------- #

def build_stations_js(project):
    return (
        "/* GENERATED FILE - do not edit. Run  python build.py  instead.\n"
        " *\n"
        " * map/index.html fetches ../StudentRadios_MYAEGEAN_project.json when it is\n"
        " * served over http(s). Browsers block that fetch under the file:// protocol,\n"
        " * so the page falls back to this script, which assigns the same object.\n"
        " * That is what lets the map be previewed by double-clicking index.html.\n"
        " */\n"
        "window.STATION_DATA = %s;\n" % json.dumps(project, ensure_ascii=False, indent=2)
    )


# --------------------------------------------------------------------------- #

def main():
    project, meta, stations = load()
    print("%d stations, snapshot generated %s"
          % (len(stations), project.get("generated_Time")))

    os.path.isdir(EXPORTS) or os.makedirs(EXPORTS)
    os.path.isdir(MAP) or os.makedirs(MAP)

    write(os.path.join(EXPORTS, "M3U_studentradios.m3u"), build_m3u(stations))
    write(os.path.join(EXPORTS, "PLS_studentradios.pls"), build_pls(stations))
    write(os.path.join(EXPORTS, "XSPF_studentradios.xspf"), build_xspf(stations))
    write(os.path.join(EXPORTS, "ADDTO__kodi.m3u"), build_kodi(stations, meta))
    write(os.path.join(EXPORTS, "ADDTO__rhythmdb.xml"), build_rhythmdb(stations))
    write(os.path.join(EXPORTS, "ADDTO__ScreamerRadio.json"), build_screamer(stations, meta))
    write(os.path.join(MAP, "stations.js"), build_stations_js(project))

    print("done.")


if __name__ == "__main__":
    main()
