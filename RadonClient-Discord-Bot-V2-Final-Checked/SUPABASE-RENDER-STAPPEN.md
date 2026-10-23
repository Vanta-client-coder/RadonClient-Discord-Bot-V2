# RadonClient Bot V2 — Supabase + Render (stappen)

De bot gebruikt **één online PostgreSQL database**; de website kan later veilig op dezelfde database aansluiten. Alleen de botcode is op dit moment gekoppeld; de website nog niet.

1. Maak via https://supabase.com/dashboard een **Free** project aan. Noteer je databasewachtwoord op een veilige plek, deel het niet met iemand.
2. Klik in het project op **Connect** en kies bij voorkeur **Session pooler** (poort 5432). Render kan een IPv4-netwerk gebruiken; de directe gratis Supabase-verbinding is IPv6-only. Neem de volledige gegenereerde connection string over, inclusief juiste host en gebruikersnaam. **Niet zelf een hostnaam verzinnen.**
3. Voeg indien nodig `?sslmode=require` toe (gebruik `&sslmode=require` wanneer de URL al query parameters heeft). Gebruik bij voorkeur certificaatverificatie `verify-full` wanneer je de benodigde CA hebt geconfigureerd.
4. Zet op de Render-service **Environment**: `DATABASE_URL` = connection string en `RADON_REQUIRE_PERSISTENT_DB` = `1`. Laat `DISCORD_TOKEN` en `RADON_CONFIG_JSON` ongewijzigd. Deel geen van deze geheime waarden in chat of GitHub.
5. Maak eerst een back-up van de huidige botversie en zo mogelijk de bestaande SQLite-data; een Render Free bestand kan na herstart verdwenen zijn. Gebruik `migrate_sqlite_to_postgres.py` uitsluitend voor een echte beschikbare SQLite-back-up en **vóór** de nieuwe bot gegevens schrijft naar PostgreSQL.
6. Optioneel: test lokaal vanaf een privé shell met `python check_database.py` terwijl `DATABASE_URL` is ingesteld. Deze controle leest alleen, toont nooit het wachtwoord en verandert geen tabellen.
7. Werk **de bestaande** GitHub-repo en Render-service bij, zonder een tweede bot met hetzelfde token te starten. Behoud de huidige Root Directory, `pip install -r requirements.txt`, en `python -u bot.py`.
8. Kijk in Render-logs of `[DATABASE] PostgreSQL connected; persistent storage enabled.` verschijnt, en of Discord echt als online is aangemeld. Test vervolgens de bestaande tickets, giveaways en warnings via een testkanaal.
9. Controleer na een geplande herstart of de testgegevens nog bestaan. Richt waar mogelijk afzonderlijke back-ups in. Een database alleen is geen back-up.

## Beperkingen

- Supabase Free is gratis maar kan bij weinig activiteit na circa 7 dagen pauzeren. Een gepauzeerde database kan de bot beletten te starten totdat het project is hersteld.
- De 500 MB Free-limiet kan voorlopig voldoende zijn; dat is geen garantie over toekomstig gebruik.
- De website is nog niet aangesloten; daarvoor is aparte server-side implementatie en beveiliging nodig.
- Automatische tests zijn geen live test bij Discord, Render of Supabase.

Officiële documentatie: https://supabase.com/docs/guides/database/connecting-to-postgres en https://supabase.com/docs/guides/platform/free-project-pausing
