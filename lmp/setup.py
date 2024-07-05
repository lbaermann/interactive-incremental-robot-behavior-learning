from pathlib import Path
from typing import Dict

import langchain.chat_models
import langchain.llms
import yaml
from langchain.chat_models.base import BaseChatModel
from langchain.schema.language_model import BaseLanguageModel

import lmp.repl.error_handlers
from .code_execution import CodeExecutionEnvironment
from .function_gen_lmp import FunctionGenerationLMP
from .lmp import LMP, LMPBase
from .namespace import DynamicNamespaceDict
from .repl.code_execution import ReplExecutionEnvironment
from .repl.dynamic_prompt import DynamicPromptBuilder
from .repl.learn_from_interaction import ChatLearnFromInteractionModule, SaveUnmodifiedHistoryLearnFromInteractionModule
from .repl.repl_lmp import ReplLMP


def load_config(cfg_file: Path) -> Dict:
    loaded_cfgs = {}

    def _load(f: Path):
        cfg = yaml.safe_load(f.read_text())
        _load_prompts(cfg, f)
        loaded_cfgs[str(f.resolve())] = cfg
        imported_cfgs = {}
        for sub_name, sub_f in cfg.pop('import_lmps', {}).items():
            sub_f = (f.parent / f'{sub_f}.yaml').resolve()
            cache_key = str(sub_f.resolve())
            if cache_key in loaded_cfgs:
                sub_cfg = loaded_cfgs[cache_key]
            else:
                sub_cfg = _load(sub_f)
            imported_cfgs[sub_name] = sub_cfg
        cfg['import_lmps'] = imported_cfgs
        return cfg

    return _load(cfg_file)


def _load_prompts(cfg, base_f):
    def _resolve_rel_path(name, extension=''):
        return (base_f.parent / f'{name}{extension}').resolve()

    def _load_prompt_file(name):
        prompt_file = _resolve_rel_path(name, '.prompt.py')
        return prompt_file.read_text().strip()

    if 'prompt_cfg' in cfg:
        prompt_cfg = cfg['prompt_cfg']
        prompts = []
        new_prompt_cfg = {
            'base_prompt': _load_prompt_file(prompt_cfg.pop('base')),
            'prompt_db': prompts
        }
        if 'loop_prevention' in prompt_cfg:
            new_prompt_cfg['loop_prevention_prompt'] = _load_prompt_file(prompt_cfg.pop('loop_prevention'))
        if 'suffix' in prompt_cfg:
            new_prompt_cfg['prompt_suffix'] = _load_prompt_file(prompt_cfg.pop('suffix'))
        if 'custom_prompt_db_file' in prompt_cfg:
            new_prompt_cfg['custom_prompt_db_file'] = _resolve_rel_path(prompt_cfg.pop('custom_prompt_db_file'))
        for include_path in prompt_cfg.pop('db'):
            if '*' in include_path:
                for prompt_f in base_f.parent.glob(f'{include_path}.prompt.py'):
                    prompts.append(prompt_f.resolve().read_text().strip())
            else:
                prompts.append(_load_prompt_file(include_path))
        new_prompt_cfg.update(prompt_cfg)
        cfg['prompt_cfg'] = new_prompt_cfg
    elif cfg.get('type') != 'helper':
        cfg['prompt_text'] = _load_prompt_file(base_f.stem)

    if 'learn_from_interaction_cfg' in cfg and 'few_shot_file' in cfg['learn_from_interaction_cfg']:
        cfg['learn_from_interaction_cfg']['few_shot_file'] = _resolve_rel_path(
            cfg['learn_from_interaction_cfg']['few_shot_file'])


def setup_lmp(cfg: Dict, namespace: DynamicNamespaceDict) -> LMPBase:
    cfg = dict(cfg)  # Copy to keep "pop"s locally, since loaded dict might be shared on multi-way imports
    lmp_type = cfg.pop('type', 'lmp')
    llm = _instantiate_llm(cfg.pop('llm', {}))

    imports = cfg.pop('import_lmps', {})
    imported_lmps = {
        name: setup_lmp(sub_cfg, namespace)
        for name, sub_cfg in imports.items()
    }

    namespace.permanent_definitions.update({
        k: imported_lmps[k]
        for k in imported_lmps.keys() - {'fgen'}
    })
    if lmp_type == 'repl':
        exec_env = ReplExecutionEnvironment(namespace)

        if 'result_function' in cfg:
            exec_env.set_result_function_name(cfg.pop('result_function'))

        prompt_builder = DynamicPromptBuilder(**cfg.pop('prompt_cfg'))
        if 'learn_from_interaction_cfg' in cfg:
            learn_from_interaction = _instantiate_learn_from_interaction(cfg.pop('learn_from_interaction_cfg'))
        else:
            learn_from_interaction = None
        error_handlers = [
            _instantiate_from_cfg(handler_cfg, lmp.repl.error_handlers)
            for handler_cfg in cfg.pop('error_handlers', lmp.repl.error_handlers.default_error_handler_config())
        ]
        if 'fgen' in imported_lmps:
            cfg['fgen_lmp'] = imported_lmps['fgen']

        return ReplLMP(
            llm,
            exec_env,
            prompt_builder,
            error_handlers,
            learn_from_interaction,
            **cfg
        )
    else:
        exec_env = CodeExecutionEnvironment(namespace)
        if lmp_type == 'fgen':
            return FunctionGenerationLMP(cfg, llm, exec_env)
        elif lmp_type == 'helper':
            from helper_llm.helper_lmp import HelperLMP
            return HelperLMP(
                llm, exec_env, top_k=cfg.pop('top_k', 3)
            )
        elif lmp_type == 'dynamic_cap_lmp':
            from lmp.dynamic_cap_lmp import DynamicCapLMP
            return DynamicCapLMP(
                cfg, imported_lmps['fgen'], llm, exec_env
            )
        else:
            return LMP(cfg, imported_lmps['fgen'], llm, exec_env)


def _instantiate_learn_from_interaction(learn_cfg: Dict):
    t = learn_cfg.get('type', 'cot')
    if t == 'cot':
        llm = _instantiate_llm(learn_cfg.get('llm', {}))
        assert isinstance(llm, BaseChatModel), 'ChatLearnFromInteractionModule only supports Chat LLM'
        return ChatLearnFromInteractionModule(
            llm,
            Path(learn_cfg['few_shot_file']))
    elif t == 'no-improve':
        return SaveUnmodifiedHistoryLearnFromInteractionModule()


def _instantiate_llm(llm_cfg: Dict) -> BaseLanguageModel:
    llm_cfg.setdefault('type', 'ChatOpenAI')
    if 'OpenAI' in llm_cfg['type']:
        import openai
        llm_cfg['openai_api_key'] = openai.api_key
        llm_cfg.setdefault('request_timeout', 30)

    return _instantiate_from_cfg(llm_cfg, langchain.llms, langchain.chat_models)


def _instantiate_from_cfg(cfg: Dict, *base_pkgs):
    t = cfg.pop('type')
    cls = None
    for pkg in base_pkgs:
        if hasattr(pkg, t):
            cls = getattr(pkg, t)
            break
    if cls is None:
        raise ValueError(f'Type {t} not found in {base_pkgs}')
    return cls(**cfg)
