"""Broad help-oriented ticket categories, not one category per game module.

Existing explicitly configured ticket types always take priority.
"""

DEFAULT_TICKET_TYPES = (
    {'id': 'general', 'label': 'General Support', 'description': 'Questions and other help', 'openingPrompt': 'Tell us what you need help with and what you have already tried.'},
    {'id': 'install', 'label': 'Installation & Setup', 'description': 'Minecraft, Fabric and Java setup', 'openingPrompt': 'Tell us your Minecraft, Fabric, Java and Radon versions and where setup goes wrong.'},
    {'id': 'technical', 'label': 'Technical Issues & Crashes', 'description': 'Crashes, lag and incompatible mods', 'openingPrompt': 'Explain the problem, when it occurs and include a redacted error log if possible.'},
    {'id': 'client-bugs', 'label': 'Client Bugs & Features', 'description': 'Modules, GUI and settings not working', 'openingPrompt': 'Name the affected feature or module, describe what happens and how to reproduce it.'},
    {'id': 'license', 'label': 'Licenses & Activation', 'description': 'Keys, activation and access', 'openingPrompt': 'Explain the activation issue without sharing your full license key.'},
    {'id': 'billing', 'label': 'Purchases & Payments', 'description': 'Orders and payment questions (refunds are not offered)', 'openingPrompt': 'Describe your question without sharing payment card details or private credentials.'},
    {'id': 'website', 'label': 'Website & Account Help', 'description': 'Website login and account problems', 'openingPrompt': 'Tell us which page or account step fails and any safe-to-share error.'},
    {'id': 'beta', 'label': 'Beta Testing Help', 'description': 'Applications and beta participation', 'openingPrompt': 'Explain which part of beta signup, participation or review you need help with.'},
    {'id': 'giveaway', 'label': 'Giveaways & Rewards', 'description': 'Entries, winners and prizes', 'openingPrompt': 'Tell us the giveaway or reward involved and what assistance you need.'},
    {'id': 'report', 'label': 'Reports & Safety', 'description': 'Report abuse or security concerns', 'openingPrompt': 'Provide relevant evidence or message links without exposing personal or secret information.'},
    {'id': 'feedback', 'label': 'Suggestions & Feedback', 'description': 'Ideas and improvements', 'openingPrompt': 'Describe your idea or feedback and why it would be useful.'},
)


def effective_ticket_types(config):
    types = (config.get('tickets') or {}).get('types')
    if isinstance(types, list) and types:
        return types
    return list(DEFAULT_TICKET_TYPES)
