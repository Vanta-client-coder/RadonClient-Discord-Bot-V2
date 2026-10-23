"""Offline, privacy-conscious helpdesk matching; no AI key or external API required."""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Topic:
    title: str
    phrases: tuple
    advice: str


def topic(title, keywords, steps):
    return Topic(title, tuple(keywords.split('|')), steps)

TOPICS = (
    topic('Minecraft crashes on launch', 'crash on launch|crashes on startup|minecraft crashes|game crashes|exit code|exception|crash report|launcher crash|not launching|wont launch|won\'t launch',
          '1. Check that you selected **Minecraft Java 1.21.11**, **Fabric**, and **Java 21**.\n2. Temporarily move other mods out of the `mods` folder and retry with Radon only.\n3. Look for a specific error in the launcher or the latest crash report.\n4. Send the error text or relevant log lines (remove your username, paths and personal information).\n5. Tell us whether the crash happens before the menu, when joining a world, or after enabling a module.'),
    topic('Installing Radon Client', 'how to install|installation|install|download|setup|fabric loader|mod folder|mods folder|java 21|fabric version|jar file|where do i put',
          '1. Install a compatible **Fabric** profile for **Minecraft Java 1.21.11**.\n2. Confirm that Minecraft is using **Java 21**.\n3. Put the Radon mod `.jar` in your Minecraft `mods` folder; do not unpack the JAR.\n4. Remove older duplicate Radon JARs and restart Minecraft with Fabric selected.\n5. If it still fails, tell us exactly what appears in your launcher or mod list.'),
    topic('Updating or incompatible versions', 'update radon|new update|outdated|wrong version|incompatible|version mismatch|unsupported version|update client|new release',
          '1. Check the Minecraft and Fabric versions required by the Radon release.\n2. Download the correct version from your trusted Radon source.\n3. Remove the old Radon JAR before adding the new one.\n4. Restart Minecraft; avoid mixing different versions of the same mod.\n5. Tell us both your Minecraft version and the version of Radon you installed.'),
    topic('Fabric or mod conflicts', 'fabric error|mod conflict|conflicting mod|dependency|missing dependency|mixin|fabric api|mod incompatible|loader error',
          '1. Copy the exact Fabric or dependency error (without personal paths).\n2. Check the required game and loader versions.\n3. Temporarily test with Radon and only its required dependencies.\n4. Re-add other mods one by one to identify a conflict.\n5. Share the names and versions of mods that conflict.'),
    topic('Performance, lag or FPS', 'low fps|fps drop|fps drops|lag|lagging|stutter|stutters|freeze|freezing|performance|frame drop|high cpu|memory',
          '1. Tell us whether the issue happens in singleplayer, multiplayer or both.\n2. Check whether the problem starts when a particular module or overlay is enabled.\n3. Disable that feature briefly to compare performance.\n4. Report your Minecraft version, approximate FPS before/after, and any relevant log errors.\n5. Do not share private system or account information.'),
    topic('Flight or server movement', 'flight|fly mode|flying|rubberband|server kicks|movement correction|cant fly|cannot fly|teleport back',
          '1. Tell us whether Flight works in singleplayer but not on the server.\n2. Check whether the server permits flying; servers may enforce movement restrictions.\n3. Try with other movement-related modules disabled to identify a conflict.\n4. Describe whether the player is corrected, kicked, or the module simply has no effect.\n5. Share any non-sensitive kick/error message. We cannot promise flight will be permitted on every server.'),
    topic('Auto Crystal', 'auto crystal|autocrystal|crystal target|end crystal|obsidian crystal|crosshair crystal',
          '1. Confirm whether **Crosshair** mode is selected.\n2. Explain whether the module stays focused on an old crystal when you aim somewhere new.\n3. Tell us what happens when the previous crystal disappears or explodes.\n4. Include any visible settings and whether this happens in singleplayer or multiplayer.\n5. A short screen recording can help staff reproduce the target-switching problem.'),
    topic('Auto Anchor', 'auto anchor|autoanchor|respawn anchor|anchor place|anchor explode|anchor fire',
          '1. Describe whether the issue concerns placing, charging or triggering an anchor.\n2. Confirm the dimension and whether fire is occupying the target position.\n3. Note whether the module stops after a previous action or when switching targets.\n4. Share settings and steps to reproduce.\n5. Staff can check whether the behavior matches normal Minecraft placement rules.'),
    topic('Fast Break', 'fast break|fastbreak|instant mine|mining speed|break blocks|breaking blocks',
          '1. Say which block you were mining and which tool you used.\n2. Describe whether Fast Break changes only the animation or the actual break time.\n3. Compare behavior in singleplayer and on the affected server.\n4. Include the Fast Break settings and any other mining modules enabled.\n5. Servers may control breaking speed; share what you observe rather than expecting a guaranteed server-side effect.'),
    topic('Aim Helper', 'aim helper|aim assist|red circle|target aim|strength 100|aim strength',
          '1. Check that Aim Helper is enabled.\n2. Tell us whether the red crosshair circle appears.\n3. Explain whether the aim follows valid targets or becomes stuck on one target.\n4. Include Strength, range and target-filter settings.\n5. Share whether the issue affects players, mobs or both.'),
    topic('ESP and rendering', 'esp|hole esp|light debug|light finder|shulker preview|render overlay|highlight|flickering markers|wallhack',
          '1. Name the exact rendering module.\n2. Describe what you expected versus what appears on screen.\n3. Include render distance, overlay settings and whether you move when the issue occurs.\n4. Temporarily test without shader or other rendering mods.\n5. Provide a screenshot if possible, without exposing personal information.'),
    topic('Shield Breaker and combat', 'shield breaker|shieldbreaker|auto totem|totem|combat bug|shield stops|after respawn',
          '1. Name the combat module and whether it is still shown as enabled.\n2. Tell us if it stops after death or respawn.\n3. Check whether disabling and re-enabling temporarily changes the behavior.\n4. Include the module settings, game mode and target details.\n5. Staff can investigate stale state after respawning.'),
    topic('Keybinds and ClickGUI', 'keybind|key bind|hotkey|clickgui|click gui|gui setting|menu|category resets|settings reset|scroll position',
          '1. Identify the affected key or menu/category.\n2. Check whether another module uses the same keybind.\n3. Explain if the setting changes during play or after restarting Minecraft.\n4. Tell us the exact steps that reproduce the GUI issue.\n5. Please do not delete your saved configuration before staff helps.'),
    topic('Settings not saving', 'settings not saving|config resets|save settings|lost settings|reset after restart|preferences disappear|configuration lost',
          '1. Describe which setting is being reset and when.\n2. Close Minecraft normally and check whether the same issue happens after restarting.\n3. Avoid deleting config files or overwriting backups.\n4. Tell staff if this began after an update.\n5. Share only non-sensitive log output.'),
    topic('Licenses and activation', 'license|licence|activation|activate|redeem|key not working|invalid key|premium license|license expired',
          '1. Tell us the exact non-sensitive activation error.\n2. Check that you are signed into the intended account.\n3. Confirm whether the issue started after changing devices or reinstalling.\n4. Staff can check your license status through approved internal tools.\n5. **Never post your full license key, password or token in a ticket.**'),
    topic('Purchase and payment', 'payment|paid|purchase|billing|charged|checkout|buy premium|order failed|transaction',
          '1. Tell us what you were trying to purchase and roughly when.\n2. State whether payment was completed, pending or failed.\n3. Do not pay again just because confirmation is delayed.\n4. A staff member can review the purchase using approved records.\n5. **Never share full card numbers, payment credentials or private receipts publicly.**'),
    topic('Refund policy', 'refund|money back|cancel purchase|chargeback',
          '1. Radon Client does not offer refunds.\n2. If you have a payment error, duplicate charge or unauthorized transaction, describe what happened without sharing payment credentials.\n3. Staff can help review payment problems but cannot promise a refund.\n4. Never share card numbers, passwords or sensitive payment information.'),
    topic('Discord login and roles', 'discord login|discord oauth|login|log in|account|access denied|permission|role missing|cannot access|owner role',
          '1. Tell us where the login/access issue occurs (Discord, bot command or website).\n2. Copy the exact error text but **not** any token or code.\n3. Check that you are using the correct Discord account and server.\n4. If a bot command is blocked, name the command and expected role.\n5. Staff can verify permissions without asking for your password.'),
    topic('Website and Owner Studio', 'website|owner studio|beta testing|participate|beta application|announcement template|localhost|web page|owner code',
          '1. Identify the website page and the button or feature that is failing.\n2. Explain what should happen and what happens instead.\n3. Include the browser and whether the problem is local or on a hosted site.\n4. If possible, share an image with private values hidden.\n5. **Never send the Owner Security Code, Discord token or password.**'),
    topic('Tickets and Discord bot', 'ticket|support channel|giveaway|bot offline|bot status|heartbeat|slash command|discord bot',
          '1. Tell us which bot command, ticket feature or status message is affected.\n2. Copy the visible error without secrets.\n3. Describe whether it happens every time or only after a restart.\n4. Include when the issue began and the channel where it happened.\n5. Staff can inspect bot logs and permissions.'),
    topic('Account security', 'hacked|phishing|scam|stolen account|compromised|2fa|password reset|security',
          '1. Do **not** share passwords, recovery codes, tokens or private authentication links.\n2. Use the official account provider website to secure the account and enable two-factor authentication.\n3. If you suspect a stolen token, revoke or rotate it through the official service.\n4. Tell staff the general issue without posting private information.\n5. Staff cannot ask you for passwords or verification codes.'),
    topic('Downloading the client', 'download link|where to download|download page|download button|file missing|download stuck|download failed',
          '1. Use only the official Radon distribution channel or website.\n2. Confirm that the download is for your Minecraft version.\n3. If your browser reports an error, copy the warning text without bypassing security protections.\n4. Do not run files sent in private messages by unknown people.\n5. Staff can confirm the current approved download location.'),
    topic('Discord bot commands', 'command denied|command not working|bot command|help command|prefix command|command permission|slash commands missing',
          '1. Tell us which command you entered and where.\n2. Check that you are in the configured Radon Discord server.\n3. Verify that you have the assigned role for staff-only commands.\n4. Include the complete non-sensitive error message.\n5. Staff can review role IDs and the command access configuration.'),
    topic('Discord ticket problems', 'cant open ticket|cannot open ticket|ticket reaction|ticket panel|ticket button|ticket wont open|ticket channel missing',
          '1. Use the ticket panel or reaction in the intended channel.\n2. Check whether you already have an open ticket.\n3. Describe what happens after clicking or reacting.\n4. Avoid repeatedly creating duplicate tickets.\n5. A staff member can check ticket permissions and the ticket category.'),
    topic('Beta testing application', 'beta tester|beta application|participate button|apply for beta|beta signup|application declined|application pending',
          '1. Sign in with Discord on the Radon Website V100.\n2. Check whether beta applications are currently open.\n3. Enter your Minecraft Java username and complete all required questions.\n4. The application limit may be 50; a submission does not guarantee acceptance.\n5. Staff can explain the current status, but never share your password or login code.'),
    topic('Missing premium access', 'premium not showing|premium missing|radon plus missing|bought premium|no premium|premium role missing',
          '1. Confirm which account was used for the purchase or activation.\n2. Reopen the approved website and check the visible status.\n3. Avoid buying a second time while the first order is being reviewed.\n4. Do not post a full license key, payment card or password.\n5. Staff can verify entitlement through approved records.'),
    topic('Auto Totem', 'auto totem|autototem|totem switch|totem slot|totem not equipping',
          '1. Confirm Auto Totem is enabled and a totem is in your inventory.\n2. Tell us whether it fails on the first activation or after a death/respawn.\n3. Include the relevant module settings.\n4. Mention other inventory management modules you use.\n5. Staff can use reproduction steps to investigate.'),
    topic('Shulker Preview', 'shulker preview|shulker tooltip|shulker contents|shulker box preview',
          '1. Check whether Shulker Preview is enabled.\n2. Tell us if it fails with every shulker or only some.\n3. Test without conflicting inventory tooltip mods.\n4. Share the relevant settings and Minecraft version.\n5. Staff can help identify a display conflict.'),
    topic('Block Picker', 'block picker|pick block|middle click block|selected block wrong',
          '1. Confirm which block you are pointing at.\n2. Check the configured keybind.\n3. Describe the chosen block versus the expected block.\n4. Report whether it happens in Creative, Survival or both.\n5. Share module settings and steps to reproduce.'),
    topic('UI sounds', 'ui sounds|soundpack|hover sound|menu sounds|sound pack|gui click sound',
          '1. Check whether UI Sounds is enabled.\n2. Verify the selected soundpack and volume.\n3. Tell us whether clicks, hovers or both are silent.\n4. Test in the main ClickGUI navigation.\n5. Include your game version and any audio mods.'),
    topic('Deep Player Finder', 'deep player finder|player finder|find nearby players|player tracker',
          '1. Check that the module is enabled and configured.\n2. Tell us whether it detects no players or gives incorrect results.\n3. Describe the dimension and server environment.\n4. Include relevant range and visibility settings.\n5. Staff can review the tracker logic.'),
    topic('Suggestions and feature requests', 'suggestion|feature request|add feature|idea|improvement|could you add|new module',
          '1. Describe the feature you would like to see.\n2. Explain what problem it solves.\n3. Share an example of how it should work.\n4. Staff can review it; implementation and release dates are not guaranteed.'),
)

GENERIC = ('General support',
           'Thanks for reaching out. I could not confidently identify the issue yet.\n'
           '1. Tell us which Radon product or feature you are using.\n'
           '2. Explain what you expected and what actually happened.\n'
           '3. Share the exact non-sensitive error and steps to reproduce.\n'
           '4. Do not send passwords, license keys, payment details or tokens.')

# False positives from individual broad words are reduced by phrase-boundary checks.
def match_ticket_issue(message):
    clean = re.sub(r'\s+', ' ', str(message).casefold()).strip()
    if not clean:
        return GENERIC
    scored = []
    for index, entry in enumerate(TOPICS):
        hits = [phrase for phrase in entry.phrases if re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', clean)]
        if hits:
            score = sum(3 + len(phrase.split()) * 2 for phrase in hits)
            scored.append((score, max(map(len, hits)), -index, entry))
    if not scored:
        return GENERIC
    _, _, _, winning = max(scored)
    return winning.title, winning.advice
