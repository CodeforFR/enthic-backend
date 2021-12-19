**French societies accountability extraction and treatment**
============================================================

Project that treats data from opendata-rncs.inpi.fr. They contain xml
files of the account declaration of all french societies. The overall project
is meant to be low-code and open source. Aim to provide ethical indicators on companies.
Information media is a MySQL database, CSV files, web visualisation and a
swagger API. The search engine endpoint return a JSON-LD (Hydra) compliant JSON.
Company JSON cannot conform to JSON-LD Organization type due to lack of data
(contact for instance).
Score and indicators are calculated by batch, sql and why not using
fancy libraries. Help in data treatment to improve scoring would be appreciated.
Scoring, AI, data scrapping for segmentation.

**Install dependencies and python package**
-------------------------------------------

Install system wide the following requirements :
```
apt-get install pyenv-virtualenv libxml2-utils mysql-server libmariadbclient-dev
mysql_secure_installation
```

Create and activate virtual environment python 3.9.4.
The package uses [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv).
```
make create_environment
make requirements
```

**Run an instance**
-------------------

***Fill configuration file***
-----------------------------
Fill file ``python/enthic/configuration.json`` with correct user/password for Mysql and INPI.
Change ip for host to "0.0.0.0" for production server


***Create MySQL database and fill it***
---------------------------------------
Create database, tables and indexes. Then begins to download data from INPI's FTP and loads it into MySQL database.

.. code-block:: bash

   $ sh ./database-creation.sh <your mysql password>

***Run API***
-------------

A flask REST API can distribute data over the web. Following Swagger standard.

.. code-block:: bash

   $ python -m enthic.app


Testing
-------

`pytest`


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
