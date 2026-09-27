def _face(eyes, mouth):
    return "\n".join([
        "        .-\"\"\"\"\"\"-.",
        "       /          \\",
        "      | %-9s |" % eyes,
        "      | %-9s |" % mouth,
        "      |   ------   |",
        "      \\    .._     /",
        "       '-._____.-'",
        "",
    ])


HEAD = _face(".  .", "--")


def state_face(state):
    faces = {
        "idle": ("o     o", "   -   "),
        "listening": ("o     o", "   v   "),
        "thinking": ("~     ~", "   .   "),
        "speaking": ("o     O", "   v   "),
    }
    eyes, mouth = faces.get(state, faces["idle"])
    return _face(eyes, mouth)