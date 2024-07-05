import math
import random
import re
from typing import Tuple, Literal

import numpy as np

from cap_simulation.environment import PickPlaceEnv, CORNER_POS, BOUNDS

_Direction = Literal['top', 'left', 'bottom', 'right']
_Distance = Literal['farthest', 'closest']
_Magnitude = Literal['a little', 'a lot']
_LineDirection = Literal['horizontal', 'vertical', 'diagonal']


def _check_on_top_of(var_name_1, var_name_2):
    return lambda vals, env, tmp: env.on_top_of(vals[var_name_1], vals[var_name_2])


def _check_all_blocks_at(var_name):
    return lambda vals, env, tmp: all(
        env.on_top_of(x, vals[var_name])
        for x in env.object_list if 'block' in x
    )


def _find_block_in_direction(env: PickPlaceEnv,
                             direction: _Direction,
                             relative_to_obj: str):
    base_pos = env.get_obj_pos(relative_to_obj)
    blocks = [x for x in env.object_list if 'block' in x and relative_to_obj != x]
    blocks_per_direction = {
        'top': [b for b in blocks if env.get_obj_pos(b)[1] > base_pos[1]],
        'bottom': [b for b in blocks if env.get_obj_pos(b)[1] < base_pos[1]],
        'left': [b for b in blocks if env.get_obj_pos(b)[0] < base_pos[0]],
        'right': [b for b in blocks if env.get_obj_pos(b)[0] > base_pos[0]],
    }
    candidate_blocks: list = blocks_per_direction[direction]
    candidate_blocks.sort(key=lambda b: np.linalg.norm(env.get_obj_pos(b)[:2] - base_pos[:2]))
    return None if len(candidate_blocks) == 0 else candidate_blocks[0]


def _find_block_by_distance(env: PickPlaceEnv,
                            distance: _Distance,
                            relative_to_obj: str):
    base_pos = env.get_obj_pos(relative_to_obj)
    blocks = [x for x in env.object_list if 'block' in x and relative_to_obj != x]
    blocks.sort(key=lambda b: np.linalg.norm(env.get_obj_pos(b)[:2] - base_pos[:2]))
    return blocks[0 if distance == 'closest' else -1]


def _find_corner_by_distance(base_pos: np.ndarray, distance: _Distance):
    corners = [k + ' corner' for k in ('top left', 'top right', 'bottom left', 'bottom right')]
    corners.sort(key=lambda c: np.linalg.norm(CORNER_POS[c][:2] - base_pos[:2]))
    return corners[0 if distance == 'closest' else -1]


def _check_all_blocks_in_different_corners(env: PickPlaceEnv):
    all_corners = [x for x in CORNER_POS.keys() if 'corner' in x]
    used_corners = []
    for obj in env.object_list:
        if 'block' not in obj:
            continue
        size_before = len(used_corners)
        for corner in all_corners:
            if env.on_top_of(obj, corner):
                if corner in used_corners:
                    return False
                else:
                    used_corners.append(corner)
        if len(used_corners) == size_before:  # Was not in any corner
            return False
    return True


def _check_object_relative_to_object(
        env: PickPlaceEnv,
        reference_obj: str,
        check_obj: str,
        direction: _Direction,
        magnitude: _Magnitude
):
    ref_pos = env.get_obj_pos(reference_obj)
    check_pos = env.get_obj_pos(check_obj)
    if (
            direction == 'top' and check_pos[1] < ref_pos[1]
            or direction == 'bottom' and check_pos[1] > ref_pos[1]
            or direction == 'right' and check_pos[0] < ref_pos[0]
            or direction == 'left' and check_pos[0] > ref_pos[0]
    ):
        return False
    relevant_idx = 0 if direction in ['left', 'right'] else 1
    relevant_distance = abs(ref_pos[relevant_idx] - check_pos[relevant_idx])
    relevant_range = BOUNDS[relevant_idx, 1] - BOUNDS[relevant_idx, 0]
    if magnitude == 'a little':
        return relevant_distance <= relevant_range / 3
    elif magnitude == 'a lot':
        return relevant_distance > relevant_range / 3
    else:
        raise AssertionError(magnitude)


