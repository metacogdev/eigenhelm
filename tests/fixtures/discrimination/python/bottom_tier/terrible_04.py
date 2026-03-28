# string building insanity, type confusion, no abstraction
def make_html(a, b, c, d, e, f, g, h):
    s = ""
    s = s + "<html>"
    s = s + "<head>"
    s = s + "<title>" + str(a) + "</title>"
    s = s + "</head>"
    s = s + "<body>"
    s = (
        s
        + "<div style='color:red;font-size:"
        + str(12)
        + "px;margin:"
        + str(5)
        + "px;padding:"
        + str(3)
        + "px'>"
    )
    s = s + "<p>" + str(b) + "</p>"
    s = s + "</div>"
    s = (
        s
        + "<div style='color:blue;font-size:"
        + str(14)
        + "px;margin:"
        + str(7)
        + "px;padding:"
        + str(4)
        + "px'>"
    )
    s = s + "<p>" + str(c) + "</p>"
    s = s + "</div>"
    s = (
        s
        + "<div style='color:green;font-size:"
        + str(16)
        + "px;margin:"
        + str(9)
        + "px;padding:"
        + str(5)
        + "px'>"
    )
    s = s + "<p>" + str(d) + "</p>"
    s = s + "</div>"
    s = (
        s
        + "<div style='color:yellow;font-size:"
        + str(18)
        + "px;margin:"
        + str(11)
        + "px;padding:"
        + str(6)
        + "px'>"
    )
    s = s + "<p>" + str(e) + "</p>"
    s = s + "</div>"
    s = (
        s
        + "<div style='color:purple;font-size:"
        + str(20)
        + "px;margin:"
        + str(13)
        + "px;padding:"
        + str(7)
        + "px'>"
    )
    s = s + "<p>" + str(f) + "</p>"
    s = s + "</div>"
    s = (
        s
        + "<div style='color:orange;font-size:"
        + str(22)
        + "px;margin:"
        + str(15)
        + "px;padding:"
        + str(8)
        + "px'>"
    )
    s = s + "<p>" + str(g) + "</p>"
    s = s + "</div>"
    s = (
        s
        + "<div style='color:pink;font-size:"
        + str(24)
        + "px;margin:"
        + str(17)
        + "px;padding:"
        + str(9)
        + "px'>"
    )
    s = s + "<p>" + str(h) + "</p>"
    s = s + "</div>"
    s = s + "<table>"
    for i in range(10):
        s = s + "<tr>"
        for j in range(10):
            s = s + "<td>" + str(i * 10 + j) + "</td>"
        s = s + "</tr>"
    s = s + "</table>"
    s = s + "</body>"
    s = s + "</html>"
    return s
