objects = ['blue block', 'cyan block', 'purple bowl', 'gray bowl', 'brown bowl', 'pink block', 'purple block']
# the block closest to the purple bowl.
block_names = ['blue block', 'cyan block', 'purple block']
block_positions = get_obj_positions_np(block_names)
closest_block_idx = get_closest_idx(points=block_positions, point=get_obj_pos('purple bowl'))
closest_block_name = block_names[closest_block_idx]
ret_val = closest_block_name