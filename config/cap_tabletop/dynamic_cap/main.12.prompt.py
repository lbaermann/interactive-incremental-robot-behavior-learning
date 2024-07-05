objects = ['brown bowl', 'green block', 'brown block', 'blue bowl', 'blue block', 'green bowl']
# place the blue block in the empty bowl.
empty_bowl_name = parse_obj_name('the empty bowl', f'objects = {get_obj_names()}')
put_first_on_second('blue block', empty_bowl_name)
