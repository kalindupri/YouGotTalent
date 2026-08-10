import html

from app.core.config import settings

# Brand colors mirrored from the frontend's dark professional masthead (rose-600 accent,
# zinc-950/zinc-900 dark surfaces) so transactional email matches the product's look.
_ROSE = "#e11d48"
_ZINC_950 = "#09090b"
_ZINC_600 = "#52525b"
_ZINC_200 = "#e4e4e7"


def _text_to_html_paragraphs(body: str) -> str:
    """Converts a plain-text email body (blank-line-separated paragraphs, as every call site
    already writes) into escaped <p> tags — escaping first is what keeps user-supplied text
    (a booking message, an application note) from being interpreted as markup once it's
    rendered as HTML instead of plain text.
    """
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    return "".join(
        f'<p style="margin:0 0 16px;line-height:1.6;">{html.escape(p).replace(chr(10), "<br/>")}</p>' for p in paragraphs
    )


def render_branded_email(subject: str, body_html: str) -> str:
    """Wraps a body of already-escaped HTML in the shared branded template. Inline styles only
    — email clients strip <style> blocks and many block remote assets, so this deliberately
    avoids external CSS, fonts, or images (the wordmark is styled text, not a hosted logo).
    """
    return f"""<!doctype html>
<html>
<body style="margin:0;padding:0;background-color:{_ZINC_200};font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{_ZINC_200};padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;border-radius:12px;overflow:hidden;">
          <tr>
            <td style="background-color:{_ZINC_950};padding:20px 28px;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background-color:{_ROSE};border-radius:4px;width:32px;height:32px;text-align:center;vertical-align:middle;">
                    <span style="color:#ffffff;font-weight:900;font-size:14px;">YT</span>
                  </td>
                  <td style="padding-left:10px;color:#ffffff;font-weight:900;font-size:16px;letter-spacing:0.02em;text-transform:uppercase;">
                    YouGotTalent
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 28px;">
              <h1 style="margin:0 0 16px;font-size:20px;font-weight:800;color:{_ZINC_950};">{html.escape(subject)}</h1>
              <div style="font-size:14px;color:{_ZINC_950};">{body_html}</div>
            </td>
          </tr>
          <tr>
            <td style="background-color:#fafafa;padding:20px 28px;border-top:1px solid {_ZINC_200};">
              <p style="margin:0;font-size:12px;color:{_ZINC_600};">
                YouGotTalent — Every skill. One stage.<br/>
                <a href="{html.escape(settings.FRONTEND_URL)}" style="color:{_ZINC_600};">{html.escape(settings.FRONTEND_URL)}</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
