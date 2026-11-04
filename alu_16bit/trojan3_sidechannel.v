// ============================================================
// Module: trojan3_sidechannel (Side-Channel Leakage Trojan)
// Description: Wraps clean alu_16bit. Does NOT alter the
//              output result or any flags — completely
//              functionally transparent.
//              Instead, modulates 8 dummy flip-flop registers
//              based on XOR of A, B and internal result bits,
//              creating abnormal switching activity that leaks
//              information through the power side-channel.
//              Mimics the AES-T100 CDMA leakage mechanism
//              but applied to the ALU domain.
// Detection: Only visible via switching activity analysis,
//            not via functional testing.
// ============================================================
`timescale 1ns / 1ps

module trojan3_sidechannel (
    input  wire        clk,
    input  wire        rst,
    input  wire [15:0] A,
    input  wire [15:0] B,
    input  wire [3:0]  opcode,
    output wire [15:0] result,
    output wire        Z,
    output wire        C,
    output wire        V,
    output wire        S,
    // Exposed for simulation/dataset extraction only:
    output wire [7:0]  leakage_activity
);

    // ── Internal wires from clean ALU ────────────────────────
    wire [15:0] clean_result;

    // ── Instantiate clean golden ALU (pass-through) ──────────
    alu_16bit CLEAN_ALU (
        .A      (A),
        .B      (B),
        .opcode (opcode),
        .result (clean_result),
        .Z      (Z),
        .C      (C),
        .V      (V),
        .S      (S)
    );

    // Result passes through unmodified
    assign result = clean_result;

    // ── Trojan: 8 dummy flip-flops (side-channel carrier) ────
    // Each FF toggles based on XOR of operand bits and result
    // bits — this creates power spikes correlated to secret data
    reg [7:0] dummy_ff;

    // Internal LFSR for pseudo-randomness (mimics AES-T100 PRNG)
    reg [7:0] lfsr;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            dummy_ff <= 8'h00;
            lfsr     <= 8'hAC; // Non-zero seed
        end else begin
            // Advance LFSR (x^8 + x^6 + x^5 + x^4 + 1)
            lfsr <= {lfsr[6:0], lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3]};

            // Each dummy FF = (secret operand bit) XOR (LFSR bit)
            // This spreads the leakage over many cycles (CDMA-like)
            dummy_ff[0] <= A[0]  ^ lfsr[0];
            dummy_ff[1] <= A[4]  ^ lfsr[1];
            dummy_ff[2] <= A[8]  ^ lfsr[2];
            dummy_ff[3] <= A[12] ^ lfsr[3];
            dummy_ff[4] <= B[0]  ^ lfsr[4];
            dummy_ff[5] <= B[4]  ^ lfsr[5];
            dummy_ff[6] <= clean_result[0] ^ lfsr[6];
            dummy_ff[7] <= clean_result[8] ^ lfsr[7];
        end
    end

    // Expose dummy activity for VCD/switching analysis
    assign leakage_activity = dummy_ff;

endmodule
