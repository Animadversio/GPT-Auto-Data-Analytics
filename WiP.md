
## Work-in-Progress
* [x] Terminate the loop properly and avoid repeated run of loop. 
* [x] **Dataset** Demo dataset of for data analysis from Kaggle. Mar. 3
* [x] **ipynb report export** @Mar 10
    * [x] Export a ipynb type output from recorded analysis chat history!  @Mar 10
    * [x] support multi media outputs (table, image) in the captured output and export! @Mar 10
    * [x] Export a ipynb type output from the system, record. Build up the ipynb in the process `tool_chat_loop_2nb`. 
    * [x] Support PDF and HTML formulated export of ipynb. 
* [ ] **Presentation** Nicer way to summarize results, code and figures into a nice looking report for human to read, instead of reading through the debugging history. 
    * [x] Jupyter notebook report 
    * [x] PDF and HTML report 
    * [ ] Post processing and filtering of report. 
    * [ ] **Bug fix**, if the loop in running in a terminal then the captured won't get the figure component! wont go to report!! 
* [ ] **Folder structure** Design file structure for storing analysis results. 
    * [x] *reports* sub-directory
    * [x] notebook
    * [ ] export figure directory? 
    * [ ] cleaned up code 
* [ ] **Multi agent** tool chat, one assigning tasks and objectives the other one execute it. 
    * Code architecture for these multi agent system.
    * **Roles** 
        * [x] **Analysis Supervisor**. Breaking down the overall objective into smaller questions that could be analyzed by code, assign them to data analyst. 
        * [x] **Data analyst**. Taking the objective and tasks into account, using code to solve each one of them. 
        * [x] **Visual analyst**. Draw conclusions from reading the figures and code. @Mar.12th
        * [ ] **Research Manager**. Maintain a list of TODO for the analyst, hand out task one by one, when one analysis is finished check the result and write summary, assign a new one. 
            * [x] Format the objective in a structred list, as json etc.  @Mar.12th
            * [ ] Then we can ask / answer them one by one? How to manage better? 
        * [ ] **Summary writer**. Taking the output of data analyst and polish it into a report. 
* [x] **Vision interface**, current agent cannot see the plot, so the analysis is not quite informative....
    * [x] Demo for vision api drawing conclusions from the figures. @Mar.11. 
    * [x] Integrating vision agent with the main chat loop and integrating visual insight @Mar.12th. 
    * Vision API is significantly slower than others..... 
* [ ] Overall CLI for default data analysis of a data set. Have a default workflow. Supervisor => Data analysis => 
    * [ ] Think about input structure. `csvpath`, `column description`, `dataset description`. `overall objective` 
* [ ] Add memory slot, let it remember the objective by reading it back.  
* [ ] Multi-file complex system analysis project. 
