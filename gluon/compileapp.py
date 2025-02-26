# -*- coding: utf-8 -*-

"""
| This file is part of the web2py Web Framework
| Copyrighted by Massimo Di Pierro <mdipierro@cs.depaul.edu>
| License: LGPLv3 (http://www.gnu.org/licenses/lgpl.html)

Functions required to execute app components
---------------------------------------------

Note:
    FOR INTERNAL USE ONLY
"""

import copy
import fnmatch
import importlib
import marshal
import os
import py_compile
import random
import re
import shutil
import sys
import types
from functools import reduce
from os.path import exists
from os.path import join as pjoin

from pydal.base import BaseAdapter

from gluon import html, rewrite, validators
from gluon.cache import Cache
from gluon.cfs import getcfs
from gluon.dal import DAL, Field
from gluon.fileutils import (abspath, add_path_first, listdir, mktree,
                             read_file, write_file)
from gluon.globals import Response, current
from gluon.http import HTTP, redirect
from gluon.languages import TranslatorFactory
from gluon.restricted import compile2, restricted
from gluon.settings import global_settings
from gluon.sqlhtml import SQLFORM, SQLTABLE
from gluon.storage import List, Storage
from gluon.template import parse_template
from gluon.validators import Validator

MAGIC = importlib.util.MAGIC_NUMBER

CACHED_REGEXES = {}
CACHED_REGEXES_MAX_SIZE = 1000


def re_compile(regex):
    try:
        return CACHED_REGEXES[regex]
    except KeyError:
        if len(CACHED_REGEXES) >= CACHED_REGEXES_MAX_SIZE:
            CACHED_REGEXES.clear()
        compiled_regex = CACHED_REGEXES[regex] = re.compile(regex)
        return compiled_regex


def LOAD(
    c=None,
    f="index",
    args=None,
    vars=None,
    extension=None,
    target=None,
    ajax=False,
    ajax_trap=False,
    url=None,
    user_signature=False,
    timeout=None,
    times=1,
    content="loading...",
    post_vars=Storage(),
    **attr
):
    """LOADs a component into the action's document

    Args:
        c(str): controller
        f(str): function
        args(tuple or list): arguments
        vars(dict): vars
        extension(str): extension
        target(str): id of the target
        ajax(bool): True to enable AJAX behaviour
        ajax_trap(bool): True if `ajax` is set to `True`, traps
            both links and forms "inside" the target
        url(str): overrides `c`, `f`, `args` and `vars`
        user_signature(bool): adds hmac signature to all links
            with a key that is different for every user
        timeout(int): in milliseconds, specifies the time to wait before
            starting the request or the frequency if times is greater than
            1 or "infinity"
        times(integer or str): how many times the component will be requested
            "infinity" or "continuous" are accepted to reload indefinitely the
            component
    """
    if args is None:
        args = []
    vars = Storage(vars or {})
    target = target or "c" + str(random.random())[2:]
    attr["_id"] = target
    request = current.request
    if "." in f:
        f, extension = f.rsplit(".", 1)
    if url or ajax:
        url = url or html.URL(
            request.application,
            c,
            f,
            r=request,
            args=args,
            vars=vars,
            extension=extension,
            user_signature=user_signature,
        )
        # timing options
        if isinstance(times, str):
            if times.upper() in ("INFINITY", "CONTINUOUS"):
                times = "Infinity"
            else:
                # FIXME: should be a ValueError
                raise TypeError("Unsupported times argument %s" % times)
        elif isinstance(times, int):
            if times <= 0:
                raise ValueError(
                    "Times argument must be greater than zero, 'Infinity' or None"
                )
        else:
            # NOTE: why do not use ValueError only?
            raise TypeError("Unsupported times argument type %s" % type(times))
        if timeout is not None:
            if not isinstance(timeout, int):
                raise ValueError("Timeout argument must be an integer or None")
            elif timeout <= 0:
                raise ValueError("Timeout argument must be greater than zero or None")
            statement = "$.web2py.component('%s','%s', %s, %s);" % (
                url,
                target,
                timeout,
                times,
            )
            attr["_data-w2p_timeout"] = timeout
            attr["_data-w2p_times"] = times
        else:
            statement = "$.web2py.component('%s','%s');" % (url, target)
        attr["_data-w2p_remote"] = url
        if target is not None:
            return html.DIV(content, **attr)

    else:
        if not isinstance(args, (list, tuple)):
            args = [args]
        c = c or request.controller
        other_request = Storage(request)
        other_request["env"] = Storage(request.env)
        other_request.controller = c
        other_request.function = f
        other_request.extension = extension or request.extension
        other_request.args = List(args)
        other_request.vars = vars
        other_request.get_vars = vars
        other_request.post_vars = post_vars
        other_response = Response()
        other_request.env.path_info = "/" + "/".join(
            [request.application, c, f] + [str(a) for a in other_request.args]
        )
        other_request.env.query_string = (
            vars and html.URL(vars=vars).split("?")[1] or ""
        )
        other_request.env.http_web2py_component_location = request.env.path_info
        other_request.cid = target
        other_request.env.http_web2py_component_element = target
        other_request.restful = types.MethodType(
            request.restful.__func__, other_request
        )
        # A bit nasty but needed to use LOAD on action decorates with @request.restful()
        other_response.view = "%s/%s.%s" % (c, f, other_request.extension)

        other_environment = copy.copy(current.globalenv)  # FIXME: NASTY

        other_response._view_environment = other_environment
        other_response.generic_patterns = copy.copy(current.response.generic_patterns)
        other_environment["request"] = other_request
        other_environment["response"] = other_response

        ## some magic here because current are thread-locals

        original_request, current.request = current.request, other_request
        original_response, current.response = current.response, other_response
        page = run_controller_in(c, f, other_environment)
        if isinstance(page, dict):
            other_response._vars = page
            other_response._view_environment.update(page)
            page = run_view_in(other_response._view_environment)

        current.request, current.response = original_request, original_response
        js = None
        if ajax_trap:
            link = html.URL(
                request.application,
                c,
                f,
                r=request,
                args=args,
                vars=vars,
                extension=extension,
                user_signature=user_signature,
            )
            js = "$.web2py.trap_form('%s','%s');" % (link, target)
        script = js and html.SCRIPT(js, _type="text/javascript") or ""
        return html.TAG[""](html.DIV(html.XML(page), **attr), script)


