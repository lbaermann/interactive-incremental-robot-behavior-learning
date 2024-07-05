objects = ['brown bowl', 'green block', 'brown block', 'green bowl', 'blue bowl', 'blue block']
# the third bowl from the top.
bowl_names = ['brown bowl', 'green bowl', 'blue bowl']
bowl_positions = get_obj_positions_np(bowl_names)
top_bowl_idx = np.argsort(bowl_positions[:, 1])[-3]
top_bowl_name = bowl_names[top_bowl_idx]
ret_val = top_bowl_name