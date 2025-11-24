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
from pathlib import Path
from typing import Any, TypeAlias

import hdl_parser as hdl
import ucdp as u
from matchor import matchsp

Attrs: TypeAlias = dict[str, dict[str, Any]]

_RE_WIDTH = re.compile(r"\[([^\:]+)\:([^\]+])\](.*)")
_RE_M1 = re.compile(r"(.+?)(-\s*1)")
DIRMAP = {
    "input": u.IN,
    "output": u.OUT,
    "inout": u.INOUT,
}


def import_params_ports(
    mod: u.BaseMod,
    filelistname: str = "hdl",
    filepath: Path | None = None,
    paramattrs: Attrs | None = None,
    portattrs: Attrs | None = None,
) -> None:
    """Import Parameter and Ports."""
    importer = SvImporter()
    if paramattrs:
        importer.add_paramattrs(paramattrs)
    if portattrs:
        importer.add_portattrs(portattrs)
    importer.import_params_ports(mod, filelistname=filelistname, filepath=filepath)


class SvImporter(u.Object):
    """Importer."""

    paramattrs: Attrs = u.Field(default_factory=dict)
    portattrs: Attrs = u.Field(default_factory=dict)

    def add_paramattrs(self, attrs: Attrs) -> None:
        """Add Parameter Attributes."""
        self.paramattrs.update(attrs)

    def add_portattrs(self, attrs: Attrs) -> None:
        """Add Port Attributes."""
        self.portattrs.update(attrs)

    def set_paramattrs(self, name: str, attrs: Attrs) -> None:
        """Set Parameter Attributes For `name`."""
        self.paramattrs[name] = attrs

    def set_portattrs(self, name: str, attrs: Attrs) -> None:
        """Set Port Attributes For `name`."""
        self.paramattrs[name] = attrs

    def import_params_ports(self, mod: u.BaseMod, filelistname: str = "hdl", filepath: Path | None = None) -> None:
        """Import Parameter and Ports."""
        filepath = filepath or self._find_filepath(mod, filelistname)
        file = hdl.parse_file(filepath)
        for module in file.modules:
            if module.name == mod.modname:
                self._import_params(mod, module.params)
                self._import_ports(mod, module.ports)
                break
        else:
            raise ValueError(f"{filepath} does not contain module {mod.modname}")

    def _import_params(self, mod: u.BaseMod, params: tuple[hdl.Param, ...]) -> None:
        paramdict = {param.name: param for param in params}
        while paramdict:
            # first element
            param = paramdict.get(next(iter(paramdict.keys())))
            name = param.name
            # determine attrs
            attrs = self._get_attrs(self.paramattrs, param.name)
            # determine type_
            type_ = attrs.pop("type_", None)
            type_, name, _ = self._resolve_type(type_, param.name, paramdict)
            if type_ is None:
                type_ = self._get_type(mod, param)
                if param.default:
                    parsed_default = SvImporter._parse(mod, param.default)
                    if type_:
                        try:
                            type_ = type_.new(default=parsed_default)
                        except TypeError:
                            pass
                    elif isinstance(parsed_default, u.Expr):
                        type_ = parsed_default.type_
                    else:
                        type_ = self._get_param_defaulttype(default=parsed_default)
                elif not type_:
                    type_ = self._get_param_defaulttype()
            # create
            if param.ifdefs:
                attrs.setdefault("ifdefs", param.ifdefs)
            mod.add_param(type_, name, **attrs)

    def _get_param_defaulttype(self, **kwargs) -> u.BaseType:
        return u.IntegerType(**kwargs)

    def _import_ports(self, mod: u.BaseMod, ports: tuple[hdl.Port, ...]) -> None:
        portdict = {port.name: port for port in ports}
        while portdict:
            # first element
            port = portdict.get(next(iter(portdict.keys())))
            name = port.name
            # determine attrs
            attrs = self._get_attrs(self.portattrs, port.name)
            # determine type_
            type_ = attrs.pop("type_", None)
            direction = attrs.pop("direction", DIRMAP[port.direction])
            type_, name, direction = self._resolve_type(type_, port.name, portdict, direction=direction)
            if type_ is None:
                type_ = self._get_type(mod, port) or self._get_port_defaulttype()
            # create
            if port.ifdefs:
                attrs.setdefault("ifdefs", port.ifdefs)
            mod.add_port(type_, name, direction=direction, **attrs)

    def _get_port_defaulttype(self) -> u.BaseType:
        return u.BitType()

    @staticmethod
    def _find_filepath(mod: u.BaseMod, filelistname: str) -> Path:
        modfilelist = u.resolve_modfilelist(mod, filelistname, replace_envvars=True)
        if not modfilelist:
            raise ValueError(f"No filelist {filelistname!r} found.")

        try:
            return modfilelist.filepaths[0]
        except IndexError:
            raise ValueError(f"Filelist {filelistname!r} has empty 'filepaths'.") from None

    @staticmethod
    def _get_attrs(attrs: Attrs, name: str) -> dict[str, Any]:
        try:
            return dict(attrs[name])
        except KeyError:
            pass
        key = matchsp(name, attrs)
        if key:
            return dict(attrs[key])
        return {}

    @staticmethod
    def _resolve_type(
        type_: u.BaseType,
        name: str,
        itemdict: dict[str, Any],
        direction: u.Direction | None = None,
    ) -> tuple[u.BaseType, str, u.Direction | None] | None:
        if isinstance(type_, u.BaseStructType):
            if direction is None:
                idents = (u.Param(type_, "n"),)
            else:
                idents = (
                    u.Port(type_, "n_i", direction=u.IN),
                    u.Port(type_, "n_o", direction=u.OUT),
                    u.Port(type_, "n", direction=u.IN),
                    u.Port(type_, "n", direction=u.OUT),
                )
            for ident in idents:
                # try to find ident which matches `name`
                submap = {sub.name.removeprefix("n"): sub for sub in ident.iter(filter_=_svfilter)}
                for ending, subident in submap.items():
                    if name.endswith(ending) and subident.direction == direction:
                        ident = ident.new(name=f"{name.removesuffix(ending)}{ident.suffix}")  # noqa: PLW2901
                        break
                else:
                    continue
                # ensure all struct members have their friend
                subs = tuple(ident.iter(filter_=_svfilter))
                if not all(sub.name in itemdict for sub in subs):
                    continue
                # todo: check type
                # strip
                for sub in subs:
                    itemdict.pop(sub.name)
                return ident.type_, ident.name, ident.direction
            type_ = None
        itemdict.pop(name)
        return type_, name, direction

    @staticmethod
    def _get_type(mod: u.BaseMod, item: hdl.Param | hdl.Port) -> u.BaseMod | None:
        ptype = item.ptype
        dtype = getattr(item, "dtype", "").split(" ")
        dim = item.dim
        dim_unpacked = item.dim_unpacked

        type_ = None

        # Default Type
        if not ptype and not dim and not dim_unpacked:
            return type_

        if item.ptype == "integer":
            type_ = u.IntegerType()
        elif dim:
            width, left, right, sdir, dim = SvImporter._resolve_dim(mod, dim)
            if sdir != u.DOWN:
                raise ValueError(f"{mod}: {dim} is not DOWNTO")
            if "signed" in dtype:
                type_ = u.SintType(width=width, right=right)
            else:
                type_ = u.UintType(width=width, right=right)
        else:
            type_ = u.BitType()

        while dim:
            width, left, right, sdir, dim = SvImporter._resolve_dim(mod, dim)
            type_ = u.ArrayType(type_, width, left=left, right=right, direction=sdir)

        while dim_unpacked:
            width, left, right, sdir, dim_unpacked = SvImporter._resolve_dim(mod, dim_unpacked)
            type_ = u.ArrayType(type_, width, left=left, right=right, direction=sdir)

        return type_

    @staticmethod
    def _resolve_dim(mod: u.BaseMod, dim: str) -> tuple[int | u.Expr, int | u.Expr, u.SliceDirection, str]:
        m = _RE_WIDTH.match(dim)
        if not m:
            raise ValueError(f"Unknown dimension {dim}")
        left, right, rem = m.groups()
        rexpr = SvImporter._parse(mod, right)
        lexpr = SvImporter._parse(mod, left)
        # determine width
        if lexpr >= rexpr:
            wexpr = SvImporter._plus1(mod, left, lexpr)
            if rexpr:
                wexpr -= rexpr
            sdir = u.DOWN
        else:
            wexpr = SvImporter._plus1(mod, right, rexpr)
            if lexpr:
                wexpr -= lexpr
            sdir = u.UP
        return wexpr, lexpr, rexpr, sdir, rem

    @staticmethod
    def _parse(mod: u.BaseMod, value: str) -> int | u.Expr:
        try:
            return int(value)
        except ValueError:
            return mod.parser(value)

    @staticmethod
    def _plus1(mod: u.BaseMod, value: str, expr: int | u.Expr) -> int | u.Expr:
        m = _RE_M1.fullmatch(value)
        if m:
            return SvImporter._parse(mod, m.group(1))
        return expr + 1


def _svfilter(ident: u.Ident) -> bool:
    return not isinstance(ident.type_, u.BaseStructType)
