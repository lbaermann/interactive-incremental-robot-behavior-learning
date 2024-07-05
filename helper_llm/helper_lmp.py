# Based on https://github.com/Gabesarch/HELPER

import sys
import traceback
from pathlib import Path
from typing import List

import numpy as np
from langchain.embeddings import CacheBackedEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema.language_model import BaseLanguageModel
from langchain.storage import LocalFileStore

from lmp.code_execution import CodeExecutionEnvironment
from lmp.lmp import LMPBase
from lmp.repl.semantic_hint_errror import SemanticHintError
from .prompt_db import HelperPromptDB


class HelperLMP(LMPBase):
    def __init__(self,
                 llm: BaseLanguageModel,
                 code_execution_env: CodeExecutionEnvironment,
                 embedding_model: Embeddings = None,
                 prompt_db: HelperPromptDB = None,
                 top_k=3
                 ) -> None:
        super().__init__(llm, code_execution_env)
        if embedding_model is None:
            embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.embedding_model: Embeddings = CacheBackedEmbeddings.from_bytes_store(
            embedding_model,
            LocalFileStore(Path(__file__).parent / "cache"),
            namespace=embedding_model.__class__.__name__ + '-' + getattr(embedding_model, 'model', '')
        )
        self.top_k = top_k
        self.exec_hist = ''
        self.prompt_db = prompt_db if prompt_db else HelperPromptDB()
        self.last_executed_cmd_and_plan = None

    @property
    def embeddings(self) -> np.ndarray:
        ex_keys = [ex.split('\n')[0].split('dialogue: ')[-1]
                   for ex in self.prompt_db.all_examples]
        return np.asarray(self.embedding_model.embed_documents(ex_keys))

    @property
    def error_embeddings(self) -> np.ndarray:
        ex_keys = [ex.split('\nInput dialogue:')[0]
                   for ex in self.prompt_db.examples_errors]
        return np.asarray(self.embedding_model.embed_documents(ex_keys))

    def __call__(self, command: str, max_errors=3):
        command = '<Commander> ' + command
        api_str = self.code_execution_env.namespace.build_import_statement(
            use_defs=True,
            exclude=['wait_for_trigger', 'learn_from_interaction']
        )
        prompt = self.prompt_db.prompt_plan
        prompt = prompt.replace('{API}', api_str)
        prompt = prompt.replace('{RETRIEVED_EXAMPLES}', self._retrieve_examples(command))
        prompt = prompt.replace('{command}', f'{command}')
        print('Prompting:\n', prompt)
        plan = self.llm.predict(prompt)

        error = True
        i = 0
        while error and i < max_errors:
            i += 1
            try:
                print('Executing plan:\n', plan)
                self.exec_hist += plan + '\n'
                self.code_execution_env(plan)
                error = False
            except (NameError, TypeError, ImportError, IndexError, KeyError, SemanticHintError) as e:
                failure_line = traceback.format_exc()
                print(failure_line, file=sys.stderr)
                failure_line = (
                    failure_line
                    [failure_line.find('python/llm_planner/lmp/code_execution.py", line 96, in _exec_safe') + 65:]
                )
                failure_line = (
                    failure_line
                    [failure_line.find('File "<string>", line ') + 22:]
                )
                failure_line = failure_line[:failure_line.find(',')]
                failure_line = plan.splitlines()[int(failure_line) - 1]
                prompt = self.prompt_db.prompt_replan
                prompt = prompt.replace('{API}', api_str)
                prompt = prompt.replace('Failed subgoal: ...', f'Failed subgoal:\n{failure_line}')
                prompt = prompt.replace('Execution error: ...', f'Execution error: {e}')
                prompt = prompt.replace('Input dialogue: ...', f'Input dialogue: {command}')
                prompt = prompt.replace('{retrieved_plans}', self._retrieve_example_errors(failure_line, str(e)))
                print('Failure Prompting:\n', prompt)
                plan = self.llm.predict(prompt)
                if 'Plan:\n' in plan:
                    parts = plan.split('Plan:\n')
                    print('Failure Reasoning:', parts[0])
                    plan = parts[-1]  # take everything after reflection
                elif 'Plan (Python script):\n' in plan:
                    parts = plan.split('Plan (Python script):\n')
                    print('Failure Reasoning:', parts[0])
                    plan = parts[-1]  # take everything after reflection
                plan = plan.strip("'''").strip()

        if error:
            self.last_executed_cmd_and_plan = None
        else:
            self.last_executed_cmd_and_plan = (command, plan)

    def reinforce_last_plan_successful(self):
        assert self.last_executed_cmd_and_plan is not None
        cmd, plan = self.last_executed_cmd_and_plan
        print(f'Storing last plan as new example ({cmd})')
        self.prompt_db.store_new_example(
            f'dialogue: {cmd}\n'
            f'Python script:\n'
            f'{plan}'
        )

    def _retrieve_examples(self, command):
        return self._retrieve_examples_from(
            command, self.prompt_db.all_examples, self.embeddings,
            base_prompt="Here are a few examples of typical inputs and outputs (only for in-context reference):\n",
            separator='\n'
        )

    def _retrieve_example_errors(self, failure_line, error):
        examples_input_prompt = f'Failed subgoal:\n{failure_line}\nExecution error: {error}'
        return self._retrieve_examples_from(
            examples_input_prompt, self.prompt_db.examples_errors, self.error_embeddings,
            base_prompt="Here are a few examples of typical inputs and outputs:\n",
            separator='"""\n'
        )

    def _retrieve_examples_from(self, command, example_set: List[str], embeddings: np.ndarray,
                                base_prompt: str, separator: str):
        embedding = self.embedding_model.embed_query(command)
        embedding = np.asarray(embedding)
        # nearest neighbor
        distance = np.linalg.norm(embeddings - embedding[None, :], axis=1)
        distance_argsort_topk = np.argsort(distance)[:self.top_k]
        example_text = base_prompt
        example_number = 1
        for idx in list(distance_argsort_topk):
            example_text += f'Example #{example_number}:\n' + separator
            example_text += example_set[idx]
            example_text += '\n' + separator
            example_number += 1
        print(f"most relevant examples are: {list(distance_argsort_topk)}")
        return example_text
