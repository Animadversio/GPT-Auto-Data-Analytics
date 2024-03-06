
import os
import sys
import textwrap
from openai import OpenAI
import IPython
from IPython.core.interactiveshell import InteractiveShell
from auto_analytics.utils.json_utils import parse_partial_json
from auto_analytics.utils.ipython_utils import richoutput_to_image
from auto_analytics.utils.format_utils import wrap_breakline

client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)

system_message = """You are an intelligent assistent with access to a running ipython kernel. 
You can use `python_code_exec` to execute python code to solve computational problems and return the output. 
You can also use `inspect_variable` to inspect the state of the kernel by getting the value of a variable. 
You should use `seek_human_input` when analysis finishes. When you stuck, use this function to ask human for clarification, instruction.
These functions execute code in local terminal with no cost, you can use them as many times as you want.
When facing complex problems, you can divide them into smaller problems and run code to solve smaller ones, check the returned results and then solve the more complex one.
"""

codeexec_functions = [
    {
        'name': 'python_code_exec',
        'description': 'Execute python code to solve computational problems and return the output',
        'parameters': {
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'string',
                    'description': 'Python code to execute, multiline string supported.'
                },
            }
        }
    },
    {
        'name': 'inspect_variable',
        'description': 'Get the value of a variable from the kernel. Used to inspect the state of the kernel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'var_name': {
                    'type': 'string',
                    'description': 'Name of the variable to get the value of.'
                },
            }
        }
    },
    {
        'name': 'seek_human_input',
        'description': 'When analysis finishes, stuck or is exhausted, ask human for clarification, instruction for further progress.',
        'parameters': {
            'type': 'object',
            'properties': {
                'question': {
                    'type': 'string',
                    'description': 'Question for human to progress and get unstuck.'
                },
            }
        }
    }
]

codeexec_tools = [
        {
            "type": "function",
            "function": codeexec_functions[0]
        }
    ]

# Step 0: define the python functions. 
def python_code_exec(code, verbose=False):
    with IPython.utils.io.capture_output() as captured:
        # Execute the code
        out = shell.run_cell(code)
    # except Exception as e:
    #     results = f"query failed with error: {e}"
    if verbose:
        print("Result of the code execution: ", type(out.result), "\n", out.result)
        print("Standard Output:", captured.stdout)
        print("Standard Error:", captured.stderr)
        print("Captured Outputs:", captured.outputs)
    disp_images = []
    if captured.outputs:
        for display_output in captured.outputs:
            # Process each display output as needed
            disp_images.append(richoutput_to_image(display_output))
    return out, captured, disp_images


def inspect_variable(var_name):
    return shell.user_ns[var_name]


def seek_human_input(question):
    return question    

# start the ipython kernel
shell = InteractiveShell.instance()

available_functions = {
                    "python_code_exec": python_code_exec,
                    "inspect_variable": inspect_variable,
                    "seek_human_input": seek_human_input
                }  

MAX_ROUND = 4
# model_name = 'gpt-3.5-turbo-1106' # "gpt-4-turbo-preview"
# question = "We have already loaded a dataframe `df` in the kernel. Do not reload this. Each row denotes one model and its performance. find the best performing 10 models and summarize their similarities in time window"
def tool_chat_loop(question, model_name='gpt-3.5-turbo-1106', 
                   available_functions=available_functions, 
                   codeexec_tools=codeexec_tools, MAX_ROUND=4):
    # Step 1: send the conversation and available functions to the model
    messages = [
            {'role': 'system', 'content': system_message}, 
            {'role': 'user', 'content': question}
        ]
    # this flag allows us to break out of the loop when human input is needed.
    LOOP_END = False 
    for iteration in range(MAX_ROUND):
        response = client.chat.completions.create(
            model = model_name, 
            messages = messages,
            tools = codeexec_tools,
            tool_choice = 'auto',  # auto is default, but we'll be explicit
        )
        response_message = response.choices[0].message
        messages.append(response_message)  # extend conversation with assistant's reply
        tool_calls = response_message.tool_calls
        if response_message.content:
            print(wrap_breakline(response_message.content, width=80))
        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # iterate over all the function calls
            for tool_call in tool_calls:
                # Parse the function call
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                # Note: the JSON response may not always be valid; be sure to handle errors
                # function_args = json.loads(tool_call.function.arguments)
                function_args = parse_partial_json(tool_call.function.arguments)
                # Step 3: call the function
                if function_name == "python_code_exec":
                    out, captured, disp_images = function_to_call(*list(function_args.values()))
                    print("Python Code executed:\n```python", function_args['code'], "```", sep="\n")
                    if not out.success:
                        # if not success, return the error message as function response. 
                        print("Execution error:",  out.error_in_exec.__class__.__name__, out.error_in_exec)
                        function_response = "Execution error: %s : %s" % (out.error_in_exec.__class__.__name__, out.error_in_exec)
                    else:
                        # if success return the output as function response.
                        print("Execution Succeed:")
                        captured.show()
                        if captured.stdout:
                            function_response = captured.stdout
                        elif captured.outputs:
                            function_response = captured.outputs[0].data['text/plain']
                        else:
                            function_response = "Multimedia output e.g. image and code."
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": function_response,
                        }
                    )  # extend conversation with function response
                    LOOP_END = False
                elif function_name == "inspect_variable":
                    insp_var = function_to_call(*list(function_args.values()))
                    print("Variable inspected:", function_args['var_name'])
                    print(insp_var)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": insp_var.__repr__(),
                        }
                    )
                    LOOP_END = False
                elif function_name == "seek_human_input":
                    print(f"[Loop end, human input needed]\nAI request {list(function_args.values())}")
                    LOOP_END = True
            if LOOP_END:
                break
            # Step 4: send the info for each function call and function response to the model
            second_response = client.chat.completions.create(
                model=model_name,
                messages=messages,
            )  
            # get a new response from the model where it can see the function response
            response_message_w_func = second_response.choices[0].message
            print(wrap_breakline(response_message_w_func.content, width=80))
            messages.append(response_message_w_func)
        else:
            print("[No tool use. Finishing conversation.]")
            break
    return messages