class LoadFactory(object):
    """
    Attention: this helper is new and experimental
    """

    def __init__(self, environment):
        self.environment = environment

    def __call__(
        self,
        c=None,
        f="index",
        args=None,
        vars=None,
        extension=None,
        target=None,
        ajax=False,
        ajax_trap=False,
        url=None,
        user_signature=False,
        content="loading...",
        **attr
    ):
        if args is None:
            args = []
        vars = Storage(vars or {})
        target = target or "c" + str(random.random())[2:]
        attr["_id"] = target
        request = current.request
        if "." in f:
            f, extension = f.rsplit(".", 1)
        if url or ajax:
            url = url or html.URL(
                request.application,
                c,
                f,
                r=request,
                args=args,
                vars=vars,
                extension=extension,
                user_signature=user_signature,
            )
            script = html.SCRIPT(
                '$.web2py.component("%s","%s")' % (url, target), _type="text/javascript"
            )
            return html.TAG[""](script, html.DIV(content, **attr))
        else:
            if not isinstance(args, (list, tuple)):
                args = [args]
            c = c or request.controller

            other_request = Storage(request)
            other_request["env"] = Storage(request.env)
            other_request.controller = c
            other_request.function = f
            other_request.extension = extension or request.extension
            other_request.args = List(args)
            other_request.vars = vars
            other_request.get_vars = vars
            other_request.post_vars = Storage()
            other_response = Response()
            other_request.env.path_info = "/" + "/".join(
                [request.application, c, f] + [str(a) for a in other_request.args]
            )
            other_request.env.query_string = (
                vars and html.URL(vars=vars).split("?")[1] or ""
            )
            other_request.env.http_web2py_component_location = request.env.path_info
            other_request.cid = target
            other_request.env.http_web2py_component_element = target
            other_response.view = "%s/%s.%s" % (c, f, other_request.extension)
            other_environment = copy.copy(self.environment)
            other_response._view_environment = other_environment
            other_response.generic_patterns = copy.copy(
                current.response.generic_patterns
            )
            other_environment["request"] = other_request
            other_environment["response"] = other_response

            ## some magic here because current are thread-locals

            original_request, current.request = current.request, other_request
            original_response, current.response = current.response, other_response
            page = run_controller_in(c, f, other_environment)
            if isinstance(page, dict):
                other_response._vars = page
                other_response._view_environment.update(page)
                page = run_view_in(other_response._view_environment)

            current.request, current.response = original_request, original_response
            js = None
            if ajax_trap:
                link = html.URL(
                    request.application,
                    c,
                    f,
                    r=request,
                    args=args,
                    vars=vars,
                    extension=extension,
                    user_signature=user_signature,
                )
                js = "$.web2py.trap_form('%s','%s');" % (link, target)
            script = js and html.SCRIPT(js, _type="text/javascript") or ""
            return html.TAG[""](html.DIV(html.XML(page), **attr), script)


