// ============================================================
// Module: alu_shifter
// Description: Shift and Rotate operations for 16-bit ALU
//
// Opcode Map:
//   4'b1011 (11) : SHL  — Shift Left Logical  (A << B[3:0])
//   4'b1100 (12) : SHR  — Shift Right Logical (A >> B[3:0])
//   4'b1101 (13) : SAR  — Shift Right Arithmetic (sign-extended)
//   4'b1110 (14) : ROL  — Rotate Left
//   4'b1111 (15) : ROR  — Rotate Right
// ============================================================
`timescale 1ns / 1ps

module alu_shifter (
    input  wire [15:0] A,
    input  wire [15:0] B,       // B[3:0] = shift amount (0-15)
    input  wire [3:0]  opcode,
    output reg  [15:0] result
);

    wire [3:0] shamt = B[3:0];  // Shift amount (4 bits = max 15)

    always @(*) begin
        case (opcode)
            // SHL: Logical left shift
            4'b1011: result = A << shamt;

            // SHR: Logical right shift (zero-filled)
            4'b1100: result = A >> shamt;

            // SAR: Arithmetic right shift (sign-bit filled)
            4'b1101: result = $signed(A) >>> shamt;

            // ROL: Rotate Left — bits shifted out wrap to LSB
            4'b1110: begin
                if (shamt == 4'd0)
                    result = A;
                else
                    result = (A << shamt) | (A >> (16 - shamt));
            end

            // ROR: Rotate Right — bits shifted out wrap to MSB
            4'b1111: begin
                if (shamt == 4'd0)
                    result = A;
                else
                    result = (A >> shamt) | (A << (16 - shamt));
            end

            default: result = 16'h0000;
        endcase
    end

endmodule
