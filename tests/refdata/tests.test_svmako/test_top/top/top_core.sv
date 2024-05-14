// =============================================================================
//
// Module:     top.top_core
// Data Model: top.top.TopCoreMod
//
// =============================================================================


module top_core #( // top.top.TopCoreMod
  parameter integer width_p = 10,
  parameter integer depth_p = 4
) (
  // main_i
  input  wire                  main_clk_i,
  input  wire                  main_rst_an_i, // Async Reset (Low-Active)
  input  wire  [(width_p-1):0] data_i,
  output logic [(width_p-1):0] data_o,
  // intf_i: RX/TX
  output logic                 intf_rx_o,
  input  wire                  intf_tx_i
);


endmodule // top_core
