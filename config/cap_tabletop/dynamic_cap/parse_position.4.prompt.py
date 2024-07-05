# a point between the cyan block and purple bowl.
block_name = parse_obj_name('cyan block', f'objects = {get_obj_names()}')
bowl_name = parse_obj_name('purple bowl', f'objects = {get_obj_names()}')
pts = [get_obj_pos(block_name), get_obj_pos(bowl_name)]
pos = get_center_np(pts=pts)
ret_val = pos
