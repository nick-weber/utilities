# -*- coding: utf-8 -*-
"""
A collection of decorator functions, many of which were taken from this tutorial:
https://realpython.com/primer-on-python-decorators/
"""

import functools
import time
import pint
import os
import xarray


def timer(func):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()    # 1
        value = func(*args, **kwargs)
        end_time = time.perf_counter()      # 2
        run_time = end_time - start_time    # 3
        print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
        return value
    return wrapper_timer


def debug(func):
    """Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]                      # 1
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
        signature = ", ".join(args_repr + kwargs_repr)           # 3
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")           # 4
        return value
    return wrapper_debug


def slow_down(_func=None, *, num_secs=1):
    """Sleep 'num_secs' seconds before calling the function"""
    def decorator_slow_down(func):
        @functools.wraps(func)
        def wrapper_slow_down(*args, **kwargs):
            time.sleep(num_secs)
            return func(*args, **kwargs)
        return wrapper_slow_down

    if _func is None:             # argument(s) passed
        return decorator_slow_down
    else:                         # no argument(s) passed
        return decorator_slow_down(_func)


def repeat(_func=None, *, num_times=2):
    """Repeats the function 'num_times' times"""
    def decorator_repeat(func):
        @functools.wraps(func)
        def wrapper_repeat(*args, **kwargs):
            for _ in range(num_times):
                value = func(*args, **kwargs)
            return value
        return wrapper_repeat

    if _func is None:             # argument(s) passed
        return decorator_repeat
    else:                         # no argument(s) passed
        return decorator_repeat(_func)


def count_calls(_func, *, verbose=True):
    """Keeps track of the number of times a function is called"""
    def decorator_count_calls(func):
        @functools.wraps(func)
        def wrapper_count_calls(*args, **kwargs):
            wrapper_count_calls.num_calls += 1
            if verbose:
                print(f"Call {wrapper_count_calls.num_calls} of {func.__name__!r}")
            return func(*args, **kwargs)
        wrapper_count_calls.num_calls = 0
        return wrapper_count_calls

    if _func is None:             # argument(s) passed
        return decorator_count_calls
    else:                         # no argument(s) passed
        return decorator_count_calls(_func)


def cache(func):
    """Keeps a cache of previous function calls"""
    @functools.wraps(func)
    def wrapper_cache(*args, **kwargs):
        cache_key = args + tuple(kwargs.items())
        if cache_key not in wrapper_cache.cache:
            wrapper_cache.cache[cache_key] = func(*args, **kwargs)
        return wrapper_cache.cache[cache_key]
    wrapper_cache.cache = dict()
    return wrapper_cache


def set_unit(unit):
    """Register a unit on a function"""
    def decorator_set_unit(func):
        func.unit = unit
        return func
    return decorator_set_unit


def use_unit(unit):
    """Have a function return a Quantity with given unit"""
    use_unit.ureg = pint.UnitRegistry()
    def decorator_use_unit(func):
        @functools.wraps(func)
        def wrapper_use_unit(*args, **kwargs):
            value = func(*args, **kwargs)
            return value * use_unit.ureg(unit)
        return wrapper_use_unit
    return decorator_use_unit


def nc_dump(_func=None, *, filename=None, store_path=None, keep_chars=15):
    """
    Wraps a function that returns an xarray Dataset.
    If this is the first execution of that function, the Dataset
    will be dumped to netCDF. If not, then the previously dumped
    netCDF will be loaded instead of executing the function again.

    Args
    ----
    filename : str
        Name of the netcdf file to be written/read (optional).
    store_path : str
        Path to directory where nc_dump subdirectory will be created (for netcdf storage).
    keep_chars : int
        The maximum number of characters in the auto-generated netcdf
        filename (only applies if filename is None).
    """
    def decorator_nc_dump(func):
        @functools.wraps(func)
        def wrapper_nc_dump(*args, **kwargs):
            if filename is None:
                if 'nc_dump_file' in kwargs.keys() and kwargs['nc_dump_file'] is not None:
                    nc_filename = kwargs['nc_dump_file']
                else:
                    all_args = args + tuple([str(k)+str(v) for k,v in kwargs.items()])
                    nc_filename = '_'.join([str(a) for a in all_args])
                    for badstr in [' ', ':', '(', ')', '[', ']', '\n', ',', '.']:
                        nc_filename = nc_filename.replace(badstr, '')
                    nc_filename = nc_filename[:keep_chars] + '.nc'
            else:
                nc_filename = filename
            if store_path is None:
                nc_dir = os.path.join(os.getcwd(), 'nc_dump')
            else:
                nc_dir = os.path.join(store_path, 'nc_dump')
            nc_fullpath = os.path.join(nc_dir, nc_filename)
            if os.path.isfile(nc_fullpath):
                ds = xarray.open_dataset(nc_fullpath)
            else:
                ds = func(*args, **kwargs)
                if not os.path.isdir(nc_dir):
                    os.makedirs(nc_dir)
                if ds is not None:
                    ds.to_netcdf(nc_fullpath)
            return ds
        return wrapper_nc_dump

    if _func is None:             # argument(s) passed
        return decorator_nc_dump
    else:                         # no argument(s) passed
        return decorator_nc_dump(_func)
