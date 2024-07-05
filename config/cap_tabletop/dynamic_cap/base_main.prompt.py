# Python 2D robot control script
import numpy as np
from env_utils import get_obj_pos, detect_obj, get_obj_names
from plan_utils import parse_position, parse_obj_name
from ctrl_utils import put_first_on_second, stack_objects_in_order, point_gripper_to

{EXAMPLES}