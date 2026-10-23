"""Read-only PostgreSQL connection check for RadonClient Bot V2.

Run locally with DATABASE_URL set in a private environment. It never prints
credentials, creates tables, or writes any rows.
"""
import os
import sys
from urllib.parse import urlsplit, parse_qs

TABLES = (
    'warnings', 'tickets', 'giveaways', 'giveaway_entries',
    'license_sales_messages', 'weekly_activity', 'weekly_reports', 'weekly_invites',
)


def database_url_advice(url):
    if not url:
        return 'DATABASE_URL ontbreekt. Zet deze eerst privé in je omgeving.'
    parsed = urlsplit(url)
    if parsed.scheme not in ('postgresql', 'postgres') or not parsed.hostname:
        return 'DATABASE_URL moet een geldige PostgreSQL-connection string zijn.'
    if parsed.port == 6543:
        return 'LET OP: transaction pooler (poort 6543). Gebruik voor deze langlopende bot bij voorkeur de Supabase Session pooler (poort 5432).'
    if parse_qs(parsed.query).get('sslmode', [''])[0] not in ('require', 'verify-ca', 'verify-full'):
        return 'LET OP: zet sslmode=require of verify-full in de connection string voor versleuteling.'
    return 'OK'


def check(url):
    advice = database_url_advice(url)
    if advice.startswith('DATABASE_URL'):
        print('[ERROR]', advice)
        return 2
    if advice != 'OK':
        print('[ADVICE]', advice)
    try:
        import psycopg
    except ImportError:
        print('[ERROR] psycopg ontbreekt; voer pip install -r requirements.txt uit.')
        return 2
    try:
        with psycopg.connect(url, connect_timeout=10, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.execute('SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = current_schema()')
                present = {row[0] for row in cursor.fetchall()}
                missing = [table for table in TABLES if table not in present]
                if missing:
                    print('[CONNECTED] PostgreSQL bereikbaar, maar tabellen ontbreken:', ', '.join(missing))
                    print('Dit is normaal vóór de eerste succesvolle botstart; bot maakt het schema aan.')
                else:
                    print('[OK] PostgreSQL verbonden. Alle 8 bot-tabellen bestaan.')
            return 0
    except Exception as exc:
        # Never print driver exceptions: they may include the connection URL / password.
        print('[ERROR] Databaseverbinding mislukt (' + type(exc).__name__ + ').')
        print('Controleer privé de connection string, SSL, database-status en netwerktoegang.')
        return 1


if __name__ == '__main__':
    sys.exit(check(os.getenv('DATABASE_URL', '').strip()))
