>>> wait_for_trigger()
{'type': 'dialog', 'text': 'point gripper to the corner closest to the yellow block'}
>>> corner_positions_normalized = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
>>> corner_positions_real = [denormalize_xy(corner) for corner in corner_positions_normalized]
>>> get_closest_idx(points=corner_positions_real, point=get_obj_pos('yellow block'))
1
>>> point_gripper_to(corner_positions_real[1])
'success'