# %%
import sys
sys.path.append('../')
import os
from os.path import join
import pandas as pd
import pickle as pkl
import openai_multi_tool_use_parallel_patch
from auto_analytics.tool_chat_loop import tool_chat_loop,tool_chat_loop_2, shell, tool_chat_loop_2nb, tool_chat_loop_2nb_with_vision
from auto_analytics.supervisor_loop import supervisor_chat_loop_2nb, system_message_library
from auto_analytics.utils.format_utils import message_thread_render
from auto_analytics.utils.nbformat_utils import save_cells_to_nb
from nbformat.v4 import new_notebook, new_code_cell, new_output, new_markdown_cell
from auto_analytics.utils.nbformat_utils import create_code_cell_from_captured, save_cells_to_nb
from auto_analytics.utils.nbformat_utils import convert_notebook_to_html, convert_notebook_to_pdf


class TabularAnalysisPipeline:
    def __init__(self, analysis_name, dataset_path, report_root="", ):
        self.report_dir = report_root
        self.dataset_path = dataset_path
        self.result_dir = None
        self.analysis_name = analysis_name
        self.nbcells = []
        self.messages = []
        self.cache = []
        self.result_dir = join(self.report_dir, analysis_name)
        os.makedirs(self.result_dir, exist_ok=True)
        print(f"Result of analysis [{analysis_name}] will be saved to {self.result_dir}")
        assert os.path.exists(dataset_path), f"Dataset path {dataset_path} does not exist! check the path."
        # self.setup_directories(analysis_name)
        # TODO: check and clear the ipython kernel

    def setup_directories(self, name):
        self.result_dir = join(self.report_dir, name)
        os.makedirs(self.result_dir, exist_ok=True)

    def set_dataset_description(self, table_descriptions, column_descriptions):
        self.table_descriptions = table_descriptions
        self.column_descriptions = column_descriptions

    def supervisor_set_analysis_task(self, task_objective, 
            model_name="gpt-4-turbo-preview", MAX_ROUND=1):
        self.task_objective = task_objective
        self.messages, self.nbcells, _ = supervisor_chat_loop_2nb(
            f"Here is a dataset, that can be loaded from {self.dataset_path}."\
            f"the dataset description {self.table_descriptions}. "\
            f"and the column description {self.column_descriptions}.\n"\
            f"Our objective is to {self.task_objective}",
            model_name=model_name, MAX_ROUND=MAX_ROUND, 
            nbcells=self.nbcells)

        content = self.messages[-1].content
        with open(join(self.result_dir, "analysis_questions.md"), "w") as file:
            file.write(content)

    def perform_data_analysis(self, query=None, MAX_ROUND=15, model_name='gpt-3.5-turbo-1106', 
                              enable_vision=True, vision_token_count=1024):
        
        if query is None:
            print("No query is provided, using the default query from the supervisor.")
            with open(join(self.result_dir, "analysis_questions.md"), "r") as file:
                supervisor_objective = file.read()
            query = f"""Here is a dataset, that can be loaded from {self.dataset_path}.
            The dataset description {self.table_descriptions}. 
            And the column description {self.column_descriptions}.\n
            Our overall objective is to {self.task_objective}, \n
            The specific questions are listed as follows, 
            {supervisor_objective}"""
        else:
            query = query
        
        self.messages, self.nbcells, cache = tool_chat_loop_2nb_with_vision(query, 
            enable_vision=enable_vision, vision_token_count=vision_token_count,
            MAX_ROUND=MAX_ROUND, model_name=model_name,
            nbcells=self.nbcells, chat_history=self.messages)
        self.cache += cache
        pkl.dump((self.messages, self.nbcells, self.cache), 
                 open(join(self.result_dir, "datasci_messages.pkl"), "wb"))

    def perform_data_analysis_human_in_loop(self, query=None, 
            MAX_ROUND=15, model_name='gpt-3.5-turbo-1106', 
            enable_vision=True, vision_token_count=1024):
        
        if query is None:
            print("No query is provided, using the default query from the supervisor.")
            with open(join(self.result_dir, "analysis_questions.md"), "r") as file:
                supervisor_objective = file.read()
            query = f"""Here is a dataset, that can be loaded from {self.dataset_path}.
            The dataset description {self.table_descriptions}. 
            And the column description {self.column_descriptions}.\n
            Our overall objective is to {self.task_objective}, \n
            The specific questions are listed as follows, 
            {supervisor_objective}"""
        else:
            query = query
            
        while True:
            self.messages, self.nbcells, cache = tool_chat_loop_2nb_with_vision(query, 
                enable_vision=enable_vision, vision_token_count=vision_token_count,
                MAX_ROUND=MAX_ROUND, model_name=model_name,
                nbcells=self.nbcells, chat_history=self.messages)
            self.cache += cache
            pkl.dump((self.messages, self.nbcells, self.cache), 
                    open(join(self.result_dir, "datasci_messages.pkl"), "wb"))
            
            next_query = input("Human input: (QUIT to break loop)")
            if next_query.strip().lower() == "quit":
                break
            else:
                query = next_query
    
    def save_results(self, savename=None):
        if savename is None:
            savename = self.analysis_name
        save_cells_to_nb(self.nbcells, join(self.result_dir, f"{savename}_report.ipynb"), 
                         save_html=True, save_pdf=True)


