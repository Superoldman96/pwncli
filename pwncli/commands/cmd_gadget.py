#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    : cmd_gadget.py
@Time    : 2023/03/28 14:09:58
@Author  : Roderick Chan
@Email   : roderickchan@foxmail.com
@Desc    : None
'''



import os
import shlex
import subprocess

import click
from pwn import wget, which

from ..cli import _set_filename, pass_environ
from ..utils.misc import _Inner_Dict

@click.command(name="gadget", short_help="Get all gadgets using ropper and ROPgadget, and then store them in files.")
@click.argument('filename', type=str, default=None, required=False, nargs=1)
@click.option('-a', '--all', '--all-gadgets', "all_gadgets", is_flag=True, show_default=True, help="Get all gadgets and don't remove duplicates.")
@click.option('-d', '--dir', '--directory', "directory", type=click.Path(exists=True, dir_okay=True), default=".", required=False, help="The directory to save files.")
@click.option('-x', '--opcode', "opcode", type=str, default="", required=False, help="The opcode mode.")
@click.option('-n', '--depth', '--count', "depth", type=int, default=-1, required=False, help="The depth of the gadgets.")
@click.option('-v', '--verbose', count=True, help="Show more info or not.")
@pass_environ
def cli(ctx, filename, all_gadgets, directory, depth, opcode, verbose):
    """
    FILENAME: The binary file name.
    
    \b
    pwncli gadget ./pwn -d ./gadgets -a -n 20
    pwncli gadget ./pwn -x 015dc3
    
    pwncli g ./pwn -n 10
    """
    if not ctx.verbose:
        ctx.verbose = verbose
    if verbose:
        ctx.vlog("gadget-command --> Open 'verbose' mode")

    _set_filename(ctx, filename)

    if not ctx.get('filename'):
        ctx.abort(
            "gadget-command ---> No filename, please specify the binary file.")

    ropper_path = which("ropper")
    ropgadget_path = which("ROPgadget")
    
    rp_name = "rp-lin"
    rp_path = None # which(rp_name)

    if len(opcode) > 0:
        opcode = opcode.strip()
        opcode = opcode.strip("'")
        opcode = opcode.strip("\"")

        len_ = len(opcode)
        if len_ > 0 and len_ % 2 == 0:
            pass
        else:
            ctx.abort("gadget-command ---> The opcode is invalid.")

        if rp_path:
            n_ = ""
            for i in range(0, len_, 2):
                n_ += "\\x"
                n_ += opcode[i:i+2]
            opcode = n_
            cmd = "{} -f {} --search-hexa \"{}\"".format(
                rp_name,
                filename, opcode)
        elif ropgadget_path:
            cmd = "ROPgadget --binary {} --opcode {}".format(filename, opcode)
        elif ropper_path:
            cmd = "ropper -f {} --opcode {}".format(filename, opcode)
        else:
            ctx.abort(
                "gadget-command ---> No rop tools exists, please install one.")
        ctx.vlog("gadget-command ---> Exec cmd: {}".format(cmd))
        os.system(cmd)
        return

    if not os.path.isdir(directory):
        ctx.abort("gadget-command ---> The 'directory' is invalid.")

    if False:
        rp_url_link = "https://github.com/0vercl0k/rp/releases/download/v2.1.3/rp-lin-clang.zip"
        res = input(
            "Install {} from {}? [y/n]".format(rp_name, rp_url_link))
        if res.strip().lower() == "y":
            try:
                wget(rp_url_link, timeout=300, save=True)
                rp_filename = rp_url_link.split("/")[-1]
                
                cmd = "unzip {}".format(rp_filename)
                ctx.vlog("gadget-command ---> Exec cmd: {}".format(cmd))
                os.system(cmd)
                
                os.unlink(rp_filename)
                
                bin_path = "$HOME/.local/bin" if os.getuid() != 0 else "/usr/local/bin"

                cmd = "chmod +x {}".format(rp_name)
                ctx.vlog("gadget-command ---> Exec cmd: {}".format(cmd))
                os.system(cmd)
                
                cmd = "mv {} {}".format(rp_name, bin_path)
                ctx.vlog("gadget-command ---> Exec cmd: {}".format(cmd))
                os.system(cmd)
                
                if which(rp_name):
                    rp_path = 1
                else:
                    rp_path = 0
            except:
                ctx.verrlog("gadget-command ---> Download {} error!".format(rp_name))
    ps = []
    if rp_path:
        cmd = "{} -f {} ".format(rp_name, filename)
        if not all_gadgets:
            cmd += " --unique "
        if depth > 0:
            cmd += " -r {} ".format(depth)
        else:
            cmd += " -r 6 "
        store_file = "{}".format(os.path.join(
            directory, "rp_gadgets-" + os.path.split(ctx.get('filename'))[1]))
        ctx.vlog(
            "gadget-command ---> Exec cmd: {} and store in {}".format(cmd, store_file))
        p = subprocess.Popen(shlex.split(cmd), stdout=open(
            store_file, "wt", encoding='utf-8', errors='ignore'))
        # ps.append(p)

    if ropgadget_path:
        cmd = "ROPgadget --binary {}".format(filename)
        if all_gadgets:
            cmd += " --all"
        if depth > 0:
            cmd += " --depth {}".format(depth)
        store_file = "{}".format(os.path.join(
            directory, "ropgadget_gadgets-" + os.path.split(ctx.get('filename'))[1]))
        ctx.vlog(
            "gadget-command ---> Exec cmd: {} and store in {}".format(cmd, store_file))
        p = subprocess.Popen(shlex.split(cmd), stdout=open(
            store_file, "wt", encoding='utf-8', errors='ignore'))
        # ps.append(p)

    if ropper_path and (not ropgadget_path):
        cmd = "ropper -f {} --nocolor".format(filename)
        if all_gadgets:
            cmd += " --all"
        if depth > 0:
            cmd += " --inst-count {}".format(depth)
        store_file = "{}".format(os.path.join(
            directory, "ropper_gadgets-" + os.path.split(ctx.get('filename'))[1]))
        ctx.vlog(
            "gadget-command ---> Exec cmd: {} and store in {}".format(cmd, store_file))
        p = subprocess.Popen(shlex.split(cmd), stdout=open(
            store_file, "wt", encoding='utf-8', errors='ignore'))
        ps.append(p)

    for p in ps:
        p.wait()
        p.terminate()