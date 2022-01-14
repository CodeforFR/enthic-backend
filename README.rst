**French societies accountability extraction and treatment**
============================================================

This projects download from open source the financial results of french companies.
It proposes financial and social indicators to evaluate companies social impact.
Indicators are available through a web API, documented in swagger.

https://enthic-dataviz.netlify.app


**Install application**
------------------------

Install base dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~

Install system wide softwares.

.. code-block:: bash

  apt-get install libxml2-utils mysql-server libmariadbclient-dev
  mysql_secure_installation

Create and activate virtual environment python3 (only once).

.. code-block:: bash

  make create_environment


Fill the configuration file ``python/enthic/configuration.json`` with correct user/password for Mysql and INPI.
Change ip for host to "0.0.0.0" for production server


Create MySQL database.

.. code-block:: bash

  bash sh/database_creation.sh

For development
~~~~~~~~~~~~~~~

Install libraries.

.. code-block:: bash

  make dev_requirements

Download the data.

.. code-block:: bash

   python -m enthic.scraping.download_from_INPI

Run the API.

.. code-block:: bash

  python -m enthic.app

Test the project.

.. code-block:: bash
  pytest

For production
~~~~~~~~~~~~~~

Install required librairies.

.. code-block:: bash

  . venv/bin/activate
  pip install -r requirements/prod.txt


Install server configuration.

.. code-block:: bash

  sudo bash sh/install-server.sh

Generate documentation
----------------------

Generate HTML documentation via Sphinx documentation framework. Sphinx is called
programmatically at the beginning of setup.py. Therefore the above installation
build the doc at the same time.


License
-------

`Do What The Fuck You Want To Public License (WTFPL) <http://www.wtfpl.net/about/>`_

Donation
--------

You can donate to support Python and Open Source development.

**BTC** ``32JSkGXcBK2dirP6U4vCx9YHHjV5iSYb1G``

**ETH** ``0xF556505d13aC9a820116d43c29dc61417d3aB2F8``