def local_import_aux(name, reload_force=False, app="welcome"):
    """
    In apps, instead of importing a local module
    (in applications/app/modules) with::

       import a.b.c as d

    you should do::

       d = local_import('a.b.c')

    or (to force a reload):

       d = local_import('a.b.c', reload=True)

    This prevents conflict between applications and un-necessary execs.
    It can be used to import any module, including regular Python modules.
    """
    items = name.replace("/", ".")
    name = "applications.%s.modules.%s" % (app, items)
    module = importlib.import_module(name)
    for item in name.split(".")[1:]:
        module = getattr(module, item)
    if reload_force:
        importlib.reload(module)
    return module


#
# OLD IMPLEMENTATION:
#
#   items = name.replace('/','.').split('.')
#   filename, modulepath = items[-1], pjoin(apath,'modules',*items[:-1])
#   imp.acquire_lock()
#   try:
#       file=None
#       (file,path,desc) = imp.find_module(filename,[modulepath]+sys.path)
#       if not path in sys.modules or reload:
#           if is_gae:
#               module={}
#               execfile(path,{},module)
#               module=Storage(module)
#           else:
#               module = imp.load_module(path,file,path,desc)
#           sys.modules[path] = module
#       else:
#           module = sys.modules[path]
#   except Exception, e:
#       module = None
#   if file:
#       file.close()
#   imp.release_lock()
#   if not module:
#       raise ImportError, "cannot find module %s in %s" % (
#           filename, modulepath)
#   return module


_base_environment_ = dict((k, getattr(html, k)) for k in html.__all__)
_base_environment_.update((k, getattr(validators, k)) for k in validators.__all__)
_base_environment_["__builtins__"] = __builtins__
_base_environment_["HTTP"] = HTTP
_base_environment_["redirect"] = redirect
_base_environment_["DAL"] = DAL
_base_environment_["Field"] = Field
_base_environment_["SQLDB"] = DAL  # for backward compatibility
_base_environment_["SQLField"] = Field  # for backward compatibility
_base_environment_["SQLFORM"] = SQLFORM
_base_environment_["SQLTABLE"] = SQLTABLE
_base_environment_["LOAD"] = LOAD


def build_environment(request, response, session, store_current=True):
    """
    Build the environment dictionary into which web2py files are executed.
    """
    # h,v = html,validators
    environment = dict(_base_environment_)

    if not request.env:
        request.env = Storage()
    # Enable standard conditional models (i.e., /*.py, /[controller]/*.py, and
    # /[controller]/[function]/*.py)
    response.models_to_run = [
        r"^\w+\.py$",
        r"^%s/\w+\.py$" % request.controller,
        r"^%s/%s/\w+\.py$" % (request.controller, request.function),
    ]

    T = environment["T"] = TranslatorFactory(
        pjoin(request.folder, "languages"), request.env.http_accept_language
    )
    c = environment["cache"] = Cache(request)

    # configure the validator to use the t translator
    Validator.translator = staticmethod(
        lambda text: None if text is None else str(T(text))
    )

    if store_current:
        current.globalenv = environment
        current.request = request
        current.response = response
        current.session = session
        current.T = T
        current.cache = c

    if global_settings.is_jython:
        # jython hack
        class mybuiltin(object):
            """
            NOTE could simple use a dict and populate it,
            NOTE not sure if this changes things though if monkey patching import.....
            """

            # __builtins__
            def __getitem__(self, key):
                try:
                    return getattr(builtin, key)
                except AttributeError:
                    raise KeyError(key)

            def __setitem__(self, key, value):
                setattr(self, key, value)

        global __builtins__
        __builtins__ = mybuiltin()

    environment["request"] = request
    environment["response"] = response
    environment["session"] = session
    environment["local_import"] = (
        lambda name, reload=False, app=request.application: local_import_aux(
            name, reload, app
        )
    )
    BaseAdapter.set_folder(pjoin(request.folder, "databases"))
    from gluon.custom_import import custom_import_install

    custom_import_install()
    return environment


