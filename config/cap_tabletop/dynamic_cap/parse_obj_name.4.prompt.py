objects = ['brown bowl', 'banana', 'brown block', 'apple', 'blue bowl', 'blue block']
# the largest fruit.
fruit_names = ['banana', 'apple']
fruit_bbox = [get_bbox(name) for name in fruit_names]
fruit_sizes = [get_box_area(bbox) for bbox in fruit_bbox]
ret_val = fruit_names[np.argmax(fruit_sizes)]
