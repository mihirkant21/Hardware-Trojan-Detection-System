// ============================================================
// Module: alu_logic
// Description: Bitwise logic operations for 16-bit ALU
//
// Opcode Map:
//   4'b0100 (4)  : AND
//   4'b0101 (5)  : OR
//   4'b0110 (6)  : XOR
//   4'b0111 (7)  : NOT  (bitwise NOT of A)
//   4'b1000 (8)  : NAND
//   4'b1001 (9)  : NOR
//   4'b1010 (10) : XNOR
// ============================================================
`timescale 1ns / 1ps

module alu_logic (
    input  wire [15:0] A,
    input  wire [15:0] B,
    input  wire [3:0]  opcode,
    output reg  [15:0] result
);

    always @(*) begin
        case (opcode)
            4'b0100: result = A & B;          // AND
            4'b0101: result = A | B;          // OR
            4'b0110: result = A ^ B;          // XOR
            4'b0111: result = ~A;             // NOT A
            4'b1000: result = ~(A & B);       // NAND
            4'b1001: result = ~(A | B);       // NOR
            4'b1010: result = ~(A ^ B);       // XNOR
            default: result = 16'h0000;
        endcase
    end

endmodule
