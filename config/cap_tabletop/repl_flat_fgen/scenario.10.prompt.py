>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move the brown bowl to the closest side'}
>>> side_positions_normalized = [[0.0, 0.5], [1.0, 0.5], [0.5, 0.0], [0.5, 1.0]]
>>> side_positions_real = [denormalize_xy(side) for side in side_positions_normalized]
>>> get_closest_idx(points=side_positions_real, point=get_obj_pos('brown bowl'))
0
>>> put_first_on_second('brown bowl', side_positions_real[0])
'success'

