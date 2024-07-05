from pathlib import Path

from langchain import PromptTemplate
from langchain.prompts import HumanMessagePromptTemplate, AIMessagePromptTemplate, SystemMessagePromptTemplate


def print_code(code, name=None, force_color=False):
    import sys

    to_print = None
    if sys.stdout.isatty() or force_color:
        try:
            from pygments import highlight
            from pygments.lexers import PythonLexer
            from pygments.formatters import TerminalFormatter
            to_print = highlight(code, PythonLexer(), TerminalFormatter())
        except ImportError:
            pass

    if to_print is None:
        to_print = code

    if name:
        print(f'{name}:\n\n{to_print}\n')
    else:
        print(f'\n\n{to_print}\n')


def load_chat_messages_from_txt(f: Path):
    messages = []
    lines = f.read_text().splitlines()
    current_msg_text = ''
    current_msg_type = None
    signal_words = {
        'Human: ': HumanMessagePromptTemplate,
        'AI: ': AIMessagePromptTemplate,
        'System: ': SystemMessagePromptTemplate
    }

    def flush():
        if current_msg_type is not None:
            messages.append(current_msg_type(prompt=PromptTemplate(
                input_variables=[], validate_template=False, template_format='jinja2',
                template=current_msg_text)))

    for line in lines:
        found_kw = None
        for keyword, t in signal_words.items():
            if line.startswith(keyword):
                flush()
                current_msg_type = t
                found_kw = keyword
        if found_kw:
            current_msg_text = line[len(found_kw):]
        else:
            current_msg_text += '\n' + line
    flush()
    return messages
