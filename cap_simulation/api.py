from typing import Tuple

import numpy as np
import shapely

from cap_simulation.environment import COLORS
from lmp.namespace import comment
from lmp.repl.code_execution import ReplExecutionEnvironment


class SimulationAPI:

    def __init__(self, env, cfg, render=False):
        self._env = env
        self._cfg = cfg
        self._object_names = list(self._cfg['init_objs'])

        self._min_xy = np.array(self._cfg['coords']['bottom_left'])
        self._max_xy = np.array(self._cfg['coords']['top_right'])
        self._range_xy = self._max_xy - self._min_xy

        self._table_z = self._cfg['coords']['table_z']
        self._render = render

    def wait_for_trigger(self):
        raise StopIteration((ReplExecutionEnvironment.RETURN_FN_SIGNAL, None))

    def is_obj_visible(self, obj_name):
        return obj_name in self._object_names

    def get_obj_names(self):
        return self._object_names[::]

    def denormalize_xy(self, pos_normalized):
        return pos_normalized * self._range_xy + self._min_xy

    @comment('2D xy position')
    def get_obj_pos(self, obj_name) -> np.ndarray:
        # return the xy position of the object in robot base frame
        return self._env.get_obj_pos(obj_name)[:2]

    def get_bbox(self, obj_name):
        # return the axis-aligned object bounding box in robot base frame (not in pixels)
        # the format is (min_x, min_y, max_x, max_y)
        bbox = self._env.get_bounding_box(obj_name)
        return bbox

    @comment('RGBA floats')
    def get_color(self, obj_name) -> Tuple[float, float, float, float]:
        for color, rgb in COLORS.items():
            if color in obj_name:
                return rgb

    @comment('move gripper to object 1, pick it up, move to target, release the gripper')
    def put_first_on_second(self, obj_name_1: str, target_name_or_xy_pos: str | np.ndarray):
        # put the object with obj_name on top of target
        # target can either be another object name, or it can be an x-y position in robot base frame
        pick_pos = self.get_obj_pos(obj_name_1) if isinstance(obj_name_1,
                                                              str) else obj_name_1
        if isinstance(target_name_or_xy_pos, str):
            place_pos = self.get_obj_pos(target_name_or_xy_pos)
        elif isinstance(target_name_or_xy_pos, list) and all(type(x) in (float, int) for x in target_name_or_xy_pos):
            place_pos = np.array(target_name_or_xy_pos)
        elif isinstance(target_name_or_xy_pos, shapely.Point):
            place_pos = np.array([target_name_or_xy_pos.x, target_name_or_xy_pos.y])
        else:
            place_pos = target_name_or_xy_pos
        self._env.step(action={'pick': pick_pos, 'place': place_pos})
        return 'success'

    def _get_robot_pos(self):
        # return robot end-effector xy position in robot base frame
        return self._env.get_ee_pos()

    def _goto_pos(self, position_xy):
        # move the robot end-effector to the desired xy position while maintaining same z
        ee_xyz = self._env.get_ee_pos()
        position_xyz = np.concatenate([position_xy, ee_xyz[-1]])
        while np.linalg.norm(position_xyz - ee_xyz) > 0.01:
            self._env.movep(position_xyz)
            self._env.step_sim_and_render()
            ee_xyz = self._env.get_ee_pos()

    def _follow_traj(self, traj):
        for pos in traj:
            self._goto_pos(pos)

    def _get_corner_positions(self):
        normalized_corners = np.array([
            [0, 1],
            [1, 1],
            [0, 0],
            [1, 0]
        ])
        return np.array(([self.denormalize_xy(corner) for corner in normalized_corners]))

    def _get_side_positions(self):
        normalized_sides = np.array([
            [0.5, 1],
            [1, 0.5],
            [0.5, 0],
            [0, 0.5]
        ])
        return np.array(([self.denormalize_xy(side) for side in normalized_sides]))

    def get_corner_name(self, pos):
        corner_positions = self._get_corner_positions()
        corner_idx = np.argmin(np.linalg.norm(corner_positions - pos, axis=1))
        return ['top left corner', 'top right corner', 'bottom left corner', 'botom right corner'][corner_idx]

    def get_side_name(self, pos):
        side_positions = self._get_side_positions()
        side_idx = np.argmin(np.linalg.norm(side_positions - pos, axis=1))
        return ['top side', 'right side', 'bottom side', 'left side'][side_idx]
