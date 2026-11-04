// ============================================================
// Testbench: tb_alu_16bit
// Description: Self-checking testbench with assertions for
//              all 16 ALU operations. Dumps VCD for Phase 4.
// ============================================================
`timescale 1ns / 1ps

module tb_alu_16bit;

    // ── DUT Signals ──────────────────────────────────────────
    reg  [15:0] A, B;
    reg  [3:0]  opcode;
    wire [15:0] result;
    wire        Z, C, V, S;

    // ── Error Counter ────────────────────────────────────────
    integer pass_count = 0;
    integer fail_count = 0;

    // ── DUT Instantiation ────────────────────────────────────
    alu_16bit DUT (
        .A      (A),
        .B      (B),
        .opcode (opcode),
        .result (result),
        .Z      (Z),
        .C      (C),
        .V      (V),
        .S      (S)
    );

    // ── VCD Dump for GTKWave ─────────────────────────────────
    initial begin
        $dumpfile("alu_16bit.vcd");
        $dumpvars(0, tb_alu_16bit);
    end

    // ── Task: Assert & Report ────────────────────────────────
    task check;
        input [15:0] exp_result;
        input        exp_Z, exp_C, exp_V, exp_S;
        input [63:0] test_id; // Test number
        input [8*20:1] op_name;
        begin
            #5; // Wait for combinational settle
            if (result === exp_result && Z === exp_Z &&
                C === exp_C && V === exp_V && S === exp_S) begin
                $display("[PASS] Test %0d %-6s | A=%h B=%h | result=%h Z=%b C=%b V=%b S=%b",
                         test_id, op_name, A, B, result, Z, C, V, S);
                pass_count = pass_count + 1;
            end else begin
                $display("[FAIL] Test %0d %-6s | A=%h B=%h", test_id, op_name, A, B);
                $display("       Expected: result=%h Z=%b C=%b V=%b S=%b",
                         exp_result, exp_Z, exp_C, exp_V, exp_S);
                $display("       Got:      result=%h Z=%b C=%b V=%b S=%b",
                         result, Z, C, V, S);
                fail_count = fail_count + 1;
            end
        end
    endtask

    // ── Test Vectors ─────────────────────────────────────────
    initial begin
        $display("========================================");
        $display("  16-bit ALU Self-Checking Testbench");
        $display("========================================");

        // ── ADD (opcode = 0000) ──────────────────────────────
        // Test 1: Normal add
        A=16'h0003; B=16'h0004; opcode=4'b0000;
        check(16'h0007, 0,0,0,0, 1, "ADD");

        // Test 2: Add with carry-out
        A=16'hFFFF; B=16'h0001; opcode=4'b0000;
        check(16'h0000, 1,1,0,0, 2, "ADD");

        // Test 3: Signed overflow (pos + pos = neg)
        A=16'h7FFF; B=16'h0001; opcode=4'b0000;
        check(16'h8000, 0,0,1,1, 3, "ADD_OV");

        // Test 4: Add zeros
        A=16'h0000; B=16'h0000; opcode=4'b0000;
        check(16'h0000, 1,0,0,0, 4, "ADD");

        // ── SUB (opcode = 0001) ──────────────────────────────
        // Test 5: Normal subtract
        A=16'h0009; B=16'h0003; opcode=4'b0001;
        check(16'h0006, 0,1,0,0, 5, "SUB");

        // Test 6: Result = 0
        A=16'h1234; B=16'h1234; opcode=4'b0001;
        check(16'h0000, 1,1,0,0, 6, "SUB");

        // Test 7: Signed overflow (neg - pos = pos)
        A=16'h8000; B=16'h0001; opcode=4'b0001;
        check(16'h7FFF, 0,1,1,0, 7, "SUB_OV");

        // Test 8: Trojan trigger condition (A=0xFFFF, B=0x0001, SUB)
        A=16'hFFFF; B=16'h0001; opcode=4'b0001;
        check(16'hFFFE, 0,1,0,1, 8, "SUB_TJ");

        // ── MUL (opcode = 0010) ──────────────────────────────
        // Test 9: Normal multiply
        A=16'h0005; B=16'h0003; opcode=4'b0010;
        check(16'h000F, 0,0,0,0, 9, "MUL");

        // Test 10: Multiply by zero
        A=16'hFFFF; B=16'h0000; opcode=4'b0010;
        check(16'h0000, 1,0,0,0, 10, "MUL");

        // ── DIV (opcode = 0011) ──────────────────────────────
        // Test 11: Normal divide
        A=16'h000C; B=16'h0004; opcode=4'b0011;
        check(16'h0003, 0,0,0,0, 11, "DIV");

        // Test 12: Divide by zero -> saturate to 0xFFFF
        A=16'h1234; B=16'h0000; opcode=4'b0011;
        check(16'hFFFF, 0,1,0,1, 12, "DIV/0");

        // ── AND (opcode = 0100) ──────────────────────────────
        // Test 13
        A=16'hFF0F; B=16'h0FF0; opcode=4'b0100;
        check(16'h0F00, 0,0,0,0, 13, "AND");

        // Test 14: AND with self = self
        A=16'hABCD; B=16'hABCD; opcode=4'b0100;
        check(16'hABCD, 0,0,0,1, 14, "AND");

        // ── OR (opcode = 0101) ───────────────────────────────
        // Test 15
        A=16'hAA00; B=16'h00BB; opcode=4'b0101;
        check(16'hAABB, 0,0,0,1, 15, "OR");

        // ── XOR (opcode = 0110) ──────────────────────────────
        // Test 16: XOR with self = 0
        A=16'hDEAD; B=16'hDEAD; opcode=4'b0110;
        check(16'h0000, 1,0,0,0, 16, "XOR");

        // ── NOT (opcode = 0111) ──────────────────────────────
        // Test 17
        A=16'h0000; B=16'hXXXX; opcode=4'b0111;
        check(16'hFFFF, 0,0,0,1, 17, "NOT");

        // Test 18
        A=16'hFFFF; B=16'h0000; opcode=4'b0111;
        check(16'h0000, 1,0,0,0, 18, "NOT");

        // ── NAND (opcode = 1000) ─────────────────────────────
        // Test 19
        A=16'hFFFF; B=16'hFFFF; opcode=4'b1000;
        check(16'h0000, 1,0,0,0, 19, "NAND");

        // ── NOR (opcode = 1001) ──────────────────────────────
        // Test 20
        A=16'h0000; B=16'h0000; opcode=4'b1001;
        check(16'hFFFF, 0,0,0,1, 20, "NOR");

        // ── XNOR (opcode = 1010) ─────────────────────────────
        // Test 21: XNOR with self = all 1s
        A=16'hBEEF; B=16'hBEEF; opcode=4'b1010;
        check(16'hFFFF, 0,0,0,1, 21, "XNOR");

        // ── SHL (opcode = 1011) ──────────────────────────────
        // Test 22: Shift left by 4
        A=16'h000F; B=16'h0004; opcode=4'b1011;
        check(16'h00F0, 0,0,0,0, 22, "SHL");

        // Test 23: Shift left by 8
        A=16'h00FF; B=16'h0008; opcode=4'b1011;
        check(16'hFF00, 0,0,0,1, 23, "SHL");

        // ── SHR (opcode = 1100) ──────────────────────────────
        // Test 24: Logical shift right
        A=16'hFF00; B=16'h0008; opcode=4'b1100;
        check(16'h00FF, 0,0,0,0, 24, "SHR");

        // ── SAR (opcode = 1101) ──────────────────────────────
        // Test 25: Arithmetic right shift (negative number)
        A=16'h8000; B=16'h0001; opcode=4'b1101;
        check(16'hC000, 0,0,0,1, 25, "SAR");

        // ── ROL (opcode = 1110) ──────────────────────────────
        // Test 26: Rotate left by 4
        A=16'hF000; B=16'h0004; opcode=4'b1110;
        check(16'h000F, 0,0,0,0, 26, "ROL");

        // ── ROR (opcode = 1111) ──────────────────────────────
        // Test 27: Rotate right by 4
        A=16'h000F; B=16'h0004; opcode=4'b1111;
        check(16'hF000, 0,0,0,1, 27, "ROR");

        // ── Summary ──────────────────────────────────────────
        #10;
        $display("========================================");
        $display("  RESULTS: %0d PASSED | %0d FAILED", pass_count, fail_count);
        $display("========================================");
        if (fail_count == 0)
            $display("  ✓ ALL TESTS PASSED — ALU is CLEAN");
        else
            $display("  ✗ FAILURES DETECTED — Review above");
        $display("========================================");
        $finish;
    end

endmodule
