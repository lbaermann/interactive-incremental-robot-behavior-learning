objects = ['purple block', 'cyan bowl', 'blue block', 'cyan block', 'purple bowl', 'blue bowl']
# move the block closest to the purple bowl to the cyan bowl.
closest_block_name = parse_obj_name('the block closest to the purple bowl', f'objects = {get_obj_names()}')
put_first_on_second(closest_block_name, 'cyan bowl')