def _check_all_blocks_in_line(env: PickPlaceEnv, line_direction: _LineDirection):
    blocks = [x for x in env.object_list if 'block' in x]
    assert len(blocks) >= 2
    block_pos = [env.get_obj_pos(b) for b in blocks]
    # y1 = a x1 + b
    # y2 = a x2 + b
    # =>  a = (y2 - y1)/ (x2 - x1), b = y1 - a x1
    # noinspection PyTupleAssignmentBalance
    x1, y1, x2, y2 = *block_pos[0][:2], *block_pos[1][:2]
    a = (y2 - y1) / (x2 - x1)
    b = y1 - a * x1
    tolerance = np.average((BOUNDS[0:2, 1] - BOUNDS[0:2, 0]) * 0.05)
    for p in block_pos[2:]:
        # calc orthogonal distance to line. simple algebra: closest point F(f_x, f_y) has the following coordinates:
        f_x = (p[0] + a * (p[1] - b)) / (1 + a * a)
        f_y = a * f_x + b
        distance = math.sqrt((f_x - p[0]) ** 2 + (f_y - p[1]) ** 2)
        if distance > tolerance:
            return False
    if line_direction == 'horizontal':
        return abs(a) < 0.3
    elif line_direction == 'diagonal':
        return 0.7 < abs(a) < 1.3
    elif line_direction == 'vertical':
        return abs(a) > 10
    else:
        raise AssertionError(line_direction)


def _check_tmp_block_at_position(vals, env, tmp):
    return env.on_top_of(tmp['block'], vals['corner/side'])


def _always_feasible(vals, env):
    return True


def _no_tmp_vars(vals, env):
    return None


def _require_none(vals, selected_random_objs):
    return []


def _require_selected_vals(vals, selected_random_objs):
    return list(v for v in vals.values() if any(x in v for x in ('block', 'bowl')))


# Tuples of (instruction: str,
#            check_fn_initial_state_extractor: (vals, env) -> initial_state_tmp,
#            check_fn: (vals, env, initial_state_tmp) -> success,
#            required_objects_fn: (vals, selected_random_objs) -> required_objs,
#            is_env_feasible: (vals, env) -> bool
#            )
instructions_seen = [
    (
        'pick up the <block:1> and place it on the <block:2>',
        _no_tmp_vars,
        _check_on_top_of('block:1', 'block:2'),
        _require_selected_vals,
        _always_feasible
    ),
    (
        'pick up the <block> and place it on the <bowl>',
        _no_tmp_vars,
        _check_on_top_of('block', 'bowl'),
        _require_selected_vals,
        _always_feasible
    ),
    (
        'put all the blocks on the <corner/side>',
        _no_tmp_vars,
        _check_all_blocks_at('corner/side'),
        _require_none,
        _always_feasible
    ),
    (
        'put the blocks in the <bowl>',
        _no_tmp_vars,
        _check_all_blocks_at('bowl'),
        _require_selected_vals,
        _always_feasible
    ),
    (
        'put all the blocks in the bowls with matching colors',
        _no_tmp_vars,
        lambda vals, env, tmp: all(
            env.on_top_of(x, x.split()[0] + ' bowl') if x.split()[0] + ' bowl' in env.object_list else True
            for x in env.object_list if 'block' in x
        ),
        lambda vals, selected_random_objs: [f'{b.split()[0]} bowl' for b in selected_random_objs if 'block' in b],
        _always_feasible
    ),
    (
        'pick up the block to the <direction> of the <bowl> and place it on the <corner/side>',
        lambda vals, env: {'block': _find_block_in_direction(env, vals['direction'], vals['bowl'])},
        _check_tmp_block_at_position,
        _require_selected_vals,
        lambda vals, env: _find_block_in_direction(env, vals['direction'], vals['bowl']) is not None
    ),
    (
        'pick up the block <distance> to the <bowl> and place it on the <corner/side>',
        lambda vals, env: {'block': _find_block_by_distance(env, vals['distance'], vals['bowl'])},
        _check_tmp_block_at_position,
        _require_selected_vals,
        _always_feasible
    ),
    (
        'pick up the <nth> block from the <direction> and place it on the <corner/side>',
        lambda vals, env: {'block': sorted(
            (x for x in env.object_list if 'block' in x),
            key=lambda b: env.get_obj_pos(b)[0 if vals['direction'] in ['left', 'right'] else 1],
            reverse=vals['direction'] in ['right', 'top']
        )[['first', 'second', 'third', 'fourth'].index(vals['nth'])]},
        _check_tmp_block_at_position,
        _require_none,
        lambda vals, env: (len([x for x in env.object_list if 'block' in x])
                           > ['first', 'second', 'third', 'fourth'].index(vals['nth']))
    ),
]

