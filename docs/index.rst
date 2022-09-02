.. solmate-sdk documentation master file, created by
   sphinx-quickstart on Thu Sep  1 16:52:14 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to solmate-sdk's documentation!
=======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


   

Examples
========

Sol2Log
-------

.. code-block:: python

   from time import sleep
   import solmate_sdk

   client = solmate_sdk.SolMateAPIClient("test1")
   client.quickstart()
   while True:
      print(f"Solmate {client.serialnum}: {client.get_live_values()}")
      sleep(5)

Sol2Csv
-------

.. code-block:: python

   from time import sleep
   import solmate_sdk

   SEPERATOR=';'

   client = solmate_sdk.SolMateAPIClient("test1")
   client.quickstart()

   vals = client.get_live_values()
   keys = vals.keys()
   print("serial_number", end=SEPERATOR)
   for k in vals.keys():
      print(k, end=SEPERATOR)
   print()
   while True:
      vals = client.get_live_values()
      print(client.serialnum, end=SEPERATOR)
      for k in keys:
         if k in vals:
               print(vals[k], end=SEPERATOR)
         else:
               print(" ", end=SEPERATOR)
      print()
      sleep(15)

Sol2CsvFile
-----------

.. code-block:: python

   from time import sleep
   import solmate_sdk
   import csv

   client = solmate_sdk.SolMateAPIClient("test1")
   client.quickstart()
   vals = client.get_live_values()
   keys = vals.keys()
   with open(f'{client.serialnum}.csv', 'w') as csvfile:
      writer = csv.DictWriter(csvfile, fieldnames = keys)
      writer.writeheader()
      writer.writerow(vals)
   while True:
      with open(f'{client.serialnum}.csv', 'a') as csvfile:
         writer = csv.DictWriter(csvfile, fieldnames = keys)
         writer.writerow(client.get_live_values())
      sleep(15)

 

.. include:: hello.py
    :lexer: 'python'
    :encoding: 'utf-8'
    :tab-width: 4

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
