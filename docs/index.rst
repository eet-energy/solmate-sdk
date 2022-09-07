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

For all examples please install solmate_sdk pypi package with:

.. code-block:: bash

   pip install solmate_sdk

Sol2Log
-------

Log SolMate live values every 10 seconds on your terminal:

.. code-block:: python

   from time import sleep
   import solmate_sdk

   client = solmate_sdk.SolMateAPIClient("test1")
   client.quickstart()
   while True:
      print(f"Solmate {client.serialnum}: {client.get_live_values()}")
      sleep(10)

Sol2Csv
-------

Log SolMate live values every 10 seconds in CSV format on your terminal:


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
      sleep(10)


Sol2CsvFile
-----------

Write SolMate live values every 10 seconds in CSV format into a CSV file:

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
      sleep(10)


Sol2MQTT
--------

Please install solmate_sdk and paho-mqtt pypi packages with:

.. code-block:: bash

   pip install solmate_sdk paho-mqtt

Publish SolMate PV Power every 10 seconds on the mqtt broker mqtt.eclipseprojects.io:1883 on the topic eet/solmate/test1/pv_power

.. code-block:: python

   import solmate_sdk
   import paho.mqtt.client as mqtt
   from time import sleep
   import json

   client = solmate_sdk.SolMateAPIClient("test1")
   client.quickstart()

   mqttClient = mqtt.Client()
   mqttClient.connect("mqtt.eclipseprojects.io", 1883, 60)
   while True:
      print(".", end="", flush=True)
      try:
         live_values = client.get_live_values()
         online = client.check_online()
         for property_name in live_values.keys():
               if property_name == 'pv_power':
                  mqttClient.publish(f"eet/solmate/{client.serialnum}/{property_name}", live_values[property_name], 1)
      except Exception as exc:
         print(exc)
      sleep(10)


.. include:: hello.py
    :lexer: 'python'
    :encoding: 'utf-8'
    :tab-width: 4

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
