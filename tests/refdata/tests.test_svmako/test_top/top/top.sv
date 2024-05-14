// =============================================================================
//
// Module:     top.top
// Data Model: top.top.TopMod
//
// =============================================================================


module top #( // top.top.TopMod
  parameter integer width_p = 10,
  parameter integer sub_p   = (width_p / 2)
) (
  // main_i
  input  wire           main_clk_i,
  input  wire           main_rst_an_i, // Async Reset (Low-Active)
  // intf_i: RX/TX
  output logic          intf_rx_o,
  input  wire           intf_tx_i,
  // bus_i
  input  wire  [2-1:0]  bus_trans_i,
  input  wire  [32-1:0] bus_addr_i,
  input  wire           bus_write_i,
  input  wire  [32-1:0] bus_wdata_i,
  output logic          bus_ready_o,
  output logic          bus_resp_o,
  output logic [32-1:0] bus_rdata_o
);



  // ------------------------------------------------------
  //  Local Parameter
  // ------------------------------------------------------
  localparam integer cntwidth_p = $clog2((width_p + 1));


  // ------------------------------------------------------
  //  Signals
  // ------------------------------------------------------
  logic clk_s;


  // ------------------------------------------------------
  //  glbl.clk_gate: u_clk_gate
  // ------------------------------------------------------
  clk_gate u_clk_gate (
    .clk_i(main_clk_i),
    .clk_o(clk_s     ),
    .ena_i(1'b0      )  // TODO
  );


  // ------------------------------------------------------
  //  top.top_core: u_core
  // ------------------------------------------------------
  top_core #(
    .width_p(width_p)
  ) u_core (
    // main_i
    .main_clk_i   (clk_s        ),
    .main_rst_an_i(main_rst_an_i), // Async Reset (Low-Active)
    .data_i       (10'h000      ), // TODO
    .data_o       (             ), // TODO
    // intf_i: RX/TX
    .intf_rx_o    (intf_rx_o    ),
    .intf_tx_i    (intf_tx_i    )
  );

endmodule // top
