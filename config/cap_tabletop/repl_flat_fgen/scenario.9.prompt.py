>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move the left most block to the green bowl'}
>>> block_names = [name for name in get_obj_names() if 'block' in name]
>>> block_positions = np.array([get_obj_pos(name) for name in block_names])
>>> np.argsort(block_positions[:, 0])[0]
3
>>> block_names[3]
'yellow block'
>>> put_first_on_second('yellow block', 'green bowl')
'success'

