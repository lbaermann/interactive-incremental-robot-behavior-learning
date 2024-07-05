>>> wait_for_trigger()
{'type': 'dialog', 'text': 'point gripper to k points in a diagonal line, where k is the number of bowls'}
>>> get_obj_names()
['orange bowl', 'red block',  'purple block', 'orange block', 'purple bowl', 'red bowl']
>>> bowl_names = [name for name in get_obj_names() if 'bowl' in name]
>>> start_pos = denormalize_xy([0.1, 0.1])
>>> end_pos = denormalize_xy([0.9, 0.9])
>>> points = interpolate_pts_on_line(start=start_pos, end=end_pos, n=len(bowl_names))
>>> for point in points:
...     point_gripper_to(point)
