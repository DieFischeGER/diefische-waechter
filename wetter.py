# Sektor7: Wetter fuer den S7-Launcher (Manu 26.10.2026 16:16 „machen wir so“ – Wetter-Lauf alle 5 Min statt nur alle 30 Min im Takt).
# Holt profiles/Sektor7_LootStats/wetter_aktuell.txt (schreibt der Server-Baustein LootStats jede Minute)
# und legt sie als wetter_<server-id>.txt ab. Der Workflow stellt sie danach in den Zweig „wetter“ dieses Repos.
# Weg 1: FTP (Secrets FTP_USER/FTP_PASS, falls hier eingetragen) – Weg 2: Nexus-Panel (Secrets NEXUS_EMAIL/NEXUS_PASS).
# Nur bekannte, kurze Wetterwerte werden veroeffentlicht – keine Namen, IDs oder Zugangsdaten.
# Bricht nie etwas ab: bei Fehler nur ein Hinweis im Log.
import os, io, sys, ftplib, urllib.parse

SERVER_ID = 13607
WETTER_ID = os.environ.get("WETTER_SERVER_ID", "deerisle")
FTP_HOST, FTP_PORT = "157.90.205.37", 21
ORDNER, DATEI = "profiles/Sektor7_LootStats/", "wetter_aktuell.txt"
ERLAUBT = {"stand", "bewoelkung", "regen", "nebel", "schnee", "wind", "temp", "ingame"}


def ueber_ftp():
    f = ftplib.FTP_TLS(timeout=40)
    f.connect(FTP_HOST, FTP_PORT)
    f.login(os.environ["FTP_USER"], os.environ["FTP_PASS"])
    f.prot_p()
    b = io.BytesIO()
    f.retrbinary("RETR " + ORDNER + DATEI, b.write)
    f.quit()
    return b.getvalue().decode("utf-8", errors="replace")


def ueber_panel():
    from nexus_panel import Panel
    p = Panel(SERVER_ID)
    p.anmelden()
    st, url, t = p._req(f"/api/gameservers/{SERVER_ID}/files/{DATEI}?path=" + urllib.parse.quote(ORDNER))
    if st != 200:
        raise RuntimeError(f"HTTP {st}")
    return t


def main():
    text, wege = None, []
    if os.environ.get("FTP_USER") and os.environ.get("FTP_PASS"):
        wege.append(("FTP", ueber_ftp))
    if os.environ.get("NEXUS_EMAIL") and os.environ.get("NEXUS_PASS"):
        wege.append(("Panel", ueber_panel))
    for name, weg in wege:
        try:
            text = weg()
            print("Wetter geholt über", name)
            break
        except Exception as e:
            print(f"Wetter über {name} nicht lesbar: {type(e).__name__} {str(e)[:120]}")
    if not text:
        print("Wetter: nichts geholt")
        return
    zeilen = []
    for z in text.splitlines():
        if ";" not in z:
            continue
        k, v = z.split(";", 1)
        k = k.strip().lower()
        if k in ERLAUBT and len(v) < 40:
            zeilen.append(f"{k};{v.strip()}")
    if not any(z.startswith("stand;") for z in zeilen):
        print("Wetter: Datei ohne Zeitstempel – nichts veröffentlicht")
        return
    open(f"wetter_{WETTER_ID}.txt", "w", encoding="utf-8").write("\n".join(zeilen) + "\n")
    print("Wetter:", " | ".join(zeilen))


if __name__ == "__main__":
    main()
