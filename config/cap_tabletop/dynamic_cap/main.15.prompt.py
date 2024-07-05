objects = ['yellow bowl', 'red block', 'yellow block', 'red bowl', 'green plate', 'orange plate']
# move objects from the green plate to the red bowl.
object_names = parse_obj_name('objects from the green plate', f'objects = {get_obj_names()}')
for object_name in object_names:
    put_first_on_second(object_name, 'red bowl')