instructions_unseen = [
    (
        'put all the blocks in different corners',
        _no_tmp_vars,
        lambda vals, env, tmp: _check_all_blocks_in_different_corners(env),
        _require_none,
        _always_feasible
    ),
    (
        'put the blocks in the bowls with mismatched colors',
        _no_tmp_vars,
        lambda vals, env, tmp: all(
            any(env.on_top_of(x, b) for b in env.object_list if 'bowl' in b and x.split()[0] != b.split()[0])
            for x in env.object_list if 'block' in x
        ),
        _require_none,
        lambda vals, env: all(
            len([bowl for bowl in env.object_list if 'bowl' in bowl and bowl != f'{block.split()[0]} bowl']) > 0
            for block in env.object_list if 'block' in block
        )
    ),
    (
        'stack all the blocks on the <corner/side>',
        _no_tmp_vars,
        lambda vals, env, tmp: all(
            env.on_top_of(x, vals['corner/side'])
            for x in env.object_list if 'block' in x
        ),
        _require_none,
        _always_feasible
    ),
    (
        'pick up the <block> and place it <magnitude> to the <direction> of the <bowl>',
        _no_tmp_vars,
        lambda vals, env, tmp: _check_object_relative_to_object(env,
                                                                vals['bowl'],
                                                                vals['block'],
                                                                vals['direction'],
                                                                vals['magnitude']),
        _require_selected_vals,
        _always_feasible,
    ),
    (
        'pick up the <block> and place it in the corner <distance> to the <bowl>',
        _no_tmp_vars,
        lambda vals, env, tmp: env.on_top_of(
            vals['block'], _find_corner_by_distance(env.get_obj_pos(vals['bowl']), vals['distance'])),
        _require_selected_vals,
        _always_feasible,
    ),
    (
        'put all the blocks in a <line> line',
        _no_tmp_vars,
        lambda vals, env, tmp: _check_all_blocks_in_line(env, vals['line']),
        _require_none,
        lambda vals, env: len([x for x in env.object_list if 'block' in x]) >= 2,
    ),
]

_seen_colors = ['blue', 'red', 'green', 'orange', 'yellow']
_unseen_colors = ['pink', 'cyan', 'brown', 'gray', 'purple']

attributes_seen = {
    'block': [f'{color} block' for color in _seen_colors],
    'bowl': [f'{color} bowl' for color in _seen_colors],
    'corner/side': ['left side', 'top left corner', 'top side', 'top right corner'],
    'direction': ['top', 'left'],
    'distance': ['closest'],
    'magnitude': ['a little'],
    'nth': ['first', 'second'],
    'line': ['horizontal', 'vertical'],
}
attributes_unseen = {
    'block': [f'{color} block' for color in _unseen_colors],
    'bowl': [f'{color} bowl' for color in _unseen_colors],
    'corner/side': ['bottom right corner', 'bottom side', 'bottom left corner'],
    'direction': ['bottom', 'right'],
    'distance': ['farthest'],
    'magnitude': ['a lot'],
    'nth': ['third', 'fourth'],
    'line': ['diagonal'],
}


def fill_template(template, attributes) -> Tuple[str, dict]:
    found_attributes = {}
    for match in re.finditer(r'<([^>:]+)(?::(\d))?>', template):
        attribute_key = match.group(1)
        attribute_idx = int(match.group(2) or '1')
        found_attributes[attribute_key] = max(found_attributes.get(attribute_key, 0), attribute_idx)

    picked_values = {
        k: random.sample(attributes[k], k=num)
        for k, num in found_attributes.items()
    }
    val_assignments = {
        (k + f':{i + 1}' if len(vals) > 1 else k): v
        for k, vals in picked_values.items()
        for i, v in enumerate(vals)
    }
    return re.sub(r'<([^>:]+)(:\d)?>',
                  lambda m: picked_values[m.group(1)].pop(0),
                  template), val_assignments
