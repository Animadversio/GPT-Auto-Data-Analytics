import textwrap

def wrap_breakline(s, width=70):
    return "\n".join("\n".join(textwrap.wrap(x, width=width)) for x in s.splitlines())