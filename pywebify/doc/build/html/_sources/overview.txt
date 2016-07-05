Report Structure
================

General Report Structure
--------------------------
A PyWebify report typically consists of three key sections:

  1) a navigation menu bar or *navbar* that can be used to provide report titles and links to 
     relevant imformation (experiment details, previous reports, DOE split tables, etc.)
  2) a *sidebar* that consists of searchable links to image or html files
  3) a *viewer* section that displays the images or html files when hovering on the *sidebar* links

A sample report is shown below:

.. figure:: /_images/report.png
  :align: center  

Report Contents
-----------------
PyWebify reports can consist of content aggregated in two distinct ways:

  1) from a entire discrete directory tree
  2) from a custom list of files and/or folders

PyWebify supports viewing of any image files (jpg, png, tiff, etc.) or html files within the 
*viewer* section.  The ability to include html files allows the user to include some dynamic content
like interactive html tables or bokeh plots.  The specific types of files to be included in the 
*sidebar* directory can be directly controlled by the user.

Customization
---------------
PyWebify is template based so the options of how to present the data and how to 
style the report are unbounded.  Many options (color, spacing, etc.) can be
specfied by adjusting CSS parameters in the `config file <config.html>`_.

Features
------------
Coming soon...