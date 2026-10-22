# DieFische: Zugriff aufs Nexus-Panel (nur fuer den Puls-Waechter: Spielerliste lesen + Server neu starten).
# Anmeldung mit einem EIGENEN Unterkonto (sekundaerer Zugriff nur mit Recht "Aktion" + "Log").
# Zugangsdaten NUR aus GitHub-Secrets: NEXUS_EMAIL, NEXUS_PASS. Nie ausgeben, nie speichern.
import os, re, json, base64, secrets, urllib.request, urllib.parse, http.cookiejar

BASIS = "https://panel.nexus-games.com"
UA = "Mozilla/5.0 (DieFische-Puls)"


class Panel:
    def __init__(self, server_id):
        self.sid = str(server_id)
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.angemeldet = False

    def _req(self, pfad, daten=None, json_body=None, kopf=None, methode=None):
        h = {"User-Agent": UA, "Accept": "application/json, text/html"}
        if kopf:
            h.update(kopf)
        body = None
        if json_body is not None:
            body = json.dumps(json_body).encode()
            h["Content-Type"] = "application/json"
        elif daten is not None:
            body = urllib.parse.urlencode(daten).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded"
        r = urllib.request.Request(BASIS + pfad, data=body, headers=h, method=methode)
        with self.op.open(r, timeout=40) as a:
            return a.status, a.geturl(), a.read().decode("utf-8", errors="replace")

    @staticmethod
    def verfuegbar():
        return bool(os.environ.get("NEXUS_EMAIL")) and bool(os.environ.get("NEXUS_PASS"))

    def anmelden(self):
        st, url, html = self._req("/de/login")
        m = re.search(r'name="_csrf_token"\s+value="([^"]+)"', html) or re.search(r'value="([^"]+)"\s+name="_csrf_token"', html)
        if not m:
            raise RuntimeError("Login-Seite ohne _csrf_token (Panel geaendert?)")
        feld = m.group(1)
        if re.fullmatch(r"[-_a-zA-Z0-9]{4,22}", feld):
            # Symfony "stateless CSRF" (csrf_protection_controller.js): Browser erzeugt Zufalls-Token,
            # legt Cookie __Host-<name>_<token>=<name> an und schickt das Token im Formular.
            token = base64.b64encode(secrets.token_bytes(18)).decode()
            self.jar.set_cookie(http.cookiejar.Cookie(
                0, f"__Host-{feld}_{token}", feld, None, False, "panel.nexus-games.com", False, False,
                "/", True, True, None, False, None, None, {"SameSite": "Strict"}))
        else:
            token = feld
        st, url, html = self._req("/de/login", daten={
            "email": os.environ["NEXUS_EMAIL"],
            "_password": os.environ["NEXUS_PASS"],
            "_csrf_token": token,
            "_remember_me": "on",
        }, kopf={"Origin": BASIS, "Referer": BASIS + "/de/login"})
        if "/login" in url:
            hinweis = ""
            for muster in (r'class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', r'class="[^"]*invalid-feedback[^"]*"[^>]*>(.*?)</', r'class="[^"]*error[^"]*"[^>]*>(.*?)</'):
                m2 = re.search(muster, html, re.S | re.I)
                if m2:
                    hinweis = re.sub(r"<[^>]+>|\s+", " ", m2.group(1)).strip()[:200]
                    break
            raise RuntimeError(f"Anmeldung abgelehnt – Panel sagt: „{hinweis or 'keine Meldung'}“ (Seite {url.split('?')[0][-30:]}, HTTP {st})")
        # Server-Seite einmal oeffnen: setzt das API-Cookie fuer /api/...
        self._req(f"/de/gameservers/{self.sid}")
        self.angemeldet = True

    def status(self):
        st, url, t = self._req(f"/api/gameservers/{self.sid}")
        return json.loads(t)

    def spieler(self):
        """gibt (anzahl, liste_verfuegbar) zurueck"""
        st, url, t = self._req(f"/api/gameservers/{self.sid}/players")
        d = json.loads(t)
        return int(d.get("activePlayers") or 0), bool(d.get("listAvailable"))

    def neustart(self):
        st, url, t = self._req(f"/api/gameservers/{self.sid}/restart", json_body={}, methode="POST")
        return st

    def starten(self):
        """gestoppten Server starten (Panel-Knopf „Start“, seit 22.10.2026)"""
        st, url, t = self._req(f"/api/gameservers/{self.sid}/start", json_body={}, methode="POST")
        return st
