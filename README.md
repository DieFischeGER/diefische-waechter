# Sektor7 Absturz-Wächter (Repo Sektor7GER/sektor7-waechter)

Kleiner Wächter für den DayZ-Server „Sektor7“: alle 5 Minuten wird im Nexus-Panel geschaut,
ob der Server läuft. Steht er außerhalb der normalen Neustartzeiten auf **gestoppt** (z. B. nach einem Absturz),
wird er gestartet und in Discord gemeldet. Ein laufender Server wird nie angefasst.

- Zugangsdaten nur als GitHub-Secrets: `NEXUS_EMAIL`, `NEXUS_PASS`, `DISCORD_ALARM`, `DISCORD_ERWAEHNEN`.
- **Pause** (z. B. wenn der Server absichtlich aus bleiben soll): Settings → Secrets and variables → Actions → *Variables* → `PAUSE` = `1`. Zum Weitermachen löschen oder `0`.
- Test: Actions → Absturz-Wächter → Run workflow → Modus `test`.

- **Wetter für den S7-Launcher** (seit 26.10.2026): bei jedem Lauf holt `wetter.py` die Wetterdatei des Servers und legt sie in den Zweig `wetter` (`wetter_deerisle.txt`). Nur Wetterwerte, keine Zugangsdaten. Fehler dabei stören den Wächter nie.
