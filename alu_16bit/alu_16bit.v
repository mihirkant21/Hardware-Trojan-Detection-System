// ============================================================
// Module: alu_16bit (Top-Level)
// Description: 16-bit ALU with 16 operations, 4-bit opcode,
//              and Z, C, V, S status flags.
//
// Full Instruction Set (4-bit opcode):
// ┌────────┬──────┬───────────────────────────────────────┐
// │ Opcode │ Mnem │ Operation                             │
// ├────────┼──────┼───────────────────────────────────────┤
// │  0000  │ ADD  │ A + B                                 │
// │  0001  │ SUB  │ A - B                                 │
// │  0010  │ MUL  │ A * B (lower 16 bits)                 │
// │  0011  │ DIV  │ A / B (integer quotient)              │
// │  0100  │ AND  │ A & B                                 │
// │  0101  │ OR   │ A | B                                 │
// │  0110  │ XOR  │ A ^ B                                 │
// │  0111  │ NOT  │ ~A                                    │
// │  1000  │ NAND │ ~(A & B)                              │
// │  1001  │ NOR  │ ~(A | B)                              │
// │  1010  │ XNOR │ ~(A ^ B)                              │
// │  1011  │ SHL  │ A << B[3:0]                           │
// │  1100  │ SHR  │ A >> B[3:0] (logical)                 │
// │  1101  │ SAR  │ A >>> B[3:0] (arithmetic)             │
// │  1110  │ ROL  │ Rotate A left by B[3:0]               │
// │  1111  │ ROR  │ Rotate A right by B[3:0]              │
// └────────┴──────┴───────────────────────────────────────┘
//
// Flags:
//   Z - Zero:     result == 0
//   C - Carry:    carry-out / borrow from arithmetic
//   V - Overflow: signed overflow (ADD/SUB only)
//   S - Sign:     MSB of result (bit 15)
// ============================================================
`timescale 1ns / 1ps

module alu_16bit (
    input  wire [15:0] A,           // Operand A
    input  wire [15:0] B,           // Operand B
    input  wire [3:0]  opcode,      // 4-bit operation selector
    output wire [15:0] result,      // 16-bit result
    output wire        Z,           // Zero flag
    output wire        C,           // Carry flag
    output wire        V,           // Overflow flag
    output wire        S            // Sign flag
);

    // ── Internal wires ──────────────────────────────────────
    wire [15:0] arith_result;
    wire [15:0] logic_result;
    wire [15:0] shift_result;
    wire        arith_carry;
    wire        arith_overflow;

    // ── Sub-module Instantiations ────────────────────────────

    alu_arithmetic ARITH (
        .A         (A),
        .B         (B),
        .opcode    (opcode),
        .result    (arith_result),
        .carry_out (arith_carry),
        .overflow  (arith_overflow)
    );

    alu_logic LOGIC (
        .A      (A),
        .B      (B),
        .opcode (opcode),
        .result (logic_result)
    );

    alu_shifter SHIFT (
        .A      (A),
        .B      (B),
        .opcode (opcode),
        .result (shift_result)
    );

    // ── Output Multiplexer ───────────────────────────────────
    // Select result from correct sub-module based on opcode
    //   Arithmetic : opcodes 0000 - 0011
    //   Logic      : opcodes 0100 - 1010
    //   Shifter    : opcodes 1011 - 1111
    reg [15:0] mux_result;

    always @(*) begin
        casez (opcode)
            4'b00??: mux_result = arith_result;   // 0-3: Arithmetic
            4'b010?: mux_result = logic_result;   // 4-5: Logic
            4'b011?: mux_result = logic_result;   // 6-7: Logic
            4'b100?: mux_result = logic_result;   // 8-9: Logic
            4'b1010: mux_result = logic_result;   // 10:  Logic
            4'b1011: mux_result = shift_result;   // 11:  SHL
            4'b1100: mux_result = shift_result;   // 12:  SHR
            4'b1101: mux_result = shift_result;   // 13:  SAR
            4'b1110: mux_result = shift_result;   // 14:  ROL
            4'b1111: mux_result = shift_result;   // 15:  ROR
            default: mux_result = 16'h0000;
        endcase
    end

    assign result = mux_result;

    // ── Flags Module ─────────────────────────────────────────
    alu_flags FLAGS (
        .result      (mux_result),
        .carry_out   (arith_carry),
        .overflow_in (arith_overflow),
        .opcode      (opcode),
        .Z           (Z),
        .C           (C),
        .V           (V),
        .S           (S)
    );

endmodule
