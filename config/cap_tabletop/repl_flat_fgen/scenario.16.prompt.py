>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move the red bowl the left of the blocks'}
>>> block_names = [name for name in get_obj_names() if 'block' in name]
>>> block_positions = np.array([get_obj_pos(name) for name in block_names])
>>> left_obj_pos = block_positions[np.argmin(block_positions[:, 0])] + [-0.1, 0]
>>> put_first_on_second('red bowl', left_obj_pos)
'success'


