// ============================================================
// Module: alu_arithmetic
// Description: Handles arithmetic operations for 16-bit ALU
//
// Opcode Map:
//   4'b0000 (0)  : ADD  — A + B
//   4'b0001 (1)  : SUB  — A - B
//   4'b0010 (2)  : MUL  — A * B (lower 16 bits)
//   4'b0011 (3)  : DIV  — A / B (integer quotient)
// ============================================================
`timescale 1ns / 1ps

module alu_arithmetic (
    input  wire [15:0] A,
    input  wire [15:0] B,
    input  wire [3:0]  opcode,
    output reg  [15:0] result,
    output reg         carry_out,
    output reg         overflow
);

    reg [16:0] temp;

    always @(*) begin
        carry_out = 1'b0;
        overflow  = 1'b0;
        result    = 16'h0000;

        case (opcode)
            4'b0000: begin
                temp      = {1'b0, A} + {1'b0, B};
                result    = temp[15:0];
                carry_out = temp[16];
                overflow  = (~A[15] & ~B[15] & result[15]) |
                            ( A[15] &  B[15] & ~result[15]);
            end
            4'b0001: begin
                temp      = {1'b0, A} + {1'b0, ~B} + 17'd1;
                result    = temp[15:0];
                carry_out = temp[16];
                overflow  = (~A[15] &  B[15] & result[15]) |
                            ( A[15] & ~B[15] & ~result[15]);
            end
            4'b0010: begin
                result    = A * B;
                carry_out = 1'b0;
                overflow  = 1'b0;
            end
            4'b0011: begin
                if (B == 16'h0000) begin
                    result    = 16'hFFFF;
                    carry_out = 1'b1;
                end else begin
                    result    = A / B;
                    carry_out = 1'b0;
                end
                overflow = 1'b0;
            end
            default: begin
                result    = 16'h0000;
                carry_out = 1'b0;
                overflow  = 1'b0;
            end
        endcase
    end

endmodule
