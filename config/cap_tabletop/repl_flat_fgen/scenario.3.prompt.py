>>> wait_for_trigger()
{'type': 'dialog', 'text': 'put the blocks into bowls with matching colors'}
>>> get_obj_names()
['orange bowl', 'red block', 'purple bowl', 'blue block', 'blue bowl', 'orange block', 'purple block', 'red bowl']
>>> put_first_on_second('orange block', 'orange bowl')
'success'
>>> put_first_on_second('red block', 'red bowl')
'success'
>>> put_first_on_second('purple block', 'purple bowl')
'success'
>>> put_first_on_second('blue block', 'blue bowl')
'success'