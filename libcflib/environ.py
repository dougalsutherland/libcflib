"""Custom environment handling tools for libcflib."""
import os
import builtins
from collections import OrderedDict
from contextlib import contextmanager
from collections.abc import MutableMapping

from xonsh.environ import Ensurer, VarDocs
from xonsh.tools import (is_string, ensure_string, always_false, always_true, is_bool,
                         is_string_set, csv_to_set, set_to_csv, is_nonstring_seq_of_strings,
                         to_bool, bool_to_str, expand_path, is_int, is_float)

from libcflib.tools import expand_file_and_mkdirs


ENV = builtins.__xonsh_env__


def csv_to_list(x):
    """Converts a comma separated string to a list of strings."""
    return x.split(',')


def list_to_csv(x):
    """Converts a list of str to a comma-separated string."""
    return ','.join(x)


def is_dict_str_str_or_none(x):
    """Checks if x is a mutable mapping from strings to strings or None"""
    if x is None:
        return True
    elif not isinstance(x, MutableMapping):
        return False
    # now we know we have a mapping, check items.
    for key, value in x.items():
        if not isinstance(key, str) or not isinstance(value, str):
            return False
    return True


def libcflib_config_dir():
    """Ensures and returns the $LIBCFLIB_CONFIG_DIR"""
    fcd = os.path.expanduser(os.path.join(ENV.get('XDG_CONFIG_HOME'), 'libcflib'))
    os.makedirs(fcd, exist_ok=True)
    return fcd


def libcflib_data_dir():
    """Ensures and returns the $LIBCFLIB_DATA_DIR"""
    fdd = os.path.expanduser(os.path.join(ENV.get('XDG_DATA_HOME'), 'libcflib'))
    os.makedirs(fdd, exist_ok=True)
    return fdd


def libcflib_logfile():
    """Ensures and returns the $LIBCFLIB_LOGFILE"""
    flf = os.path.join(ENV.get('LIBCFLIB_DATA_DIR'), 'log.json')
    flf = expand_file_and_mkdirs(flf)
    return flf


# key = name
# value = (default, validate, convert, detype, docstr)
# this needs to be ordered so that the default are applied in the correct order
ENVVARS = OrderedDict([
    ('LIBCFLIB_CONFIG_DIR', (libcflib_config_dir, is_string, str, ensure_string,
                             'Path to libcflib configuration directory')),
    ('LIBCFLIB_DATA_DIR', (libcflib_data_dir, is_string, str, ensure_string,
                           'Path to libcflib data directory')),
    ('LIBCFLIB_LOGFILE', (libcflib_logfile, always_false, expand_file_and_mkdirs,
                          ensure_string, 'Path to the libcflib logfile.')),
    ])


_ENV_SETUP = False


def setup():
    global _ENV_SETUP
    if _ENV_SETUP:
        return
    for key, (default, validate, convert, detype, docstr) in ENVVARS.items():
        if key in ENV:
            del ENV[key]
        ENV._defaults[key] = default() if callable(default) else default
        ENV._ensurers[key] = Ensurer(validate=validate, convert=convert,
                                     detype=detype)
        ENV._docs[key] = VarDocs(docstr=docstr)
    _ENV_SETUP = True


def teardown():
    global _ENV_SETUP
    if not _ENV_SETUP:
        return
    for key in ENVVARS:
        ENV._defaults.pop(key)
        ENV._ensurers.pop(key)
        ENV._docs.pop(key)
        if key in ENV:
            del ENV[key]
    _ENV_SETUP = False


@contextmanager
def context():
    """A context manager for entering and leaving the fixie environment
    safely. This context manager is reentrant and will only be executed
    if it hasn't already been entered.
    """
    global _ENV_SETUP
    if _ENV_SETUP:
        yield
        return
    setup()
    yield
    teardown()


def libcflib_envvar_names():
    """Returns the fixie environment variable names as a set of str."""
    names = set(ENVVARS.keys())
    return names


def libcflib_detype_env():
    """Returns a detyped version of the environment containing only the fixie
    environment variables.
    """
    keep = libcflib_envvar_names()
    denv = {k: v for k, v in ENV.detype().items() if k in keep}
    return denv