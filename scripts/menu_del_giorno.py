#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
menu_del_giorno.py — Legge il menu del giorno da riboscuola.it (menù scolastici di Bologna).

Estrae il menu di una scuola (default: DON MILANI PRIMARIA) per un dato giorno e
lo stampa in un formato adatto ad essere letto da Alexa / da OpenHAB.

Dipendenze: nessuna (solo libreria standard Python >= 3.9).

Esempi:
    ./menu_del_giorno.py                          # menu di oggi (testo)
    ./menu_del_giorno.py --tomorrow --format text
    ./menu_del_giorno.py --date 2026-11-10 --format json
    ./menu_del_giorno.py --format speech                    # testo parlato per Alexa
    ./menu_del_giorno.py --tomorrow --format text
    ./menu_del_giorno.py --date 2026-11-10 --format json
    ./menu_del_giorno.py --out /tmp/menu.txt --json-out /tmp/menu.json
    ./menu_del_giorno.py --list-schools
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

BASE_URL = "https://www.riboscuola.it/menu/ricerca-menu.aspx"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.35 riboscuola-menu-bot/1.0 (script per Alexa/OpenHAB)"
)
DEFAULT_SCHOOL = "DON MILANI PRIMARIA"
DEFAULT_DIET = "Menu Convenzionale"
DEFAULT_TZ = "Europe/Rome"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_MENU = 2
EXIT_AMBIGUOUS = 3


