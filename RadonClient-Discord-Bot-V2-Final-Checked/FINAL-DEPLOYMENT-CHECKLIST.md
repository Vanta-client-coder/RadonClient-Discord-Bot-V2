# RadonClient Discord Bot V2 — gecontroleerde uitrol

## Wat wel en niet is vastgesteld

- De bronbestanden, ZIP en Python syntax zijn lokaal gecontroleerd.
- Unit tests controleren lokale logica. Er is **geen echte Discord-login** uitgevoerd.
- De vorige live service kreeg HTTP 429 / Cloudflare 1015. Een nieuwe GitHub-repository lost een mogelijke Discord/IP blokkade **niet automatisch** op.
- Er is een bekend herstelrisico: bij bepaalde mislukte loginpogingen kan het Discord-clientobject gesloten raken; de bot toont dan `restart_required` en vraagt gecontroleerd ingrijpen in plaats van een onbeperkte herstartlus.

## Voor GitHub

1. Maak een PRIVATE repository aan en upload de inhoud van de ZIP naar de repository-root.
2. Publiceer GEEN `.env`, `config.json`, `.db`, tokens of API keys.
3. Gebruik je originele configuratie uit de oude omgeving. `config.example.json` bevat alleen placeholders.
4. Controleer dat `bot.py`, `requirements.txt` en `render.yaml` in de root staan.
5. Bewaar een back-up van tickets/giveaways/database. Een nieuwe Render-service heeft geen toegang tot de oude database zonder aparte migratie.

## Voor Render

1. Maak **een Web Service** met branch `main` en lege Root Directory.
2. Build Command: `pip install -r requirements.txt`.
3. Start Command: `python -u bot.py`.
4. Zet Auto Deploy uit.
5. Zet `DISCORD_TOKEN` en `RADON_CONFIG_JSON` via de private Environment-instellingen. De JSON moet uit je bestaande geldige `config.json` komen.
6. Zet `RADON_INTERNAL_API_KEY` alleen als de beveiligde website-API moet werken. Configureer dezelfde sleutel veilig in de website-backend.
7. Zet `RADON_DATA_DIR` naar een **persistent disk** als je ticket/giveawaydata na redeploy wilt behouden. Kopieer de oude database met een gecontroleerde migratie.
8. Zet de oude Render-service uit voor de **eerste** loginpoging op de nieuwe service. Bewaar de oude code en data.
9. Voer een enkele deploy uit. Controleer logs en `/health`.
10. Bij 429/1015: niet herhaaldelijk restart/deploy doen. Controleer IP/rate-limit situatie of neem contact op met Discord-support via de officiële kanalen.

## Health/heartbeat

- `online=true` betekent dat de Discord gateway verbonden is.
- `backendApiEnabled=true` betekent alleen dat de beveiligde API is ingeschakeld, niet dat de websitekoppeling live is getest.
- `heartbeat.state=active` betekent dat het Discord statusbericht recent is bijgewerkt.
- `heartbeat.state=pending/offline/cooldown/stale/disabled` zijn afzonderlijke diagnostische situaties.
- Heartbeat staat standaard op 600 seconden; agressiever pollen verhoogt alleen het API-verkeer.

## Lokale checks

```
python -m compileall -q .
python -m unittest discover -p "test*.py" -v
python preflight.py
```

De preflight controleert configuratie **zonder Discord-verzoeken** en toont nooit tokenwaarden. Je hebt hiervoor lokaal je veilige configuratie nodig.
