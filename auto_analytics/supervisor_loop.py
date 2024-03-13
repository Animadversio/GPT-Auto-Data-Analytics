
import os
import sys
import textwrap
from openai import OpenAI
import IPython
from IPython.core.interactiveshell import InteractiveShell
from auto_analytics.utils.json_utils import parse_partial_json
from auto_analytics.utils.ipython_utils import richoutput_to_image
from auto_analytics.utils.format_utils import wrap_breakline
from nbformat.v4 import new_notebook, new_code_cell, new_output, new_markdown_cell
from auto_analytics.utils.nbformat_utils import create_code_cell_from_captured, save_cells_to_nb
from auto_analytics.utils.nbformat_utils import convert_notebook_to_html, convert_notebook_to_pdf

client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)
system_message_library = {
    "Data Analysis Question Generator":
        """As a Data Analysis Research Manager, your primary role is to bridge the gap between raw datasets and the insights they can provide. 
This requires a deep understanding of both the content of datasets and the various analytical tools available to process them. Upon receiving a new dataset and reading their descriptions, you are expected to:

1. Research Questions Generation: Based on the dataset overview, formulate a set of research questions that can be explored through data analysis. 
These questions should be clear, focused, and aligned with potential research outcomes.

2. Categorization of Questions: Group the generated research questions by the type of analytical tools required to address them. Categories may include:

    * Statistical Analysis (for questions related to trends, averages, variances)
    * Machine Learning (for predictive modeling, clustering, classification)
    * Data Visualization (for questions best answered through charts, graphs, heat maps)
    * Natural Language Processing (for datasets involving textual data)
    * Time Series Analysis (for datasets with a temporal component)

3. Data Preparation Guidelines: Provide guidelines for preparing the dataset for analysis. This includes data cleaning steps, handling missing data, data transformation, and feature engineering techniques relevant to the questions posed and the analytical methods chosen.
""",


    "Data Analysis Research Manager": 
        """As a Data Analysis Research Manager, your primary role is to bridge the gap between raw datasets and the insights they can provide. This requires a deep understanding of both the content of datasets and the various analytical tools available to process them. Upon receiving a new dataset, you are expected to:

1. Dataset Overview: Provide a comprehensive description of the dataset, including its source, size, structure (e.g., columns, types of data), and any peculiarities (e.g., missing values, anomalies).

2. Research Questions Generation: Based on the dataset overview, formulate a set of research questions that can be explored through data analysis. These questions should be clear, focused, and aligned with potential business or research outcomes.

3. Categorization of Questions: Group the generated research questions by the type of analytical tools required to address them. Categories may include:

    *  Statistical Analysis (for questions related to trends, averages, variances)
    * Machine Learning (for predictive modeling, clustering, classification)
    * Data Visualization (for questions best answered through charts, graphs, heat maps)
    * Natural Language Processing (for datasets involving textual data)
    * Time Series Analysis (for datasets with a temporal component)

4. Analysis Plan: For each category of questions, outline a preliminary analysis plan. This plan should include the selection of specific tools or software (e.g., Python libraries like Pandas for data manipulation, scikit-learn for machine learning), methodologies to be employed, and any initial hypotheses or expected outcomes.

5. Data Preparation Guidelines: Provide guidelines for preparing the dataset for analysis. This includes data cleaning steps, handling missing data, data transformation, and feature engineering techniques relevant to the questions posed and the analytical methods chosen.

6. Collaboration and Reporting: Describe how you plan to collaborate with other team members (e.g., data scientists, domain experts) in the analysis process and report your findings. Include any specific formats or templates for reporting results, insights, and recommendations.
"""
}

 

system_message = system_message_library["Data Analysis Question Generator"]

def supervisor_chat_loop_2nb(question, model_name='gpt-3.5-turbo-1106', 
                   MAX_ROUND=1, chat_history=None, nbcells=None,
                   system_message=system_message, ):
    # available_functions=available_functions, 
    # codeexec_tools=codeexec_tools, 
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
            messages.append({'role': 'user', 'content': question})
            # decide if the final message is asking for human input, 
            # then append the question as result to that. 
            # if dict(messages[-1])["role"] == "assistant" and \
            #     chat_history[-1].tool_calls and \
            #     (chat_history[-1].tool_calls[-1].function.name == "seek_human_input"):
            #     print("[put the question as human input]")
            #     messages.append({
            #         "role": "tool",
            #         "tool_call_id": chat_history[-1].tool_calls[-1].id,
            #         "name": "seek_human_input",
            #         "content": question
            #     })
            # else:
            #     messages.append({'role': 'user', 'content': question})
    # add the user input as markdown cell
    nbcells.append(new_markdown_cell(source="**User**:\n"+question))
    # this flag allows us to break out of the loop when human input is needed.
    LOOP_END = False 
    for iteration in range(MAX_ROUND):
        response = client.chat.completions.create(
            model = model_name, 
            messages = messages,
            # tools = codeexec_tools,
            # tool_choice = 'auto',  # auto is default, but we'll be explicit
        )
        response_message = response.choices[0].message
        # extract token count
        # token_count = response_message.token_count
        messages.append(response_message)  # extend conversation with assistant's reply
        if response_message.content:
            print(wrap_breakline(response_message.content, width=80))
            nbcells.append(new_markdown_cell(source="**Assistant**:\n"+response_message.content))
        # else:
        #     print("[No tool use. Finishing conversation.]")
        #     break
    return messages, nbcells, cell_cache