def save_pyc(filename):
    """
    Bytecode compiles the file `filename`
    """
    cfile = "%sc" % filename
    py_compile.compile(filename, cfile=cfile)


MARSHAL_HEADER_SIZE = 16 if sys.version_info[1] >= 7 else 12


def read_pyc(filename):
    """
    Read the code inside a bytecode compiled file if the MAGIC number is
    compatible

    Returns:
        a code object
    """
    data = read_file(filename, "rb")
    if not global_settings.web2py_runtime_gae and not data.startswith(MAGIC):
        raise SystemError("compiled code is incompatible")
    return marshal.loads(data[MARSHAL_HEADER_SIZE:])


REGEX_PATH_CLASS = r"[\w%s-]" % os.sep if os.sep != "\\" else r"[\w\\-]"
REGEX_VIEW_PATH = r"%s+(?:\.\w+)*$" % REGEX_PATH_CLASS


def compile_views(folder, skip_failed_views=False):
    """
    Compiles all the views in the application specified by `folder`
    """
    path = pjoin(folder, "views")
    failed_views = []
    for fname in listdir(path, REGEX_VIEW_PATH, followlinks=True):
        try:
            data = parse_template(fname, path)
        except Exception as e:
            if skip_failed_views:
                failed_views.append(fname)
            else:
                # FIXME: should raise something more specific than Exception
                raise Exception("%s in %s" % (e, fname))
        else:
            filename = "views.%s.py" % fname.replace(os.sep, ".")
            filename = pjoin(folder, "compiled", filename)
            write_file(filename, data)
            save_pyc(filename)
            os.unlink(filename)
    return failed_views or None


REGEX_MODEL_PATH = r"%s+\.py$" % REGEX_PATH_CLASS


def compile_models(folder):
    """
    Compiles all the models in the application specified by `folder`
    """
    path = pjoin(folder, "models")
    for fname in listdir(path, REGEX_MODEL_PATH, followlinks=True):
        data = read_file(pjoin(path, fname))
        modelfile = "models." + fname.replace(os.sep, ".")
        filename = pjoin(folder, "compiled", modelfile)
        mktree(filename)
        write_file(filename, data)
        save_pyc(filename)
        os.unlink(filename)


REGEX_LONG_STRING = re.compile(r'(""".*?"""|' "'''.*?''')", re.DOTALL)
REGEX_EXPOSED = re.compile(r"^def\s+(_?[a-zA-Z0-9]\w*)\( *\)\s*:", re.MULTILINE)


def find_exposed_functions(data):
    data = REGEX_LONG_STRING.sub("", data)
    return REGEX_EXPOSED.findall(data)


REGEX_CONTROLLER = r"[\w-]+\.py$"


def compile_controllers(folder):
    """
    Compiles all the controllers in the application specified by `folder`
    """
    path = pjoin(folder, "controllers")
    for fname in listdir(path, REGEX_CONTROLLER, followlinks=True):
        data = read_file(pjoin(path, fname))
        exposed = find_exposed_functions(data)
        for function in exposed:
            command = data + "\nresponse._vars=response._caller(%s)\n" % function
            filename = pjoin(
                folder, "compiled", "controllers.%s.%s.py" % (fname[:-3], function)
            )
            write_file(filename, command)
            save_pyc(filename)
            os.unlink(filename)


REGEX_COMPILED_MODEL = r"models[_.][\w.-]+\.pyc$"
REGEX_MODEL = r"[\w-]+\.py$"


