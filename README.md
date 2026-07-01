 *his project has been created as part of the 42 curriculum by cehenrot*

 # Description

  This project enables natural language queries to be converted into structured function calls. By utilising constrained decoding, it ensures the generation of a JSON format that is strictly valid and meets the required specifications.

## Input files
The project relies on two configuration files:
* function_calling_test.json : Contains the user prompt (the natural language query) used to test the model (Small_LLM_Model).

* functions_definitions.json: Contains a list of available functions, including their names, descriptions, and the types of their arguments and return values.

## output file
Once the project has run, it generates a file called function_calling_results.json. This file contains

 * The initial request (the test prompt).
 * The name of the function best suited to fulfil the request.
 * The arguments, correctly extracted and typed.

 # Instructions

 