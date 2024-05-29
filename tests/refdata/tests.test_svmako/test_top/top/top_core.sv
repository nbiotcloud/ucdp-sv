// =============================================================================
//
// Module:     top.top_core
// Data Model: top.top.TopCoreMod
//
// =============================================================================


module top_core #( // top.top.TopCoreMod
  parameter integer       param_p = param_p,
  parameter integer       width_p = width_p,
  parameter signed  [7:0] other_p = 8'shFD
) (
  // main_i
  input  wire                main_clk_i,
  input  wire                main_rst_an_i,                    // Async Reset (Low-Active)
  input  wire  [param_p-1:0] p_i,
  output logic [param_p-1:0] p_o,
  input  wire  [width_p-1:0] data_i,
  output logic [width_p-1:0] data_o,
  input  wire  [7:0]         array_i        [0:0+(param_p-1)],
  input  wire  [7:0]         array_open_i   [0:7],
  // intf_i: RX/TX
  output logic               intf_rx_o,
  input  wire                intf_tx_i
);


endmodule // top_core
