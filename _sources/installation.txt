Installing trytond-prestashop module
====================================

The steps below below describe the process of installing the module on
a tryton instance.

.. _install-dependency:

Installation of dependencies
----------------------------

This module depends on a python module called
`pystashop <https://github.com/openlabs/pystashop>`_.
Pystashop is installed automatically while installing trytond-prestashop.
It can also installed separately by running:

  .. code-block:: sh

    pip install pystashop

.. _install-module-source:

Installation from source code
-----------------------------

1. The module source is available online and can be downloaded from
   `here <https://github.com/openlabs/trytond-prestashop>`_.

2. The module can be downloaded as a `zip` or can be `cloned` by running

   .. code-block:: sh 

        git clone https://github.com/openlabs/trytond-prestashop.git

3. If the module is downloaded as a zip, extract the module which will
   give a directory.

4. From the module directory, use the setup.py script with the command:

   .. code-block:: sh

        python setup.py install

5. The command above makes the module available for use by tryton server
   instance in a database.

6. The module can be installed in a tryton database by following to menu:

   | ``Administration > Modules > Modules``

7. This should show the modules list screen as below:

    .. image:: images/modules.png
        :width: 900
    

8. Install the module as shown below:

   | ``Step 1``

    .. image:: images/install.png
        :width: 900

   | ``Step 2``

    .. image:: images/perform.png
       :width: 900

   | ``Step 3``

    .. image:: images/popup.png
       :width: 900


.. _install-module-pypi:

Installation from PYPI
----------------------

1. The module can simply be installed by running the command:

   .. code-block:: sh

        pip install trytond-prestashop

2. The above command will install the latest available and released
   version of the module. To install the module for a specific version of
   tryton, run the following commands:

   .. code-block:: sh

        pip install "trytond-prestashop==`<version>`"

        pip install "trytond-prestashop>=`<lower version>`,<`<higher version>`"
   

:ref:`configure-prestashop-account`
