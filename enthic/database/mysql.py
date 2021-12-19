"""
==========================
Flask MySQL initialisation
==========================

PROGRAM BY PAPIT SASU, 2019

Coding Rules:

- Snake case for variables.
- Only argument is configuration file.
- No output or print, just log and files.
"""
from flask import current_app as application
from flask_mysqldb import MySQL

try:
    mysql = MySQL(application)
except RuntimeError:
    pass  # RUNTIME ERROR: WORKING OUTSIDE OF APPLICATION CONTEXT. LIKE EXECUTING SPHINX