def run_models_in(environment):
    """
    Runs all models (in the app specified by the current folder)
    It tries pre-compiled models first before compiling them.
    """
    request = current.request
    folder = request.folder
    c = request.controller
    # f = environment['request'].function
    response = current.response

    path = pjoin(folder, "models")
    cpath = pjoin(folder, "compiled")
    compiled = exists(cpath)
    if compiled:
        models = sorted(
            listdir(cpath, REGEX_COMPILED_MODEL, 0),
            key=lambda f: "{0:03d}".format(f.count(".")) + f,
        )
    else:
        models = sorted(
            listdir(path, REGEX_MODEL, 0, sort=False),
            key=lambda f: "{0:03d}".format(f.count(os.sep)) + f,
        )

    models_to_run = None
    for model in models:
        if response.models_to_run != models_to_run:
            regex = models_to_run = response.models_to_run[:]
            if isinstance(regex, list):
                regex = re_compile("|".join(regex))
        if models_to_run:
            if compiled:
                n = len(cpath) + 8
                fname = model[n:-4].replace(".", "/") + ".py"
            else:
                n = len(path) + 1
                fname = model[n:].replace(os.sep, "/")
            if not regex.search(fname) and c != "appadmin":
                continue
            elif compiled:
                f = lambda: read_pyc(model)
            else:
                f = lambda: compile2(read_file(model), model)
            ccode = getcfs(model, model, f)
            restricted(ccode, environment, layer=model)


TEST_CODE = r"""
def _TEST():
    import doctest, sys, io, types, gluon.fileutils
    if not gluon.fileutils.check_credentials(request):
        raise HTTP(401, web2py_error='invalid credentials')
    stdout = sys.stdout
    html = '<h2>Testing controller "%s.py" ... done.</h2><br/>\n' \
        % request.controller
    for key in sorted([key for key in globals() if not key in __symbols__+['_TEST']]):
        eval_key = eval(key)
        if type(eval_key) == types.FunctionType:
            number_doctests = sum([len(ds.examples) for ds in doctest.DocTestFinder().find(eval_key)])
            if number_doctests>0:
                sys.stdout = io.StringIO()
                name = '%s/controllers/%s.py in %s.__doc__' \
                    % (request.folder, request.controller, key)
                doctest.run_docstring_examples(eval_key,
                    globals(), False, name=name)
                report = sys.stdout.getvalue().strip()
                if report:
                    pf = 'failed'
                else:
                    pf = 'passed'
                html += '<h3 class="%s">Function %s [%s]</h3>\n' \
                    % (pf, key, pf)
                if report:
                    html += CODE(report, language='web2py', \
                        link='/examples/global/vars/').xml()
                html += '<br/>\n'
            else:
                html += \
                    '<h3 class="nodoctests">Function %s [no doctests]</h3><br/>\n' \
                    % (key)
    response._vars = html
    sys.stdout = stdout
_TEST()
"""


def run_controller_in(controller, function, environment):
    """
    Runs the controller.function() (for the app specified by
    the current folder).
    It tries pre-compiled controller.function.pyc first before compiling it.
    """
    # if compiled should run compiled!
    folder = current.request.folder
    cpath = pjoin(folder, "compiled")
    badc = "invalid controller (%s/%s)" % (controller, function)
    badf = "invalid function (%s/%s)" % (controller, function)
    if exists(cpath):
        filename = pjoin(cpath, "controllers.%s.%s.pyc" % (controller, function))
        try:
            ccode = getcfs(filename, filename, lambda: read_pyc(filename))
        except IOError:
            raise HTTP(
                404, rewrite.THREAD_LOCAL.routes.error_message % badf, web2py_error=badf
            )
    elif function == "_TEST":
        # TESTING: adjust the path to include site packages
        paths = (
            global_settings.gluon_parent,
            abspath("site-packages", gluon=True),
            abspath("gluon", gluon=True),
            "",
        )
        [add_path_first(path) for path in paths]
        # TESTING END

        filename = pjoin(folder, "controllers/%s.py" % controller)
        if not exists(filename):
            raise HTTP(
                404, rewrite.THREAD_LOCAL.routes.error_message % badc, web2py_error=badc
            )
        environment["__symbols__"] = list(environment.keys())
        code = read_file(filename)
        code += TEST_CODE
        ccode = compile2(code, filename)
    else:
        filename = pjoin(folder, "controllers/%s.py" % controller)
        try:
            code = getcfs(filename, filename, lambda: read_file(filename))
        except IOError:
            raise HTTP(
                404, rewrite.THREAD_LOCAL.routes.error_message % badc, web2py_error=badc
            )
        exposed = find_exposed_functions(code)
        if function not in exposed:
            raise HTTP(
                404, rewrite.THREAD_LOCAL.routes.error_message % badf, web2py_error=badf
            )
        code = "%s\nresponse._vars=response._caller(%s)" % (code, function)
        layer = "%s:%s" % (filename, function)
        ccode = getcfs(layer, filename, lambda: compile2(code, filename))

    restricted(ccode, environment, layer=filename)
    response = environment["response"]
    vars = response._vars
    if response.postprocessing:
        vars = reduce(lambda vars, p: p(vars), response.postprocessing, vars)
    if hasattr(vars, "xml") and callable(vars.xml):
        vars = vars.xml()
    return vars


