>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move the block closest to the purple bowl to the cyan bowl.'}
>>> get_obj_names()
['blue block', 'cyan block', 'purple bowl', 'gray bowl', 'brown bowl', 'pink block', 'purple block']
>>> block_names = [name for name in get_obj_names() if 'block' in name]
>>> block_positions = [get_obj_pos(name) for name in block_names]
>>> get_closest_idx(points=block_positions, point=get_obj_pos('cyan bowl'))
2
>>> block_names[2]
'pink block'
>>> put_first_on_second('pink block', 'cyan bowl')
'success'