"""GitHub source positions use physical LF lines, not Unicode text separators."""


def source_lines(text):
    lines=text.split('\n')
    if lines[-1]=='':
        lines.pop()
    return [line[:-1] if line.endswith('\r') else line for line in lines]
