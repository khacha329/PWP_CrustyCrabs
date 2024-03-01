"""
This module contains configuration settings to set up the database
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """config class for the application"""

    SECRET_KEY = "dev"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
