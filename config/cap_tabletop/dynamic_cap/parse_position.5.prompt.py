# the corner closest to the sun colored block.
block_name = parse_obj_name('the sun colored block', f'objects = {get_obj_names()}')
corner_positions = get_corner_positions()
closest_corner_idx = get_closest_idx(points=corner_positions, point=get_obj_pos(block_name))
closest_corner_pos = corner_positions[closest_corner_idx]
ret_val = closest_corner_pos