def run_view_in(environment):
    """
    Executes the view for the requested action.
    The view is the one specified in `response.view` or determined by the url
    or `view/generic.extension`
    It tries the pre-compiled views.controller.function.pyc before compiling it.
    """
    request = current.request
    response = current.response
    view = environment["response"].view
    folder = request.folder
    cpath = pjoin(folder, "compiled")
    badv = "invalid view (%s)" % view
    patterns = response.get("generic_patterns")
    layer = None
    scode = None
    if patterns:
        regex = re_compile("|".join(fnmatch.translate(p) for p in patterns))
        short_action = "%(controller)s/%(function)s.%(extension)s" % request
        allow_generic = regex.search(short_action)
    else:
        allow_generic = False
    if not isinstance(view, str):
        ccode = parse_template(view, pjoin(folder, "views"), context=environment)
        layer = "file stream"
    else:
        filename = pjoin(folder, "views", view)
        if exists(cpath):  # compiled views
            x = view.replace("/", ".")
            files = ["views.%s.pyc" % x]
            is_compiled = exists(pjoin(cpath, files[0]))
            # Don't use a generic view if the non-compiled view exists.
            if is_compiled or (not is_compiled and not exists(filename)):
                if allow_generic:
                    files.append("views.generic.%s.pyc" % request.extension)
                # for backward compatibility
                if request.extension == "html":
                    files.append("views.%s.pyc" % x[:-5])
                    if allow_generic:
                        files.append("views.generic.pyc")
                # end backward compatibility code
                for f in files:
                    compiled = pjoin(cpath, f)
                    if exists(compiled):
                        ccode = getcfs(compiled, compiled, lambda: read_pyc(compiled))
                        layer = compiled
                        break
        # if the view is not compiled
        if not layer:
            if not exists(filename) and allow_generic:
                view = "generic." + request.extension
                filename = pjoin(folder, "views", view)
            if not exists(filename):
                raise HTTP(
                    404,
                    rewrite.THREAD_LOCAL.routes.error_message % badv,
                    web2py_error=badv,
                )
            # Parse template
            scode = parse_template(view, pjoin(folder, "views"), context=environment)
            # Compile template
            ccode = compile2(scode, filename)
            layer = filename
    restricted(ccode, environment, layer=layer, scode=scode)
    # parse_template saves everything in response body
    return environment["response"].body.getvalue()


REGEX_COMPILED_CONTROLLER = r"[\w-]+\.pyc$"


def remove_compiled_application(folder):
    """
    Deletes the folder `compiled` containing the compiled application.
    """
    try:
        shutil.rmtree(pjoin(folder, "compiled"))
        path = pjoin(folder, "controllers")
        for file in listdir(path, REGEX_COMPILED_CONTROLLER, drop=False):
            os.unlink(file)
    except OSError:
        pass


def compile_application(folder, skip_failed_views=False):
    """
    Compiles all models, views, controller for the application in `folder`.
    """
    remove_compiled_application(folder)
    os.mkdir(pjoin(folder, "compiled"))
    compile_models(folder)
    compile_controllers(folder)
    failed_views = compile_views(folder, skip_failed_views)
    return failed_views
