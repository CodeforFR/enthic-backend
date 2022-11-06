from flask_mysqldb import MySQL

mysql = None


def initialize_mysql(application):
    global mysql
    try:
        mysql = MySQL(application)
    except RuntimeError:
        pass  # RUNTIME ERROR: WORKING OUTSIDE OF APPLICATION CONTEXT. LIKE EXECUTING SPHINX
