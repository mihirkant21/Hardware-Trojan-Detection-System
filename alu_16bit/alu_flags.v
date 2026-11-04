// ============================================================
// Module: alu_flags
// Description: Computes Z, C, V, S flags from ALU result
//   Z (Zero)     : result == 0
//   C (Carry)    : carry-out from bit 16 (arithmetic ops)
//   V (Overflow) : signed overflow for ADD/SUB
//   S (Sign)     : MSB of result (bit 15)
// ============================================================
`timescale 1ns / 1ps

module alu_flags (
    input  wire [15:0] result,      // 16-bit ALU result
    input  wire        carry_out,   // Raw carry from adder
    input  wire        overflow_in, // Overflow from arithmetic
    input  wire [3:0]  opcode,      // To qualify which flags are valid
    output reg         Z,           // Zero flag
    output reg         C,           // Carry flag
    output reg         V,           // Overflow flag
    output reg         S            // Sign flag
);

    always @(*) begin
        // Zero flag: always valid
        Z = (result == 16'h0000) ? 1'b1 : 1'b0;

        // Sign flag: MSB of result, always valid
        S = result[15];

        // Carry flag: valid for arithmetic ops (ADD=0, SUB=1, MUL=2, DIV=3)
        // and shift ops (SHL=11, SHR=12, SAR=13, ROL=14, ROR=15)
        case (opcode)
            4'b0000: C = carry_out;   // ADD
            4'b0001: C = carry_out;   // SUB (borrow)
            4'b0010: C = 1'b0;        // MUL - no carry defined
            4'b0011: C = carry_out;   // DIV - carry=1 signals div-by-zero
            default: C = 1'b0;        // Logic/shift ops: carry = 0
        endcase

        // Overflow flag: valid only for ADD and SUB
        case (opcode)
            4'b0000: V = overflow_in; // ADD
            4'b0001: V = overflow_in; // SUB
            default: V = 1'b0;
        endcase
    end

endmodule
