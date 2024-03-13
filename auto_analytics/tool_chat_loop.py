
import os
import sys
import textwrap
import time
import copy
import openai_multi_tool_use_parallel_patch
from openai import OpenAI
import IPython
from IPython.core.interactiveshell import InteractiveShell
from auto_analytics.utils.json_utils import parse_partial_json
from auto_analytics.utils.ipython_utils import richoutput_to_image
from auto_analytics.utils.format_utils import wrap_breakline
from auto_analytics.vision_chat_loop import vision_qa_response

client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)

system_message = """You are an intelligent assistent with access to a running ipython kernel. 
You can use `python_code_exec` to execute python code to solve computational problems and return the output. 
You can also use `inspect_variable` to inspect the state of the kernel by getting the value of a variable. 
You should use `seek_human_input` when analysis finishes. When you stuck, use this function to ask human for clarification, instruction.
These functions execute code in local terminal with no cost, you can use them as many times as you want.
When facing complex problems, you can divide them into smaller problems and run code to solve smaller ones, check the returned results and then solve the more complex one.

Under no circumstances should you attempt to call functions / tools that are not available to you.
Any functions / tools you do call must have the name satisfy the following regex: ^[a-zA-Z0-9_-]{1,64}$
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
def tool_chat_loop_obsolete(question, model_name='gpt-3.5-turbo-1106', 
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
        if question is None:
            messages = chat_history
        else:
            messages = chat_history
            # decide if the final message is asking for human input, 
            # then append the question as result to that. 
            if dict(messages[-1])["role"] == "assistant" and \
                chat_history[-1].tool_calls and \
                (chat_history[-1].tool_calls[-1].function.name == "seek_human_input"):
                print("[put the question as human input]")
                messages.append({
                    "role": "tool",
                    "tool_call_id": chat_history[-1].tool_calls[-1].id,
                    "name": "seek_human_input",
                    "content": question
                })
            else:
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

tool_chat_loop = tool_chat_loop_2
from nbformat.v4 import new_notebook, new_code_cell, new_output, new_markdown_cell
from auto_analytics.utils.nbformat_utils import create_code_cell_from_captured, save_cells_to_nb
from auto_analytics.utils.nbformat_utils import convert_notebook_to_html, convert_notebook_to_pdf
def tool_chat_loop_2nb(question, model_name='gpt-3.5-turbo-1106', 
                   available_functions=available_functions, 
                   codeexec_tools=codeexec_tools, MAX_ROUND=15, 
                   chat_history=None, nbcells=None):
    # Step 1: send the conversation and available functions to the model
    cell_cache = []
    if nbcells is None:
        nbcells = []
    else:
        nbcells = nbcells
    if chat_history is None:
        messages = [
                {'role': 'system', 'content': system_message}, 
                {'role': 'user', 'content': question}
            ]
    else:
        if question is None:
            messages = chat_history
        else:
            messages = chat_history
            # decide if the final message is asking for human input, 
            # then append the question as result to that. 
            if dict(messages[-1])["role"] == "assistant" and \
                chat_history[-1].tool_calls and \
                (chat_history[-1].tool_calls[-1].function.name == "seek_human_input"):
                print("[put the question as human input]")
                messages.append({
                    "role": "tool",
                    "tool_call_id": chat_history[-1].tool_calls[-1].id,
                    "name": "seek_human_input",
                    "content": question
                })
            else:
                messages.append({'role': 'user', 'content': question})
    # add the user input as markdown cell
    nbcells.append(new_markdown_cell(source="**User**:\n"+question))
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
        if response_message.content:
            print(wrap_breakline(response_message.content, width=80))
            nbcells.append(new_markdown_cell(source="**Assistant**:\n"+response_message.content))
            
        tool_calls = response_message.tool_calls
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
                    code_cell_out = create_code_cell_from_captured(function_args['code'], out, captured)
                    cell_cache.append((function_args['code'], out, captured))
                    nbcells.append(code_cell_out)
                    LOOP_END = False
                # elif function_name == "inspect_variable":
                #     insp_var = function_to_call(*list(function_args.values()))
                #     print("Variable inspected:", function_args['var_name'])
                #     print(insp_var)
                #     messages.append(
                #         {
                #             "role": "tool",
                #             "tool_call_id": tool_call.id,
                #             "name": function_name,
                #             "content": insp_var.__repr__(),
                #         }
                #     )
                #     LOOP_END = False
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
    return messages, nbcells, cell_cache


def tool_chat_loop_2nb_with_vision(question, model_name='gpt-3.5-turbo-1106', 
                   available_functions=available_functions, 
                   codeexec_tools=codeexec_tools, MAX_ROUND=15, 
                   chat_history=None, nbcells=None,
                   enable_vision=False, vision_token_count=1024):
    # Step 1: send the conversation and available functions to the model
    cell_cache = []
    if nbcells is None:
        nbcells = []
    else:
        nbcells = nbcells
    if chat_history is None:
        messages = [
                {'role': 'system', 'content': system_message}, 
                {'role': 'user', 'content': question}
            ]
    elif type(chat_history) == list and len(chat_history) == 0:
        messages = chat_history
        messages.extend([
                {'role': 'system', 'content': system_message}, 
                {'role': 'user', 'content': question}
            ])
    else:
        if question is None:
            messages = chat_history
        else:
            messages = chat_history
            # decide if the final message is asking for human input, 
            # then append the question as result to that. 
            if dict(messages[-1])["role"] == "assistant" and \
                chat_history[-1].tool_calls and \
                (chat_history[-1].tool_calls[-1].function.name == "seek_human_input"):
                print("[put the question as human input]")
                messages.append({
                    "role": "tool",
                    "tool_call_id": chat_history[-1].tool_calls[-1].id,
                    "name": "seek_human_input",
                    "content": question
                })
            else:
                messages.append({'role': 'user', 'content': question})
    # add the user input as markdown cell
    nbcells.append(new_markdown_cell(source="**User**:\n"+question))
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
        if response_message.content:
            print(wrap_breakline(response_message.content, width=80))
            nbcells.append(new_markdown_cell(source="**Assistant**:\n"+response_message.content))
            
        tool_calls = response_message.tool_calls
        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # iterate over all the function calls
            for tool_call in tool_calls:
                # Parse the function call
                function_name = tool_call.function.name
                if function_name not in available_functions:
                    print(f"{function_name} called by agent, which is not available. Use quick hacky fix")
                    # quick fix for the function not available. 
                    # 'multi_tool_use.parallel' issue may need separate handling.
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": "Function not available. Please call sequentially. Available functions are: " + \
                                ", ".join(available_functions.keys()),
                        }
                    )
                    continue
                function_to_call = available_functions[function_name]
                # Note: the JSON response may not always be valid; be sure to handle errors
                # function_args = json.loads(tool_call.function.arguments)
                function_args = parse_partial_json(tool_call.function.arguments)
                # Step 3: call the function
                if function_name == "python_code_exec":
                    vision_api_messages = []
                    out, captured, disp_images = function_to_call(*list(function_args.values()))
                    print("Python Code executed:\n```python", function_args['code'], "```", sep="\n")
                    code2run = function_args['code']
                    if not out.success:
                        # if execution not success, return the error message as function response. 
                        print("Execution error:",  out.error_in_exec.__class__.__name__, out.error_in_exec)
                        function_response = "Execution error: %s : %s" % (out.error_in_exec.__class__.__name__, out.error_in_exec)
                    else:
                        # if execution success, return the output as function response.
                        print("Execution Succeed:")
                        # first show the captured outputs to the user in current notebook. 
                        captured.show()
                        function_response = ""
                        if captured.stdout:
                            function_response += captured.stdout
                        # reconsider the logic of streaming capturing outputs to model. 
                        if captured.outputs:
                            # function_response = captured.outputs[0].data['text/plain']
                            for outi, output in enumerate(captured.outputs):
                                if hasattr(output, "data"):
                                    if 'text/plain' in output.data:
                                        function_response += output.data['text/plain'] + "\n"
                                        # print(output.data['text/plain'])
                                    if 'text/html' in output.data:
                                        function_response += output.data['text/html'] + "\n"
                                        # print(output.data['text/html'])
                                    if "image/png" in output.data:
                                        image = richoutput_to_image(output)
                                        if enable_vision:
                                            #TODO: maybe resize oversized images. 
                                            image_encoded = output.data['image/png']
                                            vision_prompt = f"Describe the figure from a data analysis notebook "\
                                                f"generated from the code {code2run}. Try to draw some insights from the figure."
        
                                            t0 = time.time()
                                            vision_api_message = vision_qa_response(vision_prompt, 
                                                        image_encoded, img_fmt='image/png', 
                                                        max_tokens=vision_token_count, display_output=False)
                                            t1 = time.time()
                                            
                                            print("Vision API response time:", t1-t0)
                                            function_response += "**Visual Analyst Figure Description**:\n" + \
                                                                 vision_api_message.content
                                            print(wrap_breakline("**Visual Analyst Figure Description**:\n" + 
                                                                 vision_api_message.content, width=80))
                                            vision_api_messages.append(vision_api_message)
                                    if ('text/plain' not in output.data) and \
                                        ('text/html' not in output.data) and \
                                        ("image/png" not in output.data):
                                        print("output data not recognized !!!")
                                        print(output.data)
                                        # print(output.data)
                                else:
                                    print("output has no data !!!")
                                    print(output)
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
                    code_cell_out = create_code_cell_from_captured(function_args['code'], out, captured)
                    nbcells.append(code_cell_out)
                    for vision_api_message in vision_api_messages:
                        nbcells.append(new_markdown_cell(source="**Vision Analyst Response**: \n"+vision_api_message.content))
                    cell_cache.append((function_args['code'], out, captured, copy.deepcopy(vision_api_messages)))
                    LOOP_END = False
                # elif function_name == "inspect_variable":
                #     insp_var = function_to_call(*list(function_args.values()))
                #     print("Variable inspected:", function_args['var_name'])
                #     print(insp_var)
                #     messages.append(
                #         {
                #             "role": "tool",
                #             "tool_call_id": tool_call.id,
                #             "name": function_name,
                #             "content": insp_var.__repr__(),
                #         }
                #     )
                #     LOOP_END = False
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
    return messages, nbcells, cell_cache

class DataAnalysisAgent:
    
    def __init__(self, model_name='gpt-3.5-turbo-1106', 
                 codeexec_tools=codeexec_tools,
                 available_functions=available_functions):
        self.model_name = model_name
        self.messages = []
        self.nbcells = []
        self.cell_cache = []
        self.codeexec_tools = codeexec_tools
        self.available_functions = available_functions
    
    def chat(self, question, MAX_ROUND=15):
        self.messages, self.nbcells, self.cell_cache = tool_chat_loop_2nb(
            question, model_name=self.model_name, 
            available_functions=available_functions, 
            codeexec_tools=codeexec_tools, MAX_ROUND=MAX_ROUND, 
            chat_history=self.messages, nbcells=self.nbcells)
        return self.messages
    
    def save_nb(self, filename='notebook_with_plot_all.ipynb', save_pdf=False, save_html=False):
        nb = save_cells_to_nb(self.nbcells, filename)
        if save_pdf:
            convert_notebook_to_pdf(nb, filename.replace('.ipynb', '.pdf'))
        if save_html:
            convert_notebook_to_html(nb, filename.replace('.ipynb', '.html'))
        return filename
    
    def dump_messages(self, filename='messages.json'):
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, indent=4)
        
    