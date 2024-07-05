objects = ['red block', 'red bowl', 'blue bowl', 'blue block']
# stack the blocks on the top most bowl.
bowl_name = parse_obj_name('top most bowl', f'objects = {get_obj_names()}')
block_names = parse_obj_name('the blocks', f'objects = {get_obj_names()}')
object_names = [bowl_name] + block_names
stack_objects_in_order(object_names=object_names)
