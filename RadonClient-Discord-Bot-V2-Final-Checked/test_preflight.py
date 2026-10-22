import os
import unittest
from unittest.mock import patch
from preflight import assess

class PreflightTests(unittest.TestCase):
    def test_missing_token_reports_error_without_value(self):
        with patch.dict(os.environ, {'DISCORD_TOKEN':'', 'RADON_CONFIG_JSON':'{}'}, clear=True):
            errors, warnings = assess()
        self.assertTrue(any('DISCORD_TOKEN' in x for x in errors))
    def test_invalid_json_does_not_echo_secrets(self):
        with patch.dict(os.environ, {'DISCORD_TOKEN':'private-token-value', 'RADON_CONFIG_JSON':'{secret-value'}, clear=True):
            errors, warnings = assess()
        self.assertTrue(any('Configuration unavailable' in x for x in errors))
        self.assertNotIn('private-token-value', repr(errors))
        self.assertNotIn('secret-value', repr(errors))

if __name__ == '__main__': unittest.main()
