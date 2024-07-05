>>> wait_for_trigger()
{'type': 'dialog', 'text': 'move the blue block in between the cyan block and purple bowl'}
>>> pts = [get_obj_pos('cyan block'), get_obj_pos('purple bowl')]
>>> target_pos = np.average(pts, axis=0)
>>> put_first_on_second('blue block', target_pos)
'success'