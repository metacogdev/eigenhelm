def build_html(tag, content="", attrs=None, children=None):
    """Build HTML string. String concatenation instead of proper templating."""
    html = "<" + tag
    if attrs:
        for key in attrs:
            html += " " + key + '="' + str(attrs[key]) + '"'
    html += ">"

    if content:
        html += str(content)

    if children:
        for child in children:
            if isinstance(child, str):
                html += child
            elif isinstance(child, dict):
                child_tag = child.get("tag", "div")
                child_content = child.get("content", "")
                child_attrs = child.get("attrs", None)
                child_children = child.get("children", None)
                html += build_html(
                    child_tag, child_content, child_attrs, child_children
                )
            elif isinstance(child, tuple):
                if len(child) >= 2:
                    html += build_html(child[0], child[1])
                elif len(child) == 1:
                    html += build_html(child[0])

    html += "</" + tag + ">"
    return html
