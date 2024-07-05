import json
from functools import cached_property
from pathlib import Path

from langchain.schema.language_model import BaseLanguageModel
from sentence_transformers import SentenceTransformer, util

from .code_execution import CodeExecutionEnvironment
from .lmp import LMP


class DynamicCapLMP(LMP):

    def __init__(self,
                 cfg,
                 lmp_fgen,
                 llm: BaseLanguageModel,
                 code_execution_env: CodeExecutionEnvironment):
        prompt_cfg = cfg['prompt_cfg']  # Following lmp.repl.dynamic_prompt
        cfg['prompt_text'] = prompt_cfg['base_prompt']  # For compatibility with LMP base class
        super().__init__(cfg, lmp_fgen, llm, code_execution_env)
        custom_prompt_db_file = prompt_cfg['custom_prompt_db_file']
        self.top_k = prompt_cfg['top_k']
        self.predefined_prompt_db = prompt_cfg['prompt_db']
        self.custom_prompt_db_file = Path(custom_prompt_db_file) if custom_prompt_db_file else None
        self.custom_prompt_db = (json.loads(self.custom_prompt_db_file.read_text())
                                 if custom_prompt_db_file and self.custom_prompt_db_file.exists() else [])
        if self.custom_prompt_db:
            print('Loaded', len(self.custom_prompt_db), 'samples from', self.custom_prompt_db_file)
        self.sim_model = SentenceTransformer(prompt_cfg['sentence_similarity_model'])
        self._context_prefix_length = prompt_cfg.get('context_prefix_length', 1)  # in lines

    @property
    def _all_prompts(self):
        return self.predefined_prompt_db + self.custom_prompt_db

    @cached_property
    def _prompt_embeddings_cache(self):
        commands = []
        for example in self._all_prompts:
            cmd_line = example.splitlines()[self._context_prefix_length]
            assert cmd_line.startswith('#'), cmd_line
            commands.append(cmd_line[1:])
        return self.sim_model.encode(commands, convert_to_tensor=True)

    def build_prompt(self, query, context=''):
        base_prompt, use_query = super().build_prompt(query, context)

        encoded_query = self.sim_model.encode([query], convert_to_tensor=True)
        similarities = util.cos_sim(encoded_query, self._prompt_embeddings_cache).squeeze()
        top_indices = similarities.argsort(descending=True)[:self.top_k]
        example_str = '\n'.join(self._all_prompts[i] for i in top_indices)

        return base_prompt.replace('{EXAMPLES}', example_str), use_query

    def reinforce_last_plan_successful(self):
        if not self.exec_hist:
            return

        example = self.exec_hist.strip()
        cmd_line = example.splitlines()[self._context_prefix_length]
        assert cmd_line.startswith('#'), example

        self.custom_prompt_db.append(example)
        if self.custom_prompt_db_file:
            print('Writing custom_prompt_db_file', self.custom_prompt_db_file)
            self.custom_prompt_db_file.write_text(json.dumps(self.custom_prompt_db))

        # invalidate cache
        # noinspection PyPropertyAccess
        del self._prompt_embeddings_cache

        self.exec_hist = ''  # To prevent duplicate writing by LMPs referenced by children on different levels
        for key, value in self.code_execution_env.namespace.permanent_definitions.items():
            if isinstance(value, DynamicCapLMP):
                print('Propagating reinforce_last_plan_successful to child LMP', key)
                value.reinforce_last_plan_successful()