if __name__ == "__main__":
    report_dir = "/Users/binxuwang/Github/GPT-Auto-Data-Analytics/reports"
    csvpath = "/Users/binxuwang/Github/GPT-Auto-Data-Analytics/table_data/Diabetes_Blood_Classification.csv"
    table_descriptions = """
    This dataset contains clinical data from a number of patients that have been analyzed to examine cardiovascular health and kidney function. This data is important for evaluating the risk of heart disease and diabetes, as well as the impaired kidney function often associated with these conditions.

    This dataset was created to support research and development of risk prediction models for heart disease, diabetes and impaired kidney function. With relevant features and clear diagnosis labels, this dataset can be used to build and test accurate prediction models."""
    column_descriptions = """
    About this file

    * Age: Represents the age of the patient in years. Age can be a risk factor for diabetes, as the risk of diabetes increases with age.

    * Gender: Indicates the gender of the patient, which can be a factor in the prediction of diabetes. Some studies suggest that women may have a different risk than men in developing diabetes.

    * Body Mass Index (BMI): BMI is a measure that uses a person's height and weight to determine whether they are in the normal weight, overweight, or obese category. A high BMI is associated with a higher risk of diabetes.

    * Chol: total cholesterol level in the blood. Cholesterol is a fat found in the blood and can come from foods consumed and also be produced by the body. High cholesterol can be a risk factor for heart disease and diabetes.

    * TG (Triglycerides): Represents the level of triglycerides in the blood. Triglycerides are a type of fat found in the blood, and high levels can also increase the risk of heart disease and diabetes.

    * HDL (High-Density Lipoprotein): Is the "good" cholesterol that helps transport excess cholesterol from body tissues back to the liver for further processing or excretion. High levels of HDL are usually considered good for heart health.

    * LDL (Low-Density Lipoprotein): Is the "bad" cholesterol that can cause plaque buildup in the arteries, increasing the risk of heart disease and stroke. High LDL levels can be a risk factor for diabetes.

    * Cr (Creatinine): A waste product of muscle metabolism that is excreted from the body through the kidneys. Creatinine levels in the blood can provide information about kidney function. Kidney disease may be linked to the risk of diabetes.

    * BUN (Blood Urea Nitrogen): Is a measure used to evaluate kidney and liver function. High levels of BUN may indicate kidney or liver disorders that can be related to diabetes.

    * Diagonisis: An indicator that someone has diabetes.
    """
    task_objective = """Perform explorative data analysis of this dataset, 
    This analyis is poised to uncover relationships among different variables, 
    and to find predictive model of diabetes and attribute their importance for prediction.

    First, pose potential questions that could be answered by analyzing this dataset
    Organize these question by the type of analysis that would be required to answer them.
    These questions will be send to data scientist to write code to answer. 
    """
    #%%
    # Example usage
    analysis_session = TabularAnalysisPipeline("Diabetes_Classification", csvpath, report_root=report_dir)
    # Set up dataset and column descriptions
    analysis_session.set_dataset_description(table_descriptions, column_descriptions)
    # Setup and document analysis task
    analysis_session.supervisor_set_analysis_task(task_objective)
    # Perform data analysis
    analysis_session.perform_data_analysis(query=None, MAX_ROUND=2)
    # Save results to notebook, HTML, and PDF
    analysis_session.save_results()
    