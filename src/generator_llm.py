import sys
try:
    from llm_sdk import Small_LLM_Model
    from pydantic import BaseModel
    from models import FunctionCall, PromptTest, FunctionsDefinition
except ImportError:
    sys.exit()


class GeneratorLlm():

    def __init__(self) -> None:
        self.llm_model: Small_LLM_Model = Small_LLM_Model()

    def execute_llm(self, prompt: PromptTest,
                    lst_function: list[FunctionsDefinition]) -> FunctionCall:

    