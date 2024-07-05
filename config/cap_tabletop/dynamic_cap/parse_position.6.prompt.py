# the side closest to the brown bowl.
bowl_name = parse_obj_name('brown bowl', f'objects = {get_obj_names()}')
side_positions = get_side_positions()
closest_side_idx = get_closest_idx(points=side_positions, point=get_obj_pos(bowl_name))
closest_side_pos = side_positions[closest_side_idx]
ret_val = closest_side_pos