def tool_chat_loop_2(question, model_name='gpt-3.5-turbo-1106', 
                   available_functions=available_functions, 
                   codeexec_tools=codeexec_tools, MAX_ROUND=4, chat_history=None):
    # Step 1: send the conversation and available functions to the model
    if chat_history is None:
        messages = [
                {'role': 'system', 'content': system_message}, 
                {'role': 'user', 'content': question}
            ]
    else:
        messages = chat_history
        messages.append({'role': 'user', 'content': question})
    # this flag allows us to break out of the loop when human input is needed.
    LOOP_END = False 
    for iteration in range(MAX_ROUND):
        response = client.chat.completions.create(
            model = model_name, 
            messages = messages,
            tools = codeexec_tools,
            tool_choice = 'auto',  # auto is default, but we'll be explicit
        )
        response_message = response.choices[0].message
        # extract token count
        # token_count = response_message.token_count
        messages.append(response_message)  # extend conversation with assistant's reply
        tool_calls = response_message.tool_calls
        if response_message.content:
            print(wrap_breakline(response_message.content, width=80))
        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # iterate over all the function calls
            for tool_call in tool_calls:
                # Parse the function call
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                # Note: the JSON response may not always be valid; be sure to handle errors
                # function_args = json.loads(tool_call.function.arguments)
                function_args = parse_partial_json(tool_call.function.arguments)
                # Step 3: call the function
                if function_name == "python_code_exec":
                    out, captured, disp_images = function_to_call(*list(function_args.values()))
                    print("Python Code executed:\n```python", function_args['code'], "```", sep="\n")
                    if not out.success:
                        # if not success, return the error message as function response. 
                        print("Execution error:",  out.error_in_exec.__class__.__name__, out.error_in_exec)
                        function_response = "Execution error: %s : %s" % (out.error_in_exec.__class__.__name__, out.error_in_exec)
                    else:
                        # if success return the output as function response.
                        print("Execution Succeed:")
                        captured.show()
                        if captured.stdout:
                            function_response = captured.stdout
                        elif captured.outputs:
                            function_response = captured.outputs[0].data['text/plain']
                        else:
                            function_response = "Multimedia output e.g. image and code."
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": function_response,
                        }
                    )  # extend conversation with function response
                    LOOP_END = False
                elif function_name == "inspect_variable":
                    insp_var = function_to_call(*list(function_args.values()))
                    print("Variable inspected:", function_args['var_name'])
                    print(insp_var)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": insp_var.__repr__(),
                        }
                    )
                    LOOP_END = False
                elif function_name == "seek_human_input":
                    print(f"[Loop end, human input needed]\nAI request {list(function_args.values())}")
                    LOOP_END = True
            if LOOP_END:
                break
            # # Step 4: send the info for each function call and function response to the model
            # second_response = client.chat.completions.create(
            #     model=model_name,
            #     messages=messages,
            # )  
            # # get a new response from the model where it can see the function response
            # response_message_w_func = second_response.choices[0].message
            # print(wrap_breakline(response_message_w_func.content, width=80))
            # messages.append(response_message_w_func)
        else:
            print("[No tool use. Finishing conversation.]")
            break
    return messages