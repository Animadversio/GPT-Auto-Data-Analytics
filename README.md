# GPT-Auto-Data-Analytics
Automatize local data analysis with groups of tool-using GPT agents

A data analysis project is usually motivated by a high level question and then break it down into 

## Work-in-Progress
* [x] Terminate the loop properly and avoid repeated run of loop. 
* [x] **Dataset** Demo dataset of for data analysis from Kaggle. Mar. 3
* [x] **ipynb report export** @Mar 10
    * [x] Export a ipynb type output from recorded analysis chat history!  @Mar 10
    * [x] support multi media outputs (table, image) in the captured output and export! @Mar 10
    * [x] Export a ipynb type output from the system, record. Build up the ipynb in the process `tool_chat_loop_2nb`. 
    * [x] Support PDF and HTML formulated export of ipynb. 
* [ ] **Presentation** Nicer way to summarize results, code and figures into a nice looking report for human to read, instead of reading through the debugging history. 
* [ ] **Folder structure** Design file structure for storing analysis results. 
    * [x] *reports* directory
    * [ ] export figure directory? 
    * [ ] code script and notebook?
* [ ] Multi agent tool chat, one assigning tasks and objectives the other one execute it. 
* [ ] Add memory slot, let it remember the objective by reading it back.  
* [ ] Multi-file complex system analysis project. 