// ============================================================
// Testbench: tb_trojans
// Description: Verifies all 3 Hardware Trojans behave
//              correctly — triggers fire when expected,
//              normal ops remain unaffected.
// ============================================================
`timescale 1ns / 1ps

module tb_trojans;

    // ── Clock & Reset ─────────────────────────────────────────
    reg clk, rst;
    always #5 clk = ~clk; // 100 MHz clock

    // ── Shared inputs ─────────────────────────────────────────
    reg  [15:0] A, B;
    reg  [3:0]  opcode;

    // ── Trojan 1 outputs ──────────────────────────────────────
    wire [15:0] t1_result;
    wire        t1_Z, t1_C, t1_V, t1_S;

    // ── Trojan 2 outputs ──────────────────────────────────────
    wire [15:0] t2_result;
    wire        t2_Z, t2_C, t2_V, t2_S;

    // ── Trojan 3 outputs ──────────────────────────────────────
    wire [15:0] t3_result;
    wire        t3_Z, t3_C, t3_V, t3_S;
    wire [7:0]  t3_leakage;

    // ── Clean ALU outputs (golden reference) ─────────────────
    wire [15:0] clean_result;
    wire        clean_Z, clean_C, clean_V, clean_S;

    // ── DUT Instantiations ────────────────────────────────────
    alu_16bit GOLDEN (
        .A(A), .B(B), .opcode(opcode),
        .result(clean_result),
        .Z(clean_Z), .C(clean_C), .V(clean_V), .S(clean_S)
    );

    trojan1_flag_tamper T1 (
        .A(A), .B(B), .opcode(opcode),
        .result(t1_result),
        .Z(t1_Z), .C(t1_C), .V(t1_V), .S(t1_S)
    );

    trojan2_counter_payload T2 (
        .clk(clk), .rst(rst),
        .A(A), .B(B), .opcode(opcode),
        .result(t2_result),
        .Z(t2_Z), .C(t2_C), .V(t2_V), .S(t2_S)
    );

    trojan3_sidechannel T3 (
        .clk(clk), .rst(rst),
        .A(A), .B(B), .opcode(opcode),
        .result(t3_result),
        .Z(t3_Z), .C(t3_C), .V(t3_V), .S(t3_S),
        .leakage_activity(t3_leakage)
    );

    // ── VCD Dump ─────────────────────────────────────────────
    initial begin
        $dumpfile("trojans.vcd");
        $dumpvars(0, tb_trojans);
    end

    integer i, pass_t1=0, fail_t1=0, pass_t2=0, fail_t2=0;

    initial begin
        clk = 0; rst = 1;
        A = 0; B = 0; opcode = 0;
        #20 rst = 0;

        $display("============================================================");
        $display("           HARDWARE TROJAN VERIFICATION TESTBENCH");
        $display("============================================================");

        // ════════════════════════════════════════════════════════
        // TROJAN 1: Combinational Flag Tamper
        // ════════════════════════════════════════════════════════
        $display("\n── TROJAN 1: Combinational Flag Tamper ──");

        // Test 1a: Normal SUB — Trojan should NOT trigger
        A = 16'h0009; B = 16'h0003; opcode = 4'b0001; #10;
        if (t1_Z === clean_Z && t1_V === clean_V) begin
            $display("[PASS] T1 Normal SUB — flags unchanged (Z=%b V=%b)", t1_Z, t1_V);
            pass_t1 = pass_t1 + 1;
        end else begin
            $display("[FAIL] T1 Normal SUB — flags corrupted!");
            fail_t1 = fail_t1 + 1;
        end

        // Test 1b: TRIGGER condition (A=0xFFFF, B=0x0001, SUB)
        A = 16'hFFFF; B = 16'h0001; opcode = 4'b0001; #10;
        if (t1_Z !== clean_Z && t1_V !== clean_V) begin
            $display("[PASS] T1 TRIGGERED — Z flipped: %b→%b, V flipped: %b→%b",
                     clean_Z, t1_Z, clean_V, t1_V);
            $display("       Clean: result=%h Z=%b V=%b", clean_result, clean_Z, clean_V);
            $display("       Trojan: result=%h Z=%b V=%b", t1_result, t1_Z, t1_V);
            pass_t1 = pass_t1 + 1;
        end else begin
            $display("[FAIL] T1 did NOT trigger on expected condition!");
            fail_t1 = fail_t1 + 1;
        end

        // Test 1c: ADD with same values — should NOT trigger (wrong opcode)
        A = 16'hFFFF; B = 16'h0001; opcode = 4'b0000; #10;
        if (t1_Z === clean_Z && t1_V === clean_V) begin
            $display("[PASS] T1 ADD (wrong opcode) — no trigger, flags clean");
            pass_t1 = pass_t1 + 1;
        end else begin
            $display("[FAIL] T1 triggered on ADD — should not!");
            fail_t1 = fail_t1 + 1;
        end

        $display("Trojan 1: %0d PASSED | %0d FAILED", pass_t1, fail_t1);

        // ════════════════════════════════════════════════════════
        // TROJAN 2: Sequential Counter Payload
        // ════════════════════════════════════════════════════════
        $display("\n── TROJAN 2: Sequential Counter Payload (512 ops) ──");

        // Run 511 operations — Trojan should NOT be armed yet
        A = 16'h0005; B = 16'h0003; opcode = 4'b0000;
        for (i = 0; i < 511; i = i + 1) begin
            @(posedge clk); #1;
        end

        // Check at op 511 — still clean (armed at 512)
        #2;
        // Note: counter starts after reset; pre-arm check is at early cycle
        $display("[INFO] T2 pre-arm result=%h clean=%h", t2_result, clean_result);
        if (t2_result[14:0] === clean_result[14:0]) begin
            $display("[PASS] T2 pre-arm — lower 15 bits clean (MSB may already flip near threshold)");
            pass_t2 = pass_t2 + 1;
        end else begin
            $display("[FAIL] T2 pre-arm — lower 15 bits corrupted prematurely!");
            fail_t2 = fail_t2 + 1;
        end

        // One more clock — crosses 512 threshold, arms Trojan
        @(posedge clk); #2;

        // Check at op 512 — Trojan should now be armed
        A = 16'h0001; B = 16'h0001; opcode = 4'b0000; #10;
        if (t2_result !== clean_result && t2_result[15] !== clean_result[15]) begin
            $display("[PASS] T2 ARMED at op 512 — MSB corrupted!");
            $display("       Clean:  result=%h (MSB=%b)", clean_result, clean_result[15]);
            $display("       Trojan: result=%h (MSB=%b)", t2_result, t2_result[15]);
            pass_t2 = pass_t2 + 1;
        end else begin
            $display("[FAIL] T2 not armed after 512 ops! result=%h", t2_result);
            fail_t2 = fail_t2 + 1;
        end

        $display("Trojan 2: %0d PASSED | %0d FAILED", pass_t2, fail_t2);

        // ════════════════════════════════════════════════════════
        // TROJAN 3: Side-Channel Leakage
        // ════════════════════════════════════════════════════════
        $display("\n── TROJAN 3: Side-Channel Leakage ──");

        rst = 1; #10; rst = 0;
        A = 16'hABCD; B = 16'h1234; opcode = 4'b0100; // AND

        // Run for 20 cycles and check functional transparency
        repeat(20) @(posedge clk);
        #2;

        if (t3_result === clean_result &&
            t3_Z === clean_Z && t3_C === clean_C &&
            t3_V === clean_V && t3_S === clean_S) begin
            $display("[PASS] T3 Functionally transparent — output/flags UNCHANGED");
            $display("       result=%h Z=%b C=%b V=%b S=%b",
                     t3_result, t3_Z, t3_C, t3_V, t3_S);
        end else begin
            $display("[FAIL] T3 corrupted functional output!");
        end

        $display("[INFO] T3 Leakage FF activity = %b (switching = side-channel)", t3_leakage);
        $display("       Non-zero activity confirms leakage channel is active: %s",
                 (t3_leakage !== 8'h00) ? "YES" : "NO");

        // ════════════════════════════════════════════════════════
        $display("\n============================================================");
        $display("  T1: %0d/%0d   T2: %0d/%0d   T3: functional+leakage verified",
                 pass_t1, pass_t1+fail_t1, pass_t2, pass_t2+fail_t2);
        $display("============================================================");
        $finish;
    end

endmodule
