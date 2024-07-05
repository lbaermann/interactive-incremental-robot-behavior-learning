objects = ['brown bowl', 'green block', 'brown block', 'green bowl', 'blue bowl', 'blue block']
# the object on the green bowl.
for obj_name in objects:
    if obj_name != 'green bowl':
        if np.linalg.norm(get_obj_pos('green bowl') - get_obj_pos(obj_name)) < 0.05:
            ret_val = obj_name
            break
