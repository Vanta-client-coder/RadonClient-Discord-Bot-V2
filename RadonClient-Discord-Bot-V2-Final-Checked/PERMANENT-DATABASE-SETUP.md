# RadonClient Bot V2 — Permanente database (Render)

## Waarom?

Render Free Web Services gebruiken tijdelijke opslag. Een lokale `data/radon.db` kan verdwijnen bij deploy, restart of slapen. Een online statusbericht is **geen** database-back-up. Gebruik voor tickets, giveaways, waarschuwingen, licentieberichten, weekranglijsten en staffuitnodigingen een PostgreSQL-database.

## Aanbevolen stappen — vóór een update van de huidige werkende bot

1. Maak een aparte, beheerde PostgreSQL-database aan, bijvoorbeeld bij Render (betaalde duurzame variant) of een provider met een passende retentie/backupregeling. Controleer actuele prijzen en gratis limieten; een Render Free Postgres database kan na 30 dagen verlopen.
2. Kopieer de PostgreSQL connection string **privé**. Deel deze URL niet via chat, screenshots, Discord of GitHub. Laat SSL ingeschakeld (`sslmode=require`) als de provider dit ondersteunt.
3. Ga naar de **bestaande** Render Web Service -> **Environment**. Voeg toe:
   - `DATABASE_URL`: de echte PostgreSQL connection string
   - `RADON_REQUIRE_PERSISTENT_DB`: `1`
   - Laat `DISCORD_TOKEN` en `RADON_CONFIG_JSON` ongewijzigd.
4. Maak vóór de deployment een back-up van de werkende GitHub-commit en alle databasegegevens die je nog kunt terughalen.
5. Heb je lokaal een bestaande `radon.db`? Gebruik optioneel `migrate_sqlite_to_postgres.py` *vóór* de deployment. Deze import weigert een al gevulde doeldatabase en wijzigt het bronbestand niet. Een database die alleen op het tijdelijke Render-bestandssysteem staat, kan niet gegarandeerd worden teruggehaald.
6. Zet de nieuwe broncode in je bestaande repo, met dezelfde Render Root Directory, build- en startopdracht. Doe één gecontroleerde deployment en controleer de logs voor `[DATABASE] PostgreSQL connected; persistent storage enabled.`
7. Test een ticket, waarschuwing, giveaway en wekelijkse telling. Test vervolgens dat ze ook na een geplande volgende restart aanwezig blijven.

## Beveiliging en beperkingen

- De bot start met `RADON_REQUIRE_PERSISTENT_DB=1` **niet** als `DATABASE_URL` ontbreekt. Dit voorkomt verborgen dataverlies. Als PostgreSQL zelf offline is, kan het starten mislukken; dit is veiliger dan gegevens ongemerkt in een nieuwe lege SQLite op te slaan.
- Deze release gebruikt één PostgreSQL-verbinding en één botinstantie. Start dezelfde token niet dubbel. Gebruik geen automatische scaling naar meerdere replicas.
- Back-ups zijn een aparte verantwoordelijkheid: configureer bij de provider automatische back-ups / PITR waar beschikbaar. Een externe database is niet hetzelfde als een back-up.
- Sommige bestaande lokale gegevens kunnen al eerder verloren zijn gegaan door Render-restarts; die worden niet automatisch teruggevonden.
- De PostgreSQL-implementatie is automatisch getest op SQL-vorm en opslaglogica, maar **niet live tegen jouw database of Discord**. Doe de eerste deployment gecontroleerd.
- Een PostgreSQL-schema is aanwezig voor alle huidige bot-tabellen. SQL-migraties worden idempotent toegepast bij opstart.

## Huidige data-tabellen

`warnings`, `tickets`, `giveaways`, `giveaway_entries`, `license_sales_messages`, `weekly_activity`, `weekly_reports`, `weekly_invites`.
