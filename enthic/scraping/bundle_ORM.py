"""
========================================
========================================

Coding Rules:

- Snake case for variables.
- Only argument is configuration file.
- No output or print, just log and files.
"""

import os
import shutil
import subprocess
import sys
import urllib
from argparse import ArgumentParser
from ftplib import FTP_TLS
from glob import glob
from io import BytesIO
from json import load
from logging import error, info
from os.path import abspath, basename, dirname, getsize, join, pardir

import wget
from py7zr import SevenZipFile
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Bundle(Base):

    __tablename__ = "bundle"

    siren = Column(type_=Integer, nullable=False, primary_key=True)
    declaration = Column(type_=Integer, nullable=False, primary_key=True)
    accountability = Column(type_=Integer, nullable=False, primary_key=True)
    bundle = Column(type_=Integer, nullable=False, primary_key=True)
    amount = Column(type_=Float, nullable=False)
