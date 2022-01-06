from flask import current_app as application
from flask_mysqldb import MySQL

try:
    mysql = MySQL(application)
except RuntimeError:
    pass  # RUNTIME ERROR: WORKING OUTSIDE OF APPLICATION CONTEXT. LIKE EXECUTING SPHINX
