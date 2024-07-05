>>> wait_for_trigger()
{'type': 'dialog', 'text': 'place the green block in the bowl closest to the middle'}
>>> bowl_names = [name for name in get_obj_names() if 'bowl' in name]
>>> bowl_positions = [get_obj_pos(name) for name in bowl_names]
>>> get_closest_idx(points=bowl_positions, point=denormalize_xy([0.5, 0.5]))
3
>>> bowl_names[3]
'pink bowl'
>>> put_first_on_second('green block', 'pink bowl')
'success'

