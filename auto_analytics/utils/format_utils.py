import textwrap
from IPython.display import display, Math, Markdown, Code
from auto_analytics.utils.json_utils import parse_partial_json

def wrap_breakline(s, width=70):
    return "\n".join("\n".join(textwrap.wrap(x, width=width)) for x in s.splitlines())


def replace_equsymbol_markdown(message):
    return message.replace("\(", "$").replace("\)", "$").\
                 replace("\[", "$$").replace("\]", "$$")
                 

def message_thread_render(messages):
    for message in messages:
        # if isinstance(message, dict):
        print(dict(message)["role"].upper())
        display(Markdown(replace_equsymbol_markdown(dict(message)["content"])))
        if "tool_calls" in dict(message) and message.tool_calls is not None:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                function_args = parse_partial_json(tool_call.function.arguments)
                print("Called tool: ", tool_name.upper())
                if "code" in function_args:
                    display(Code(function_args["code"], language="python"))
                else:
                    print(function_args)
                # print(function_args)
            