# Sektor7 Absturz-Waechter (Manu 22.10.2026: "der Server darf nicht so lang offline sein")
# Alle 5 Minuten: steht der Server im Nexus-Panel auf "gestoppt" (z. B. nach einem Absturz)
# und ist gerade KEIN normaler Neustart-Zeitraum, druecke ich "Start" und melde es in Discord.
# Einen LAUFENDEN Server fasse ich nie an. Zugangsdaten nur aus GitHub-Secrets.
import os, sys, json, time, datetime, urllib.request
from zoneinfo import ZoneInfo
from nexus_panel import Panel

SERVER_ID = 13607
CRON_STUNDEN = [0, 4, 8, 12, 16, 20]   # Nexus-Cron-Neustarts
FENSTER_VOR, FENSTER_NACH = 6, 12      # Minuten um den Cron-Neustart herum: nichts tun
MAX_STARTS_3H = 3                      # Bremse, falls er sofort wieder abstuerzt
BERLIN = ZoneInfo("Europe/Berlin")
STATE = "zustand.json"
TEST = os.environ.get("MODUS", "normal").strip() == "test"


def jetzt():
    return datetime.datetime.now(BERLIN)


def log(*a):
    print(f"{jetzt():%d.%m. %H:%M:%S}", *a, flush=True)


def discord(titel, text, farbe):
    url = os.environ.get("DISCORD_ALARM", "")
    if not url:
        log("Discord-Webhook fehlt")
        return
    uid = os.environ.get("DISCORD_ERWAEHNEN", "").strip()
    body = {"username": "Sektor7-Bot", "content": f"<@{uid}>" if uid else "",
            "allowed_mentions": {"users": [uid] if uid else []},
            "embeds": [{"title": titel, "description": text,
                        "color": {"rot": 0xE74C3C, "gelb": 0xF1C40F, "gruen": 0x2ECC71}[farbe],
                        "footer": {"text": f"Sektor7 Absturz-Wächter • {jetzt():%d.%m.%Y %H:%M}"}}]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Sektor7-Bot"})
    try:
        urllib.request.urlopen(req, timeout=20).close()
        log("Discord gesendet:", titel)
    except Exception as e:
        log("Discord-Fehler:", type(e).__name__)


def im_cron_fenster():
    t = jetzt()
    for tag in (-1, 0, 1):
        for h in CRON_STUNDEN:
            s = (t + datetime.timedelta(days=tag)).replace(hour=h, minute=0, second=0, microsecond=0)
            if s - datetime.timedelta(minutes=FENSTER_VOR) <= t <= s + datetime.timedelta(minutes=FENSTER_NACH):
                return True
    return False


try:
    Z = json.load(open(STATE, encoding="utf-8"))
except Exception:
    Z = {}
Z.setdefault("starts", [])


def speichern():
    Z["letzter_lauf"] = f"{jetzt():%d.%m. %H:%M}"
    json.dump(Z, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if os.environ.get("PAUSE", "").strip() == "1":
    log("Pause eingeschaltet (Variable PAUSE=1) – nichts zu tun")
    speichern(); sys.exit(0)
if im_cron_fenster() and not TEST:
    log("Normaler Neustart-Zeitraum – nichts zu tun")
    speichern(); sys.exit(0)

p = Panel(SERVER_ID)
try:
    p.anmelden()
    state = p.status().get("state")
except Exception as e:
    log("Panel nicht erreichbar:", type(e).__name__)
    Z["panel_fehler"] = Z.get("panel_fehler", 0) + 1
    if Z["panel_fehler"] == 3:   # einmal melden, nicht alle 5 Minuten
        discord("⚠️ Absturz-Wächter kommt nicht ins Panel",
                f"Seit 3 Läufen keine Anmeldung möglich ({type(e).__name__}). Bitte Claude Bescheid geben.", "gelb")
    speichern(); sys.exit(0)
Z["panel_fehler"] = 0
log("Panel-Status:", state)
if TEST:
    discord("🔧 Absturz-Wächter: Test", f"Anmeldung klappt. Server-Status gerade: **{state}**.\n"
            "Im Ernstfall (Status *stopped*) würde ich jetzt auf **Start** drücken.", "gelb")
    speichern(); sys.exit(0)

if state != "stopped":
    if Z.get("aus_seit"):
        discord("✅ Server läuft wieder", f"Status: **{state}** (aus seit {Z['aus_seit']}).", "gruen")
        Z["aus_seit"] = None
    speichern(); sys.exit(0)

# --- Server ist gestoppt ---
Z["aus_seit"] = Z.get("aus_seit") or f"{jetzt():%d.%m. %H:%M}"
grenze = jetzt() - datetime.timedelta(hours=3)
Z["starts"] = [s for s in Z["starts"] if datetime.datetime.fromisoformat(s) > grenze]
if len(Z["starts"]) >= MAX_STARTS_3H:
    if not Z.get("bremse_gemeldet"):
        discord("🚨 SERVER AUS – Start hilft nicht",
                f"Schon {len(Z['starts'])}× in 3 Std gestartet, er geht immer wieder aus. Ich höre auf.\n"
                "**Bitte selbst nachsehen / Claude fragen.**", "rot")
        Z["bremse_gemeldet"] = True
    speichern(); sys.exit(0)
Z["bremse_gemeldet"] = False
st = p.starten()
Z["starts"].append(jetzt().isoformat())
log("Start ausgelöst, HTTP", st)
discord("🚨 Server war AUS – ich starte ihn", f"Panel meldete **gestoppt** (bemerkt {jetzt():%H:%M}).\n"
        f"Start gedrückt (HTTP {st}). Ich schaue in 5 Minuten wieder nach.", "rot")
speichern()
