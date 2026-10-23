# RadonClient Bot V2 — Broad Ticket Categories

Replaced the 24 module-heavy default ticket categories with 12 help-oriented categories: General Support; Installation & Setup; Technical Issues & Crashes; Client Bugs & Features; Licenses & Activation; Purchases, Payments & Refunds; Website & Account Help; Beta Testing Help; Discord & Bot Help; Giveaways & Rewards; Reports & Safety; Suggestions & Feedback.

The detailed English automatic ticket responder remains intact and may still recognize individual modules inside a ticket message. Existing nonempty custom `tickets.types` in configuration overrides the defaults. If `tickets.types` is empty, the 12 defaults appear.

Validation: 45 unittest cases passed and Python files compiled in this environment. Discord, Render, persistence and permission behavior have not been live-tested. Do not deploy over the working bot without a backup, and keep the old Render service suspended.