# --------------------------------------------------------------------------------------
# Mini parser HTML (tolerante): costruisce un albero di nodi. Il sito emette HTML
# leggermente malformato (tag </li> duplicati), quindi siamo tolleranti.
# --------------------------------------------------------------------------------------

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag: str, attrs: Optional[dict] = None, parent: Optional["Node"] = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children: List["Node"] = []
        self.parent = parent

    # --- utilità ---------------------------------------------------------------
    def get(self, key: str, default: str = "") -> str:
        return self.attrs.get(key, default)

    @property
    def classes(self) -> List[str]:
        return self.get("class").split()

    def has_class(self, name: str) -> bool:
        return name in self.classes

    def add_text(self, text: str) -> None:
        self.children.append(text)

    def append(self, node: "Node") -> None:
        self.children.append(node)

    def iter_nodes(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.iter_nodes()

    def find_all(self, tag: Optional[str] = None, cls: Optional[str] = None,
                 id_contains: Optional[str] = None, name: Optional[str] = None,
                 name_endswith: Optional[str] = None) -> List["Node"]:
        out = []
        for n in self.iter_nodes():
            if tag is not None and n.tag != tag:
                continue
            if cls is not None and not n.has_class(cls):
                continue
            if id_contains is not None and id_contains not in n.get("id"):
                continue
            if name is not None and n.get("name") != name:
                continue
            if name_endswith is not None and not n.get("name").endswith(name_endswith):
                continue
            out.append(n)
        return out

    def find(self, *args, **kwargs) -> Optional["Node"]:
        found = self.find_all(*args, **kwargs)
        return found[0] if found else None

    def text(self, sep: str = " ") -> str:
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif child.tag == "br":
                parts.append(" ")
            else:
                parts.append(child.text(sep))
        return normalize_ws(sep.join(parts))


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self.stack: List[Node] = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].append(Node(tag, dict(attrs), self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
        # tag di chiusura orfano / duplicato: ignoriamo

    def handle_data(self, data):
        if self.stack[-1].tag in SKIP_TEXT_TAGS:
            return
        if data.strip():
            self.stack[-1].add_text(data)


def parse_html(html: str) -> Node:
    builder = TreeBuilder()
    builder.feed(html)
    builder.close()
    return builder.root


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


# --------------------------------------------------------------------------------------
# Modello dati
# --------------------------------------------------------------------------------------

@dataclass
class Piatto:
    categoria: str                    # etichetta del sito: "Primi", "Secondi", ...
    nome: str
    ingredienti: str = ""
    allergeni: List[str] = field(default_factory=list)
    congelato: bool = False           # il nome contiene * / ** (prodotto congelato)
    marcature: List[str] = field(default_factory=list)  # es. da-scoprire, del-mese, rotazione

    def nome_pulito(self) -> str:
        """Nome leggibile: via spazi doppi, i `*` del congelato e i `..` di troppo."""
        nome = self.nome.replace("\u00a0", " ")
        nome = re.sub(r"\s+", " ", nome).strip()
        nome = re.sub(r"[\s.*]+$", "", nome).strip()
        return nome


@dataclass
class Menu:
    data: str                         # YYYY-MM-DD
    scuola: str = ""
    dieta: str = ""
    piatti: List[Piatto] = field(default_factory=list)
    pdf_url: str = ""
    note: str = ""
    richiesto: str = ""               # data chiesta, se diversa da quella trovata

    @property
    def vuoto(self) -> bool:
        return not self.piatti


# --------------------------------------------------------------------------------------
# Client verso riboscuola.it
# --------------------------------------------------------------------------------------

class FormFields:
    """Campi del form ASP.NET WebForms (nomi "dinamici" legati al modulo)."""

    def __init__(self, root: Node):
        self.select_school = root.find(name_endswith="$drpDestination")
        self.select_diet = root.find(name_endswith="$drpDiet")
        self.btn_search = root.find(name_endswith="$btnSearch")
        self.hdn_date = root.find(name_endswith="$hdnDate")
        self.btn_move_to_date = root.find(name_endswith="$btnMoveToDate")
        self.viewstate = self._hidden(root, "__VIEWSTATE")
        self.viewstate_generator = self._hidden(root, "__VIEWSTATEGENERATOR")
        self.eventvalidation = self._hidden(root, "__EVENTVALIDATION")

    @staticmethod
    def _hidden(root: Node, name: str) -> Optional[Node]:
        found = [n for n in root.find_all("input", name=name)]
        return found[-1] if found else None  # l'ultimo vince (come fa il browser)

    @property
    def ok(self) -> bool:
        return all(x is not None for x in (self.select_school, self.select_diet,
                                           self.btn_search, self.viewstate,
                                           self.viewstate_generator, self.eventvalidation))

    def options(self, which: str) -> List[Tuple[str, str]]:
        sel = self.select_school if which == "school" else self.select_diet
        if sel is None:
            return []
        out = []
        for opt in sel.find_all("option"):
            label = normalize_ws(opt.text())
            value = opt.get("value")
            if value:
                out.append((label, value))
        return out


class RiboscuolaError(RuntimeError):
    pass


class AmbiguousSelection(RiboscuolaError):
    """Il nome passato (--school / --diet) corrisponde a piu' voci."""


class RiboscuolaClient:
    def __init__(self, base_url: str = BASE_URL, timeout: float = 30.0,
                 retries: int = 3, user_agent: str = USER_AGENT):
        self.base_url = base_url
        self.timeout = timeout
        self.retries = max(1, retries)
        self.user_agent = user_agent
        self._opener = urllib.request.build_opener()
        self._opener.addheaders = [
            ("User-Agent", user_agent),
            ("Accept", "text/html,application/xhtml+xml"),
            ("Accept-Language", "it-IT,it;q=0.9"),
        ]

    # --- HTTP -------------------------------------------------------------------------
    def _request(self, req: urllib.request.Request) -> str:
        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                with self._opener.open(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                text = None
                for enc in ("utf-8", "windows-1254", "latin-1"):
                    try:
                        text = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                return text or raw.decode("utf-8", "replace")
            except (urllib.error.URLError, OSError, ValueError) as err:
                last_err = err
                if attempt < self.retries:
                    time.sleep(2.0 * attempt)
        raise RiboscuolaError(f"richiesta HTTP fallita verso {self.base_url}: {last_err}")

    def _get(self) -> str:
        return self._request(urllib.request.Request(self.base_url))

    def _post(self, data: Dict[str, str]) -> str:
        body = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(self.base_url, data=body, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": self.base_url,
            "Origin": urllib.parse.urlsplit(self.base_url).scheme + "://"
                      + urllib.parse.urlsplit(self.base_url).netloc,
        })
        return self._request(req)

    # --- API -------------------------------------------------------------------------
    def form(self) -> FormFields:
        fields = FormFields(parse_html(self._get()))
        if not fields.ok:
            raise RiboscuolaError(
                "non ho trovato i campi del form di ricerca: la pagina e' cambiata?")
        return fields

    def schools(self) -> List[Tuple[str, str]]:
        return self.form().options("school")

    def diets(self) -> List[Tuple[str, str]]:
        return self.form().options("diet")

    def menu(self, school_value: str, diet_value: str,
             when: Optional[date] = None, fields: Optional[FormFields] = None) -> Menu:
        """Scarica e interpreta il menu per la scuola/dieta indicati, per il giorno `when`."""
        return parse_menu(self.menu_html(school_value, diet_value, when, fields))

    def menu_html(self, school_value: str, diet_value: str,
                  when: Optional[date] = None, fields: Optional[FormFields] = None) -> str:
        """HTML del menu richiesto (serve per salvare i fixture di test)."""
        fields = fields or self.form()
        data = self._base_post(fields, school_value, diet_value)
        data[fields.btn_search.get("name")] = fields.btn_search.get("value", "Visualizza")
        html = self._post(data)

        if when is not None:
            want = when.strftime("%d/%m/%Y")
            if selected_day(html) != want:
                # navigazione per data: servono VIEWSTATE/EVENTVALIDATION della pagina
                # appena ricevuta (il sottomenu childMenu esiste solo dopo la ricerca)
                nav = FormFields(parse_html(html))
                if nav.hdn_date and nav.btn_move_to_date:
                    data = self._base_post(nav, school_value, diet_value)
                    data[nav.hdn_date.get("name")] = want
                    data[nav.btn_move_to_date.get("name")] = ""
                    html = self._post(data)
        return html

    @staticmethod
    def _base_post(fields: FormFields, school_value: str, diet_value: str) -> Dict[str, str]:
        return {
            "__VIEWSTATE": fields.viewstate.get("value"),
            "__VIEWSTATEGENERATOR": fields.viewstate_generator.get("value"),
            "__EVENTVALIDATION": fields.eventvalidation.get("value"),
            fields.select_school.get("name"): school_value,
            fields.select_diet.get("name"): diet_value,
        }


def selected_day(html: str) -> Optional[str]:
    m = re.search(r'selected-day[^>]*data-datevalue="(\d{2}/\d{2}/\d{4})"', html)
    return m.group(1) if m else None


# --------------------------------------------------------------------------------------
# Parsing della pagina dei risultati
# --------------------------------------------------------------------------------------

def parse_menu(html: str) -> Menu:
    root = parse_html(html)
    container = root.find(cls="daily-menu")
    if container is None:
        raise RiboscuolaError("nel risultato non c'e' il blocco 'daily-menu': layout cambiato?")

    day_node = container.find(cls="selected-day")
    when = None
    if day_node:
        raw = day_node.get("data-datevalue") or day_node.text()
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", raw)
        if m:
            when = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    menu = Menu(data=when or "")
    no_menu = container.find(cls="no-menu")
    if no_menu is not None:
        menu.note = normalize_ws(no_menu.text())
        return menu

    for group in container.find_all("li"):
        label_node = group.find("label")
        if label_node is None:
            continue
        categoria = normalize_ws(label_node.text())
        for prod in group.find_all("div", cls="descr-product"):
            current: Optional[Piatto] = None
            for child in prod.children:
                if not isinstance(child, Node):
                    continue
                if child.tag == "strong":
                    nome = normalize_ws(child.text())
                    if not nome:
                        continue
                    current = Piatto(categoria=categoria, nome=nome)
                    menu.piatti.append(current)
                elif child.tag == "p":
                    txt = normalize_ws(child.text())
                    if not txt or current is None:
                        continue
                    if "pAllergen" in child.get("id") or child.has_class("allergeni"):
                        allerg = txt.split(":", 1)[-1] if txt.lower().startswith("allergeni") else txt
                        current.allergeni = [a.strip() for a in allerg.split(",") if a.strip()]
                    elif "pDescription" in child.get("id"):
                        current.ingredienti = txt
                elif child.tag == "div" and child.has_class("ico-category-container"):
                    if current is not None:
                        for inner in child.find_all("div"):
                            current.marcature += [c for c in inner.classes
                                                 if c not in ("ico-category-container",)]
            if current is not None and "*" in current.nome:
                current.congelato = True

    link = container.find("a", id_contains="lnkDownloadPdf")
    if link is not None and link.get("href"):
        menu.pdf_url = urllib.parse.urljoin(BASE_URL, link.get("href"))
    return menu


# --------------------------------------------------------------------------------------
# Formattazione
# --------------------------------------------------------------------------------------

GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]

# etichette del sito -> parola singolare usata nel parlato
CATEGORIE_SINGOLARI = {
    "Primi": "primo",
    "Primo": "primo",
    "Secondi": "secondo",
    "Secondo": "secondo",
    "Contorni": "contorno",
    "Contorno": "contorno",
    "Antipasti": "antipasto",
    "Insalata": "insalata",
    "Frutta": "frutta",
    "Dolce": "dolce",
    "Dolci": "dolce",
    "Pane": "pane",
    "Pane e frutta": "pane e frutta",
    "Merenda": "merenda",
    "Merende": "merenda",
}


def data_leggibile(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}"


def _caption(categoria: str, count: int) -> str:
    sing = CATEGORIE_SINGOLARI.get(categoria, categoria.lower())
    return sing if count <= 1 else categoria.lower()


def to_text(menu: Menu) -> str:
    """Testo leggibile (più righe), adatto a un file di stato OpenHAB."""
    if menu.vuoto:
        return (f"Menu del {data_leggibile(menu.data)}: nessun menu presente "
                f"(giorno senza mensa o menu non ancora pubblicato).")
    righe = [
        f"Menu del giorno — {data_leggibile(menu.data)}",
        f"Scuola: {menu.scuola}" if menu.scuola else "",
        f"Tipo di menu: {menu.dieta}" if menu.dieta else "",
        (f"(Nessun menu per {data_leggibile(menu.richiesto)}: sotto il menu del giorno "
         "successivo disponibile)") if menu.richiesto and menu.richiesto != menu.data else "",
        "",
    ]
    for categoria in _ordine_categorie(menu.piatti):
        piatti = [p for p in menu.piatti if p.categoria == categoria]
        names = " oppure ".join(p.nome_pulito() for p in piatti)
        righe.append(f"{_caption(categoria, len(piatti)).capitalize()}: {names}")
    righe.append("")
    allergeni = sorted({a for p in menu.piatti for a in p.allergeni})
    if allergeni:
        righe.append("Allergeni presenti: " + ", ".join(allergeni).lower())
    if menu.pdf_url:
        righe.append("Menu del mese (PDF): " + menu.pdf_url)
    return "\n".join(r for r in righe if r)


# Come si legge la portata nella frase parlata (per bambini: frasi corte e naturali)
PAROLE_PARLATO = {
    "Primi": "Come primo",
    "Primo": "Come primo",
    "Secondi": "Come secondo",
    "Secondo": "Come secondo",
    "Secondi di carne": "Come secondo di carne",
    "Secondi di pesce": "Come secondo di pesce",
    "Contorni": "Come contorno",
    "Contorno": "Come contorno",
    "Antipasti": "Come antipasto",
    "Insalata": "Come insalata",
    "Frutta": "Come frutta",
    "Dolce": "Come dolce",
    "Dolci": "Come dolce",
    "Pane": "Come pane",
    "Pane e frutta": "Come pane e frutta",
    "Merenda": "Per merenda",
}


def _nome_parlato(piatto: Piatto) -> str:
    """Nome del piatto come lo dice la voce: minuscolo e senza i marcatori del sito.

    Il sito scrive 'Mela pranzo' o 'Yogurt merenda' per dire in quale momento viene
    servito: nella frase parlata lo scrive gia' la categoria, quindi si toglie.
    """
    nome = piatto.nome_pulito().lower()
    for suffisso in (" pranzo", " merenda"):
        if nome.endswith(suffisso) and len(nome) > len(suffisso) + 1:
            nome = nome[: -len(suffisso)].strip()
            break
    return nome


def _quando(iso: str, oggi: Optional[date] = None) -> str:
    """'ieri', 'oggi', 'domani' o la data per esteso: i bambini capiscono meglio."""
    try:
        giorno = date.fromisoformat(iso)
    except ValueError:
        return iso
    oggi = oggi or today()
    for delta, parola in ((-1, "ieri"), (0, "oggi"), (1, "domani")):
        if giorno == oggi + timedelta(days=delta):
            return parola
    return data_leggibile(iso)


def _frase_portata(categoria: str, piatti: List[Piatto]) -> str:
    """Una frase per la portata: 'Come primo: X.' o 'Come primo puoi scegliere: X, oppure Y.'"""
    scelte = ", oppure ".join(_nome_parlato(p) for p in piatti)
    intro = PAROLE_PARLATO.get(categoria, "Come " + _caption(categoria, 1))
    if len(piatti) > 1:
        return f"{intro} puoi scegliere: {scelte}."
    return f"{intro}: {scelte}."


def to_speech(menu: Menu, max_chars: int = 0, oggi: Optional[date] = None) -> str:
    """Testo per la voce di Alexa, pensato per dei bambini.

    Frasi corte, una portata per frase, punto fermo fra una e l'altra (la voce di Alexa
    corre sulle virgole e i bambini non stanno dietro), e 'puoi scegliere ... oppure ...'
    quando il menu offre due piatti.
    """
    if menu.vuoto:
        return (f"Per {_quando(menu.data, oggi)} il menu della mensa non c'\u00e8: "
                f"forse quel giorno non si va a mensa.")
    frasi = []
    if menu.richiesto and menu.richiesto != menu.data:
        frasi.append(f"Per {_quando(menu.richiesto, oggi)} il menu non era ancora pronto, "
                     f"cos\u00ec ti leggo quello di {_quando(menu.data, oggi)}.")
    else:
        frasi.append(f"Ecco il menu della mensa di {_quando(menu.data, oggi)}.")
    for categoria in _ordine_categorie(menu.piatti):
        frasi.append(_frase_portata(categoria, [p for p in menu.piatti
                                                if p.categoria == categoria]))
    frasi.append("Buon appetito!")
    return _unisci_frasi(frasi, max_chars)


def _unisci_frasi(frasi: List[str], max_chars: int) -> str:
    """Unisce le frasi; se max_chars e' stretto tiene solo le frasi che ci stanno."""
    frase = " ".join(frasi)
    if not max_chars or len(frase) <= max_chars:
        return frase
    acc = ""
    for f in frasi:
        cand = f"{acc} {f}".strip()
        if len(cand) > max_chars:
            break
        acc = cand
    if acc:
        return acc if acc.endswith((".", "!")) else acc + "."
    # troppo stretto anche per la prima frase: taglia su una parola intera
    return frase[:max_chars].rsplit(" ", 1)[0].rstrip(" ,:;") + "."


def _ordine_categorie(piatti: List[Piatto]) -> List[str]:
    ordine = []
    for p in piatti:
        if p.categoria not in ordine:
            ordine.append(p.categoria)
    return ordine


def menu_to_json(menu: Menu, school: Tuple[str, str], diet: Tuple[str, str],
                 fonte: str = "") -> dict:
    return {
        "generato_il": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fonte": fonte,
        "scuola": {"nome": school[0], "id": school[1]},
        "tipo_menu": {"nome": diet[0], "id": diet[1]},
        "data": menu.data,
        "data_richiesta": menu.richiesto or menu.data,
        "data_leggibile": data_leggibile(menu.data),
        "note": menu.note,
        "pdf_menu": menu.pdf_url,
        "portate": [asdict(p) for p in menu.piatti],
        "parole_chiave": {p.categoria: [x.nome_pulito() for x in menu.piatti
                                         if x.categoria == p.categoria]
                          for p in menu.piatti},
    }


# --------------------------------------------------------------------------------------
# Risoluzione scuola / dieta
# --------------------------------------------------------------------------------------

def _norm(s: str) -> str:
    s = s.strip().lower()
    try:
        import unicodedata
        s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    except Exception:
        pass
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def find_label(options: List[Tuple[str, str]], value: str) -> str:
    for label, val in options:
        if val == value:
            return label
    return value


def resolve(options: List[Tuple[str, str]], wanted: str, cosa: str) -> Tuple[str, str]:
    """Trova (label, value) per `wanted` nella lista opzioni."""
    wanted_n = _norm(wanted)
    exact = [(l, v) for l, v in options if _norm(l) == wanted_n]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise AmbiguousSelection(f"'{wanted}' corrisponde a {len(exact)} {cosa} diverse")
    # tutte le parole richieste presenti nell'etichetta, anche in ordine diverso:
    # "don milani primaria" -> "DON MILANI - SCUOLA PRIMARIA"
    tokens = set(wanted_n.split())
    token_match = [(l, v) for l, v in options
                   if tokens and tokens <= set(_norm(l).split())]
    if len(token_match) == 1:
        return token_match[0]
    partial = [(l, v) for l, v in options if wanted_n and wanted_n in _norm(l)]
    candidati = token_match or partial
    if len(candidati) > 1:
        raise AmbiguousSelection(
            f"'{wanted}' e' ambiguo per {cosa}. Candidati: "
            + ", ".join(l for l, _ in candidati[:12])
            + (" ..." if len(candidati) > 12 else ""))
    if candidati:
        return candidati[0]
    similar = difflib.get_close_matches(wanted_n, [_norm(l) for l, _ in options], n=5, cutoff=0.6)
    hints = ", ".join(l for l, _ in options if _norm(l) in similar)
    raise RiboscuolaError(
        f"nessuna {cosa} corrisponde a '{wanted}'."
        + (f" Forse cercavi: {hints}." if hints else "")
        + " (usa --list-schools / --list-diets per l'elenco completo)")


def normalize_id(raw: str, options: List[Tuple[str, str]], cosa: str, come_listare: str) -> str:
    """Accetta il valore completo ('2|239|6') o anche solo un pezzo ('239')."""
    raw = raw.strip()
    exact = [(l, v) for l, v in options if v == raw]
    if exact:
        return exact[0][1]
    partial = [(l, v) for l, v in options if raw in v.split("|")]
    if len(partial) == 1:
        return partial[0][1]
    if len(partial) > 1:
        raise AmbiguousSelection(
            f"l'id '{raw}' non basta per capire la {cosa}. Candidati: "
            + ", ".join(f"{l} = {v}" for l, v in partial[:8])
            + (" ..." if len(partial) > 8 else ""))
    raise RiboscuolaError(f"l'id '{raw}' non corrisponde a nessuna {cosa} "
                          f"(usa {come_listare} per l'elenco)")


# --------------------------------------------------------------------------------------
# Cache / output
# --------------------------------------------------------------------------------------

def read_cache(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def cache_is_fresh(cache: dict, ttl: int, when: str) -> bool:
    if not cache or cache.get("data") != when:
        return False
    try:
        ts = datetime.fromisoformat(cache.get("generato_il"))
    except (TypeError, ValueError):
        return False
    if ts.tzinfo is None:                      # cache scritta da una versione precedente
        ts = ts.astimezone()
    return (datetime.now().astimezone() - ts).total_seconds() <= ttl


def write_atomic(path: str, content: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(content if content.endswith("\n") else content + "\n")
    os.replace(tmp, path)


def today(tz_name: str = DEFAULT_TZ) -> date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz_name)).date()
    except Exception:
        return datetime.now().date()


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def parse_data(raw: str) -> Optional[date]:
    """Accetta AAAA-MM-GG e GG/MM/AAAA (e GG-MM)."""
    raw = raw.strip()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def load_config(path: Optional[str]) -> dict:
    if not path:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError) as err:
            print(f"avviso: config non leggibile ({err}), uso i default", file=sys.stderr)
    return {}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Legge il menu del giorno da riboscuola.it e lo stampa per Alexa/OpenHAB")
    p.add_argument("--date", metavar="DATA", help="giorno da leggere: AAAA-MM-GG o GG/MM/AAAA (default: oggi)")
    p.add_argument("--tomorrow", action="store_true", help="equivalente a --date domani")
    p.add_argument("--school", help=f"scuola (default: {DEFAULT_SCHOOL})")
    p.add_argument("--school-id", help="valore interno della scuola, es. '2|239|6'")
    p.add_argument("--diet", help=f"tipo di menu (default: {DEFAULT_DIET})")
    p.add_argument("--diet-id", help="valore interno del tipo di menu, es. '2'")
    p.add_argument("--format", choices=["text", "json", "speech"], default="text",
                   help="formato dell'output stdout (default: text)")
    p.add_argument("--speech-max-chars", type=int, default=None,
                   help="tronca la frase parlata a N caratteri (0 = nessuna truncate)")
    p.add_argument("--fallback", choices=["none", "next"], default=None,
                   help="se non c'e' menu: 'next' usa il primo giorno successivo con menu")
    p.add_argument("--fallback-days", type=int, default=None, help="fin dove cercare (default 3)")
    p.add_argument("--out", metavar="FILE", help="scrivi il testo su file (atomico)")
    p.add_argument("--json-out", metavar="FILE", help="scrivi il JSON su file (atomico)")
    p.add_argument("--cache", metavar="FILE", help="file di cache JSON (per output stale)")
    p.add_argument("--no-cache", action="store_true", help="non usare ne' scrivere la cache")
    p.add_argument("--cache-ttl", type=int, default=None,
                   help="secondi di validita' della cache (0 = non usare la cache in lettura)")
    p.add_argument("--allow-stale", action="store_true",
                   help="in caso di errore usa l'ultima cache come output")
    p.add_argument("--list-schools", action="store_true", help="elenca le scuole disponibili")
    p.add_argument("--list-diets", action="store_true", help="elenca i tipi di menu disponibili")
    p.add_argument("--html", metavar="FILE",
                   help="leggi il menu da un file HTML invece che dal sito (debug/test)")
    p.add_argument("--html-next", metavar="FILE",
                   help="file HTML per il giorno dopo: serve a provare --fallback next offline")
    p.add_argument("--form", metavar="FILE",
                   help="file HTML con il form di ricerca (per --list-schools/--list-diets offline)")
    p.add_argument("--config", help="percorso del file config.json")
    p.add_argument("--timeout", type=float, default=None)
    p.add_argument("--retries", type=int, default=None)
    p.add_argument("--base-url", default=BASE_URL, help=argparse.SUPPRESS)
    p.add_argument("-q", "--quiet", action="store_true", help="nessun messaggio su stderr")
    return p


