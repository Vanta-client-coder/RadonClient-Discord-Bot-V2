from html import escape
from pathlib import Path


async def create_html_transcript(channel, ticket, closed_by):
    rows = []
    async for msg in channel.history(limit=None, oldest_first=True):
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        content = escape(msg.content or "")
        attachments = " ".join(escape(a.url) for a in msg.attachments)
        if attachments:
            content += f"<br><small>Attachments: {attachments}</small>"
        if not content:
            content = "<i>No text content</i>"
        rows.append(
            f"<div class='msg'><b>{escape(str(msg.author))}</b> "
            f"<span>{timestamp}</span><br>{content}</div>"
        )

    claimed_by = ticket["claimed_by"] or "Not claimed"
    html = f"""<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>Radon Ticket Transcript</title>
<style>
body{{font-family:Arial,sans-serif;background:#0f1115;color:#e7e7e7;padding:24px;line-height:1.45}}
h1{{color:#20D5DD;margin-bottom:12px}}
.meta{{background:#171b22;padding:14px;border-radius:8px;margin-bottom:18px}}
.msg{{padding:10px 0;border-bottom:1px solid #2b3038}}
span,small{{color:#999}}
</style>
</head>
<body>
<h1>Radon Ticket Transcript</h1>
<div class='meta'>
Owner ID: {escape(str(ticket['owner_id']))}<br>
Type: {escape(str(ticket['type_id']))}<br>
Claimed by: {escape(str(claimed_by))}<br>
Closed by: {escape(str(closed_by))}<br>
Opened at: {escape(str(ticket['opened_at']))}
</div>
{''.join(rows)}
</body>
</html>"""

    out_dir = Path(__file__).resolve().parent.parent / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"ticket-{channel.id}.html"
    path.write_text(html, encoding="utf-8")
    return path
