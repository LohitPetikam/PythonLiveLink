# PythonLiveLink
Live link between two Python instances. Designed for convenient interop between Maya/Blender/UE4 Python and system Python instances.

For research we usually want to run specialised computational code on data created in 3D tools.
However, it's hard or impractical to install modules like Numpy/SciPy/Tensorflow in python intepreters embedded into 3D tools.	 
PythonLiveLink lets the user interactively send the data created in these tools to the server for processing, and have the results retrieved to update the digital content.

# Interactive Usage Example (Maya)
1. Run ```python .\PythonLiveLink.py``` in a terminal. This terminal acts as the persistent server that can run system Python commands and scripts.
2. Run Maya and run the following code in the code editor:

```python
import sys
sys.path.append("C:\\dev\\PythonLiveLink")
import PythonLiveLink as pll # import the same "PythonLiveLink.py" file which also has the client code

# create a LiveLink object that connects to the server at port 6000
ll = pll.LiveLink(6000)

# run a few commands on the server
ll.execute('a=1')
ll.execute('b=0.5')
ll.execute('print(a+b)')

# send some data to the server
ll.store_data('x', [1,2,3,4])
ll.execute('x.append(23)') # modify the data on the server
result = ll.evaluate('x') # retrieve the new data from the server

# run code that can't run natively on Maya
ll.execute('import numpy as np')
some_matrix = [[1,2],[3,4]]
ll.store_data('matrix_A', some_matrix) # send data to server
ll.execute('inv_A = np.linalg.inv(np.array(matrix_A))') # server computes matrix inverse
inv_A = ll.evaluate('inv_A.tolist()') # retrieve the result (as native python list)

ll.close_server()
```
