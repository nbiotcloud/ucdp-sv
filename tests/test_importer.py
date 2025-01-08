#
# MIT License
#
# Copyright (c) 2024 nbiotcloud
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
"""Test Importer."""

import ucdp as u
import ucdpsv as usv


class TopMod(u.AMod):
    """Example Module."""

    filelists: u.ClassVar[u.ModFileLists] = (u.ModFileList(name="hdl", filepaths=("testdata/importer/top.sv",)),)

    def _build(self) -> None:
        usv.import_params_ports(self)


def test_verilog2ports():
    """Test verilog2ports."""
    top = TopMod()
    assert tuple(top.params) == (
        u.Param(u.IntegerType(), "param_p"),
        u.Param(u.IntegerType(), "width_p"),
        u.Param(u.UintType(u.Param(u.IntegerType(), "param_p")), "default_p"),
    )
    assert tuple(top.ports) == (
        u.Port(u.BitType(), "main_clk_i", direction=u.IN),
        u.Port(u.BitType(), "main_rst_an_i", direction=u.IN),
        u.Port(u.BitType(), "intf_rx_o", direction=u.OUT),
        u.Port(u.BitType(), "intf_tx_i", direction=u.IN),
        u.Port(u.UintType(2), "bus_trans_i", direction=u.IN),
        u.Port(u.UintType(32), "bus_addr_i", direction=u.IN),
        u.Port(u.BitType(), "bus_write_i", direction=u.IN),
        u.Port(u.UintType(32), "bus_wdata_i", direction=u.IN),
        u.Port(u.BitType(), "bus_ready_o", direction=u.OUT),
        u.Port(u.BitType(), "bus_resp_o", direction=u.OUT),
        u.Port(u.UintType(32), "bus_rdata_o", direction=u.OUT),
        u.Port(u.UintType(9), "brick_o", direction=u.OUT, ifdef="ASIC"),
        u.Port(u.UintType(u.Param(u.IntegerType(), "param_p")), "data_i", direction=u.IN),
        u.Port(u.UintType(u.Param(u.IntegerType(), "width_p")), "cnt_o", direction=u.OUT),
        u.Port(u.BitType(), "key_valid_i", direction=u.IN),
        u.Port(u.BitType(), "key_accept", direction=u.OUT),
        u.Port(u.UintType(9), "key_data", direction=u.IN),
        u.Port(u.UintType(4), "bidir", direction=u.INOUT),
        u.Port(u.UintType(9), "value_o", direction=u.OUT, ifdef="ASIC"),
    )
