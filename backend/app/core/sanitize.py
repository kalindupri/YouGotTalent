import bleach

# A branded contract only ever needs basic document formatting — this allowlist blocks
# script/style/event-handler injection from a rich-text editor's HTML output before it's
# stored and later rendered (unescaped) for the other party to view.
_ALLOWED_TAGS = ["p", "br", "strong", "b", "em", "i", "u", "h2", "h3", "ul", "ol", "li", "blockquote"]


def sanitize_contract_html(html: str) -> str:
    return bleach.clean(html, tags=_ALLOWED_TAGS, attributes={}, strip=True)
