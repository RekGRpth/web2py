#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file is part of the web2py Web Framework
Copyrighted by Massimo Di Pierro <mdipierro@cs.depaul.edu>
License: LGPLv3 (http://www.gnu.org/licenses/lgpl.html)


Web2Py framework modules
========================
"""

__version__ = "3.0.3"

__all__ = [
    "__version__",
    "A",
    "B",
    "BEAUTIFY",
    "BODY",
    "BR",
    "CAT",
    "CENTER",
    "CLEANUP",
    "CODE",
    "CRYPT",
    "DAL",
    "DIV",
    "EM",
    "EMBED",
    "FIELDSET",
    "FORM",
    "Field",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "HEAD",
    "HR",
    "HTML",
    "HTTP",
    "I",
    "IFRAME",
    "IMG",
    "INPUT",
    "IS_ALPHANUMERIC",
    "IS_DATE",
    "IS_DATETIME",
    "IS_DATETIME_IN_RANGE",
    "IS_DATE_IN_RANGE",
    "IS_DECIMAL_IN_RANGE",
    "IS_EMAIL",
    "IS_LIST_OF_EMAILS",
    "IS_EMPTY_OR",
    "IS_EQUAL_TO",
    "IS_EXPR",
    "IS_FILE",
    "IS_FLOAT_IN_RANGE",
    "IS_IMAGE",
    "IS_JSON",
    "IS_INT_IN_RANGE",
    "IS_IN_DB",
    "IS_IN_SET",
    "IS_IPV4",
    "IS_LENGTH",
    "IS_LIST_OF",
    "IS_LOWER",
    "IS_MATCH",
    "IS_NOT_EMPTY",
    "IS_NOT_IN_DB",
    "IS_NULL_OR",
    "IS_SLUG",
    "IS_STRONG",
    "IS_TIME",
    "IS_UPLOAD_FILENAME",
    "IS_UPPER",
    "IS_URL",
    "LABEL",
    "LEGEND",
    "LI",
    "LINK",
    "LOAD",
    "MARKMIN",
    "MENU",
    "META",
    "OBJECT",
    "OL",
    "ON",
    "OPTGROUP",
    "OPTION",
    "P",
    "PRE",
    "SCRIPT",
    "SELECT",
    "SPAN",
    "SQLFORM",
    "SQLTABLE",
    "STRONG",
    "STYLE",
    "TABLE",
    "TAG",
    "TBODY",
    "TD",
    "TEXTAREA",
    "TFOOT",
    "TH",
    "THEAD",
    "TITLE",
    "TR",
    "TT",
    "UL",
    "URL",
    "XHTML",
    "XML",
    "redirect",
    "current",
    "embed64",
    "wsgibase",
]

#: add pydal to sys.modules
import builtins
import os
import sys

MESSAGE = (
    "web2py depends on %s, which apparently you have not installed.\n"
    + "Probably you cloned the repository using git without '--recursive'"
    + "\nTo fix this, please run (from inside your web2py folder):\n\n"
    + "     git submodule update --init --recursive\n\n"
    + "You can also download a complete copy from http://www.web2py.com."
)

def import_packages():
    for package in ["pydal", "yatl", "rocket3"]:
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base, "packages", package)
            if path not in sys.path:
                sys.path.insert(0, path)
            sys.modules[package] = builtins.__import__(package)
        except ImportError:
            raise RuntimeError(MESSAGE % package)


import_packages()

from .compileapp import LOAD
from .dal import DAL, Field
from .globals import current
from .html import *
from .http import HTTP, redirect
from .sqlhtml import SQLFORM, SQLTABLE
from .validators import *
from .main import wsgibase

# Dummy code to enable code completion in IDE's.
if 0:
    from .cache import Cache
    from .globals import Request, Response, Session
    from .languages import translator
    from .tools import Auth, Crud, Mail, PluginManager, Service

    # API objects
    request = Request()
    response = Response()
    session = Session()
    cache = Cache(request)
    T = translator(request)

    # Objects commonly defined in application model files
    # (names are conventions only -- not part of API)
    db = DAL()
    auth = Auth(db)
    crud = Crud(db)
    mail = Mail()
    service = Service()
    plugins = PluginManager()
