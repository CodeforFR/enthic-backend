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
apt-get install libxml2-utils mariadb-server libmariadbclient-dev make python3-pip virtualenv
```

Create and activate virtual environment python 3.9.4.
The package uses [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv).
```
make create_environment
make dev_requirements
```

In production run the following instead :
```
make create_environment
make prod_requirements
```

**Run an instance**
-------------------

***Fill configuration file***
-----------------------------
Fill the configuration file ``python/enthic/configuration.json`` with correct user/password for Mysql and INPI.
Change ip for host to "0.0.0.0" for production server


***Create MySQL database and fill it***
---------------------------------------
Create database, tables and indexes. Then begins to download data from INPI's FTP and loads it into MySQL database.

.. code-block:: bash
   sh ./database-creation.sh <your mysql password>

   python -m enthic.scraping.download_from_INPI

***Run API***
-------------

A flask REST API can distribute data over the web. Following Swagger standard.

.. code-block:: bash

   $ python -m enthic.app

***Run pipeline***
------------------
The pipeline allows to download batch data from the database and generate analysis features.
First add `DATADIR=data` in the .env file.

.. code-block::bash

  python -m enthic.scoring.pipeline

This will save a parquet file 'enthic_features.parquet' in your DATADIR directory.


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