def fail_stale(err: Exception, args, cache_path: Optional[str], when: Optional[date] = None) -> int:
    """Stampa l'errore e, se possibile, stampa l'ultima cache buona."""
    print(f"errore: {err}", file=sys.stderr)
    if args.allow_stale and cache_path:
        cache = read_cache(cache_path)
        if cache:
            print(f"uso l'ultima cache disponibile: {cache_path}", file=sys.stderr)
            if when and cache.get("data") and cache.get("data") != when.isoformat():
                print(f"ATTENZIONE: il menu in cache e' del {cache.get('data')}, "
                      f"non del {when.isoformat()}", file=sys.stderr)
            emit(cache, args, cache_path)
    return EXIT_ERROR


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(args.config)

    def pick(name: str, default=None):
        return getattr(args, name, None) if getattr(args, name, None) not in (None, "") else cfg.get(name, default)

    school = pick("school", DEFAULT_SCHOOL)
    diet = pick("diet", DEFAULT_DIET)
    school_id = pick("school_id")
    diet_id = pick("diet_id")
    tz = cfg.get("timezone", DEFAULT_TZ)

    def num(name: str, default):
        val = getattr(args, name)
        return default if val is None else val

    args.fallback = args.fallback or cfg.get("fallback", "none")
    args.fallback_days = num("fallback_days", int(cfg.get("fallback_days", 3)))
    args.speech_max_chars = num("speech_max_chars", int(cfg.get("speech_max_chars", 0)))
    args.cache_ttl = num("cache_ttl", int(cfg.get("cache_ttl", 0)))
    args.timeout = num("timeout", float(cfg.get("timeout", 30.0)))
    args.retries = num("retries", int(cfg.get("retries", 3)))
    args.allow_stale = args.allow_stale or bool(cfg.get("allow_stale", False))

    client = RiboscuolaClient(base_url=args.base_url, timeout=args.timeout, retries=args.retries)

    if args.list_schools or args.list_diets:
        try:
            if args.form:
                with open(args.form, "r", encoding="utf-8") as fh:
                    fields = FormFields(parse_html(fh.read()))
                if not fields.ok:
                    raise RiboscuolaError(f"nel file '{args.form}' non c'e' il form di ricerca")
                opts = fields.options("school" if args.list_schools else "diet")
            else:
                opts = client.schools() if args.list_schools else client.diets()
        except OSError as err:
            print(f"errore: {err}", file=sys.stderr)
            return EXIT_ERROR
        except RiboscuolaError as err:
            print(f"errore: {err}", file=sys.stderr)
            return EXIT_ERROR
        for label, value in opts:
            print(f"{value}\t{label}")
        return EXIT_OK

    if args.date:
        when = parse_data(args.date)
        if when is None:
            print(f"errore: data non valida '{args.date}' (usa AAAA-MM-GG o GG/MM/AAAA)",
                  file=sys.stderr)
            return EXIT_ERROR
    elif args.tomorrow:
        when = today(tz) + timedelta(days=1)
    else:
        when = today(tz)

    cache_path = None if args.no_cache else pick("cache")
    if cache_path and not os.path.isabs(cache_path):
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cache_path)

    # cache veloce: evita di richiamare il sito se l'abbiamo gia' letto da poco
    if cache_path and args.cache_ttl > 0:
        cache = read_cache(cache_path)
        if cache and cache_is_fresh(cache, args.cache_ttl, when.isoformat()):
            if not args.quiet:
                print(f"cache: uso '{cache_path}' (data {when.isoformat()})", file=sys.stderr)
            return emit(cache, args, cache_path)

    try:
        if args.html:
            school_pair, diet_pair = (school, school_id or "-"), (diet, diet_id or "-")
            fields = None
        else:
            if args.form:
                try:
                    with open(args.form, "r", encoding="utf-8") as fh:
                        fields = FormFields(parse_html(fh.read()))
                except OSError as err:
                    return fail_stale(err, args, cache_path, when)
                if not fields.ok:
                    return fail_stale(
                        RiboscuolaError(f"nel file '{args.form}' non c'e' il form di ricerca"),
                        args, cache_path, when)
            else:
                fields = client.form()
            if school_id:
                value = normalize_id(school_id, fields.options("school"), "scuola",
                                     "--list-schools")
                school_pair = (find_label(fields.options("school"), value), value)
            else:
                school_pair = resolve(fields.options("school"), school, "scuola")
            if diet_id:
                value = normalize_id(diet_id, fields.options("diet"), "tipo di menu",
                                     "--list-diets")
                diet_pair = (find_label(fields.options("diet"), value), value)
            else:
                diet_pair = resolve(fields.options("diet"), diet, "tipo di menu")
    except AmbiguousSelection as err:
        print(f"errore: {err}", file=sys.stderr)
        return EXIT_AMBIGUOUS
    except RiboscuolaError as err:
        return fail_stale(err, args, cache_path, when)

    def fetch(day: date, first: bool = False):
        """None se non c'e' nessuna sorgente per quel giorno."""
        if args.html:
            path = args.html if first else args.html_next
            if not path:
                return None
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return parse_menu(fh.read())
            except OSError as err:
                raise RiboscuolaError(f"non leggo il file HTML '{path}': {err}") from err
        return client.menu(school_pair[1], diet_pair[1], day, fields=fields if first else None)

    try:
        menu = fetch(when, first=True)
        tried = [when]
        while menu.vuoto and args.fallback == "next" and len(tried) <= args.fallback_days:
            nxt = tried[-1] + timedelta(days=1)
            if not args.quiet:
                print(f"nessun menu per {tried[-1].isoformat()}, provo {nxt.isoformat()}",
                      file=sys.stderr)
            nxt_menu = fetch(nxt)
            if nxt_menu is None:
                break
            menu = nxt_menu
            tried.append(nxt)
        menu.scuola, menu.dieta = school_pair[0], diet_pair[0]
        if tried[-1] != when:
            menu.richiesto = when.isoformat()
    except RiboscuolaError as err:
        return fail_stale(err, args, cache_path, when)

    payload = menu_to_json(menu, school_pair, diet_pair,
                           args.html if args.html else client.base_url)
    if cache_path:
        write_atomic(cache_path, json.dumps(payload, ensure_ascii=False, indent=2))

    if menu.vuoto and args.fallback != "next":
        if not args.quiet:
            print(f"nessun menu per {when.isoformat()}", file=sys.stderr)
        emit(payload, args, cache_path)
        return EXIT_NO_MENU
    return emit(payload, args, cache_path)


def emit(payload: dict, args, cache_path: Optional[str]) -> int:
    menu = json_to_menu(payload)
    if args.format == "json":
        out = json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.format == "speech":
        out = to_speech(menu, args.speech_max_chars)
    else:
        out = to_text(menu)
    print(out)
    if args.out:
        write_atomic(args.out, out)
    if args.json_out:
        write_atomic(args.json_out, json.dumps(payload, ensure_ascii=False, indent=2))
    return EXIT_OK


def json_to_menu(payload: dict) -> Menu:
    return Menu(
        data=payload.get("data") or "",
        richiesto=payload.get("data_richiesta") or "",
        scuola=(payload.get("scuola") or {}).get("nome", ""),
        dieta=(payload.get("tipo_menu") or {}).get("nome", ""),
        piatti=[Piatto(categoria=k, nome=n) for k, names in (payload.get("parole_chiave") or {}).items()
                for n in names],
        pdf_url=payload.get("pdf_menu") or "",
        note=payload.get("note") or "",
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
