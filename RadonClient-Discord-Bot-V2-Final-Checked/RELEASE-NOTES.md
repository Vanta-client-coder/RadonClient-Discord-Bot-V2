# RadonClient — New Render Deployment Package

Changes: unbuffered logging, disabled Render auto-deploy to avoid repeated accidental Discord logins, safer DM error logging, explicit configuration check, simplified post-ready token validation (gateway login already authenticates), diagnostic connection states, Render migration guide, config example and safety tests.

**Important source limitation:** The provided ZIP had no `config.json` or persistent `data/radon.db`. Copy the real existing configuration and data from your previous project/service. Do not use the example as a working configuration.

**Verification:** Syntax compilation and basic local safety tests passed. The existing `selftest.py` cannot pass without the missing original `config.json`. No real Discord or Render connection was tested. A new service might still receive Discord 429/Cloudflare 1015.
