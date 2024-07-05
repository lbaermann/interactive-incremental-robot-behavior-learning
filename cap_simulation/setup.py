import copy
import json
import math
import random
import traceback
from functools import partial
from pathlib import Path
from threading import Thread
from typing import Literal, Callable, List, Tuple

import langchain.cache
import langchain.callbacks
import numpy as np
import shapely.affinity
import shapely.geometry

from cap_simulation.api import SimulationAPI
from cap_simulation.environment import PickPlaceEnv, ALL_BOWLS, ALL_BLOCKS, CORNER_POS
from cap_simulation.qt_thread import EasyGuiQt
from experiment import instructions_seen, attributes_seen, fill_template, attributes_unseen, instructions_unseen
from lmp.api_visibility_wrapper import ApiVisibilityWrapper
from lmp.namespace import DynamicNamespaceDict
from lmp.setup import setup_lmp, load_config

gui = EasyGuiQt()


def prepare_namespace_with_common_packages(api):
    namespace = DynamicNamespaceDict(api)
    namespace.predefined_globals['np'] = np
    namespace.predefined_globals.update({
        name: eval('shapely.geometry.' + name)
        for name in shapely.geometry.__all__
    })
    namespace.predefined_globals.update({
        name: eval('shapely.affinity.' + name)
        for name in shapely.affinity.__all__
    })
    return namespace


def _sample_objs_with_constraints(required_objs_fn: Callable[[List[str]], List[str]]):
    num_blocks_range = (1, 4)
    num_bowls_range = (1, 4)
    num_blocks = random.randint(*num_blocks_range)
    num_bowls = random.randint(*num_bowls_range)
    block_list = np.random.choice(ALL_BLOCKS, size=num_blocks, replace=False).tolist()
    bowl_list = np.random.choice(ALL_BOWLS, size=num_bowls, replace=False).tolist()

    must_include_objs = required_objs_fn(block_list + bowl_list)
    must_include_blocks = [x for x in must_include_objs if 'block' in x]
    must_include_bowls = [x for x in must_include_objs if 'bowl' in x]
    num_blocks = max(len(must_include_blocks), num_blocks)
    num_bowls = max(len(must_include_bowls), num_bowls)

    for must, actual, num in [(must_include_blocks, block_list, num_blocks),
                              (must_include_bowls, bowl_list, num_bowls)]:
        for must_item in must:
            if must_item in actual:
                actual.remove(must_item)
            actual.insert(0, must_item)
        while len(actual) > num:
            actual.pop()

    return block_list + bowl_list


def setup_simulation_lmp(cfg, required_objs_fn: Callable[[List[str]], List[str]]):
    cfg = copy.deepcopy(cfg)
    lmp_tabletop_coords = {
        'table_z': 0.0,
        **{
            k.replace(' ', '_').replace('_corner', ''): (x, y)
            for k, (x, y, z) in CORNER_POS.items()
        }
    }

    env = PickPlaceEnv(render=False, high_res=False, high_frame_rate=False)
    obj_list = _sample_objs_with_constraints(required_objs_fn)
    _ = env.reset(obj_list)

    api = SimulationAPI(env, {
        'init_objs': obj_list,
        'coords': lmp_tabletop_coords
    })
    if 'api' in cfg:
        print('Wrapping API visibility with config:', cfg['api'])
        api = ApiVisibilityWrapper(api, **cfg.pop('api', dict(include_all=True)))
    lmp = setup_lmp(cfg, prepare_namespace_with_common_packages(api))
    return lmp, env


def _run_experiment(
        env, lmp, cmd, check_fn, interactive_mode
) -> Tuple[List[Tuple[str, Literal['success', 'failure', 'error', 'timeout']]], str]:
    state_history: List[Literal['success', 'failure', 'error', 'timeout']] = []
    command_history = []
    timeout_budget = 1

    def _apply(command: str):
        env.display_text(command)
        command_history.append(command)
        with langchain.callbacks.get_openai_callback() as cb:
            lmp(command)
            print(cb)
        if timeout_budget < 0:
            return
        s: Literal['success', 'failure']
        if check_fn():
            s = 'success'
        else:
            s = 'failure'
        state_history.append(s)
        print('State after exec:', s)

    def _exec():
        nonlocal timeout_budget
        try:
            _apply(cmd)
            if not interactive_mode:
                return
            while True:  # state_history[-1] != 'success':
                timeout_budget = 100  # Give the user enough time to respond
                command = gui.get_string(f'State: {state_history[-1]}.'
                                         f'Enter a command to continue, or ENTER to quit this experiment.',
                                         title='Continue?')
                # command = input('Q: Quit, Other: Input follow-up command')
                if command is None or command == '' or command.lower() == 'q':
                    break
                timeout_budget = 2  # learn_from_interaction might take a bit longer
                _apply(command)
            if state_history[-1] == 'success' and hasattr(lmp, 'reinforce_last_plan_successful'):
                lmp.reinforce_last_plan_successful()
        except:
            traceback.print_exc()
            # If there was a timeout already, this error is just related to the killed environment
            if len(state_history) == 0 or state_history[-1] != 'timeout':
                state_history.append('error')

    t = Thread(target=_exec, name='run_experiment', daemon=True)
    t.start()
    while t.is_alive() and timeout_budget > 0:
        timeout_budget -= 1
        t.join(timeout=60)
        if timeout_budget == 0 and t.is_alive():
            print('Timeout!')
            if gui.get_yes_no('Cancel experiment due to timeout?', 'Cancel?') in [False, None]:
                timeout_budget += 1
    if t.is_alive():
        timeout_budget = -1
        state_history.append('timeout')
    env.close()

    return list(zip(command_history, state_history)), str(lmp.exec_hist)


def main(
        cfg_path='cap_tabletop/repl_flat_fgen/repl',
        num_runs_per_instruction=10,
        interactive_mode=True
):
    full_cfg_path = Path(__file__).parent.parent / 'config' / f'{cfg_path}.yaml'
    cfg = load_config(full_cfg_path)

    stats = {}
    for instruction, check_fn_initial_state_extractor, check_fn, required_objs_fn, feasibility_fn in instructions_unseen:
        # Seed based on the instruction template, so that runs are deterministic even when
        #  num_runs_per_instruction is increased. hash(instruction) somehow appears to be not reproducible
        seed = math.prod(ord(x) for x in instruction) % (2 ** 32 - 1)
        random.seed(seed)
        np.random.seed(seed)

        stats[instruction] = []
        for i in range(num_runs_per_instruction):
            command, value_assignments = fill_template(instruction, attributes_unseen)
            lmp, env = setup_simulation_lmp(cfg, partial(required_objs_fn, value_assignments))
            while not feasibility_fn(value_assignments, env):
                # Resample
                print(command, value_assignments)
                print('Not feasible, resampling')
                lmp, env = setup_simulation_lmp(cfg, partial(required_objs_fn, value_assignments))

            tmp = check_fn_initial_state_extractor(value_assignments, env)
            cmd_and_state_history, transcript = _run_experiment(
                env, lmp, command,
                check_fn=partial(check_fn, value_assignments, env, tmp),
                interactive_mode=interactive_mode
            )

            print(i, command, '--- result:', cmd_and_state_history)
            stats[instruction].append((cmd_and_state_history, transcript))

        print('\n' * 3, stats[instruction], '\n' * 2, '=' * 30, '\n' * 3)

    print('\n' * 5, '=' * 40, '\n' * 2)
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    langchain.llm_cache = langchain.cache.SQLiteCache(database_path="langchain-cache.db")
    main(
        cfg_path='cap_tabletop/repl_flat_fgen/repl'
    )
