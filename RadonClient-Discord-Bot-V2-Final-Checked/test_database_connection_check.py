import unittest
from unittest.mock import patch
from check_database import database_url_advice, check

class DatabaseConnectionCheckTests(unittest.TestCase):
    def test_missing_url(self):
        self.assertIn('ontbreekt', database_url_advice(''))
        self.assertEqual(check(''), 2)

    def test_rejects_invalid_url(self):
        self.assertIn('geldige', database_url_advice('https://example.com'))

    def test_session_pooler(self):
        self.assertEqual(database_url_advice('postgresql://user:secret@host:5432/postgres?sslmode=require'), 'OK')

    def test_transaction_pooler_warning(self):
        self.assertIn('Session pooler', database_url_advice('postgresql://u:p@host:6543/postgres?sslmode=require'))

    def test_missing_ssl_warning(self):
        self.assertIn('sslmode', database_url_advice('postgresql://u:p@host/postgres'))

if __name__ == '__main__':
    unittest.main()
