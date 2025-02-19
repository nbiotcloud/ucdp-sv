#
# MIT License
#
# Copyright (c) 2025 nbiotcloud
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""SystemVerilog Importer."""

import re
from collections.abc import Sequence
from typing import Any, TypeAlias

import ucdp as u
from matchor import is_pattern, matchsp
from sv_simpleparser._sv_parser import parse_sv

_RE_WIDTH = re.compile(r"\[([^\:]+?)(\-1)?\:([^\]+])\]")
DIRMAP = {
    "input": u.IN,
    "output": u.OUT,
    "inout": u.INOUT,
}

Attrs: TypeAlias = dict[str, dict[str, Any]]


def import_params_ports(
    mod: u.BaseMod,
    filelistname: str = "hdl",
    paramattrs: Attrs | None = None,
    portattrs: Attrs | None = None,
):
    """Import Parameter and Ports."""
    module = _find_module(mod, filelistname=filelistname)

    paramattrs_ = _preprocess_attrs(paramattrs)
    portattrs_ = _preprocess_attrs(portattrs)

    ifdef = None
    for param in module.param_decl:
        name = param.name[0]
        attrs = _get_attrs(paramattrs_, name)
        attrs.setdefault("type_", _get_type(mod.params, param.ptype or "", param.width or ""))
        attrs.setdefault("ifdef", ifdef)
        type_ = attrs.pop("type_")
        mod.add_param(type_, name, **attrs)
        ifdef = _handle_ifdef(attrs["ifdef"], param.name)

    ifdef = None
    for port in module.port_decl:
        name = port.name[0]
        attrs = _get_attrs(portattrs_, name)
        attrs.setdefault("type_", _get_type(mod.params, port.ptype or "", port.width or ""))
        attrs.setdefault("direction", DIRMAP[port.direction])
        attrs.setdefault("ifdef", ifdef)
        type_ = attrs.pop("type_")
        mod.add_port(type_, name, **attrs)
        ifdef = _handle_ifdef(attrs["ifdef"], port.name)


def _find_module(mod: u.BaseMod, filelistname: str):
    modfilelist = u.resolve_modfilelist(mod, filelistname, replace_envvars=True)
    if not modfilelist:
        raise ValueError(f"No filelist {filelistname!r} found.")

    try:
        filepath = modfilelist.filepaths[0]
    except IndexError:
        raise ValueError(f"Filelist {filelistname!r} has empty 'filepaths'.") from None

    modules = parse_sv(filepath)

    try:
        return modules[0]
    except IndexError:
        raise ValueError(f"{str(filepath)!r} does not contain SystemVerilog modules") from None


def _preprocess_attrs(attrs: Attrs | None) -> tuple[Attrs, Attrs]:
    if not attrs:
        return {}, {}
    patts = {key: value for key, value in attrs.items() if is_pattern(key)}
    names = {key: value for key, value in attrs.items() if not is_pattern(key)}
    return patts, names


def _get_attrs(attrs: tuple[Attrs, Attrs], name: str) -> dict[str, Any]:
    patts, names = attrs
    try:
        return names.pop(name)
    except KeyError:
        pass
    key = matchsp(name, patts)
    if key:
        return patts[key]
    return {}


def _get_type(namespace: u.Namespace, ptype: str, width: str) -> u.BaseType:
    """Determine UCDP Type."""
    if not ptype:
        return u.BitType()
    if ptype == "integer":
        assert not width, width
        return u.IntegerType()
    if ptype in ("logic", "wire"):
        if width:
            width, right = _get_width(namespace, width)
            return u.UintType(right=right, width=width)
        return u.BitType()

    raise ValueError(f"Unknown Type {ptype}")


def _get_width(namespace: u.Namespace, width: str) -> tuple[str, str]:
    m = _RE_WIDTH.match(width)
    if not m:
        raise ValueError(f"Unknown width {width}")
    left, m1, right = m.groups((1, 2))
    # Try to convert string to integer or find symbol in namespace
    try:
        right = int(right)
    except ValueError:
        right = namespace[right]
    # Try to convert string to integer or find symbol in namespace
    try:
        width = int(left)
        if m1:
            width = width + 1
    except ValueError:
        width = namespace[left]
        if m1 and right:
            width = width + 1

    return width, right


def _handle_ifdef(ifdef: str | None, name: Sequence[str]) -> str | None:
    # ifdef
    try:
        if name[1] == "ifdef":
            ifdef = name[2]
    except IndexError:
        pass
    # nedif
    try:
        if name[1] == "endif":
            ifdef = None
    except IndexError:
        pass

    return ifdef
