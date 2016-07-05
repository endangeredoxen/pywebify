PyWebifying (Making a Report)
=============================

PyWebify reports can be generated based on the contents of a static directory
or on a text-file list of files by envoking the ``PyWebify`` class and suppling
a file path and one or more optional configuration parameters.

**Static directory:**

.. code-block:: python
   
   import pywebify
   pywebify.PyWebify('C:\\Users\\Me\\MyReportFiles', 
                     config='C:\\Users\\Me\\PathToMyConfigFile\config.ini')
   

Default Setup
^^^^^^^^^^^^^
Coming soon