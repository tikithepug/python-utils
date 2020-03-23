import logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from atexit import register
from os import path, remove, makedirs, listdir, stat
from pyhocon import ConfigFactory
from shutil import rmtree
from subprocess import PIPE, STDOUT, Popen
from sys import exit
from datetime import datetime
from time import time
 
def get_logger(name=__name__):
    return logging.getLogger(name)
 
 
def create_parser(script_desc, arguments, arg_list):
    """Set up the argument parser object.
        Arg name | Arg description | Required | Default value | Choices"""
 
    parser = ArgumentParser(description=script_desc, formatter_class=ArgumentDefaultsHelpFormatter)
    for i in sorted(arg_list):
        if len(i) == 4:
            parser.add_argument("--" + i[0], dest=i[0], help=i[1], required=i[2], default=i[3])
        elif len(i) == 5:
            parser.add_argument("--" + i[0], dest=i[0], type=str.upper, help=i[1], required=i[2], default=i[3],
                                choices=i[4])
        else:
            parser.add_argument("--" + i[0], dest=i[0], help=i[1], required=i[2])
    return parser.parse_args(arguments)
 
 
def is_blank(key, val):
    """Check if given string is empty."""
 
    val = xstr(val).strip()
    key = xstr(key).strip()
    logger = get_logger()
    if val == "":
        logger.error("Input value '" + key + "' cannot be empty.")
        exit(-1)
    else:
        return val
 
 
def read_file(f_path):
    """Return the contents of a local file, if it exists."""
 
    if path.exists(f_path):
        f = open(f_path, "r")
        read_data = f.read()
        f.close()
        return read_data.strip()
    else:
        return None
 
 
def write_file(f_path, contents):
    """Write a string to a local file."""
 
    f = open(f_path, "w")
    f.write(contents)
    f.close()
 
 
def remove_file(f_path):
    """Remove a local file, if it exists."""
 
    if path.exists(f_path):
        remove(f_path)
 
 
def remove_folder(f_path):
    """Remove a local folder, and all of its contents."""
 
    if path.exists(f_path):
        rmtree(f_path)
 
 
def file_exists(f_path, msg_if_ne):
    """Checks if file exists, and throws an exception if it does not."""
 
    logger = get_logger()
    if not path.exists(f_path):
        logger.error(msg_if_ne)
        exit(-1)
 
 
def xstr(s):
    """Behaves like built-in str(), but returns an empty string when the argument is None."""
 
    return "" if s is None else str(s)
 
 
def run_shell(cmd_str, print_stdout=True, fail_msg=""):
    """Run a Linux shell command and return the result code."""
 
    p = Popen(cmd_str,
              shell=True,
              stderr=STDOUT,
              stdout=PIPE,
              bufsize=1,
              universal_newlines=True)
 
    logger = get_logger()
    output_lines = list()
    while True:
        output = xstr(p.stdout.readline()).strip()
        if len(output) == 0 and p.poll() is not None:
            break
        output_lines.append(output)
        if print_stdout:
            logger.info("[cmd] " + output)
 
    cmd_code = p.returncode
    cmd_stdout = "\n".join(output_lines)
    if cmd_code != 0 and fail_msg != "":
        logger.error(fail_msg)
        exit(-1)
 
    return cmd_code, cmd_stdout
 
 
def do_cleanup(dir_path, n):
    """Clean up files within a particular directory older than n days."""
 
    all_files = listdir(dir_path)
    now = time()
    n_days = n * 86400
    for f in all_files:
        file_path = path.join(dir_path, f)
        if not path.isfile(file_path):
            continue
        if stat(file_path).st_mtime < (now - n_days):
            remove(file_path)
 
 
def set_up_io(tmp_path, log_path, log_name, log_lvl="INFO"):
    """Set up tmp/log directories and logging handlers."""
 
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
   
    # Set up temp location.
    remove_folder(tmp_path)
    makedirs(tmp_path)
 
    # Set up logging.
    if log_name == "":
        log_name = path.splitext(path.basename(__file__))[0] + "_" + date_str + ".log"
    makedirs(log_path, exist_ok=True)
    do_cleanup(log_path, 30)
 
    logging.basicConfig(
        level=getattr(logging, log_lvl.upper()),
        format="%(asctime)s: [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(filename=log_path + "/" + log_name, mode="w", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
 
    register(remove_folder, tmp_path)
    return tmp_path
