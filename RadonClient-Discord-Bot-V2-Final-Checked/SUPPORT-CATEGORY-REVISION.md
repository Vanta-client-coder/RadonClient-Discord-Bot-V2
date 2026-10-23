# RadonClient Bot V2 — ticket category revision

- Removed **Discord & Bot Help** as a standalone ticket category.
- Renamed **Purchases, Payments & Refunds** to **Purchases & Payments**.
- Refunds are not offered. The auto-responder now states that policy and still provides guidance for payment errors, duplicate charges, or unauthorized transactions.
- The existing Discord bot capabilities and internal support topic matching remain intact.
- This changes default ticket categories only. Explicit ticket types already configured in `RADON_CONFIG_JSON` take precedence. To use the new defaults, leave `tickets.types` as `[]`.
- No live Discord/Render tests performed. Back up working deployment before changes.
