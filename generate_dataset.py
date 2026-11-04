"""
=============================================================
Phase 6: Automated Dataset Generator
Project: AI-Based Hardware Trojan Detection System
=============================================================
Generates 10,500 labeled simulation cycles:
  - 7,000 randomized instructions across all 16 operations
  - 2,500 targeted corner-case / Trojan-trigger stimuli
  - 1,000 sequential burst (to trigger Trojan 2 at op 512)

Runs iverilog simulation, parses raw_sim_output.csv,
engineers features, and saves alu_trojan_dataset.csv
=============================================================
"""

import subprocess
import random
import os
import csv
import pandas as pd
import numpy as np
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────
IVERILOG_PATH = r"C:\iverilog\bin\iverilog.exe"
VVP_PATH      = r"C:\iverilog\bin\vvp.exe"
SIM_DIR       = Path(r"E:\SRM Study Filess\SRM SEM-5\Computer Organization and Architecture\Project\alu_16bit")
OUT_DIR       = Path(r"E:\SRM Study Filess\SRM SEM-5\Computer Organization and Architecture\Project")

NUM_CYCLES    = 10500
RANDOM_SEED   = 42

# Opcode map
OPCODES = {
    0x0: "ADD",  0x1: "SUB",  0x2: "MUL",  0x3: "DIV",
    0x4: "AND",  0x5: "OR",   0x6: "XOR",  0x7: "NOT",
    0x8: "NAND", 0x9: "NOR",  0xA: "XNOR", 0xB: "SHL",
    0xC: "SHR",  0xD: "SAR",  0xE: "ROL",  0xF: "ROR",
}

# Label map: 0=clean, 1=T1_flag_tamper, 2=T2_counter, 3=T3_sidechannel
LABELS = {0: "clean", 1: "trojan1_flag", 2: "trojan2_counter", 3: "trojan3_side"}

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ── Step 1: Generate Stimulus ─────────────────────────────────
def generate_stimulus():
    """
    Build 10,500 stimulus vectors with labels.
    Returns lists: A_list, B_list, op_list, label_list
    """
    A_list, B_list, op_list, label_list = [], [], [], []

    print("[GEN] Generating stimulus vectors...")

    # ── 7000 Random instructions (balanced label distribution) ──
    for i in range(7000):
        A  = random.randint(0, 0xFFFF)
        B  = random.randint(0, 0xFFFF)
        op = random.randint(0, 15)
        # Assign label based on which variant this cycle belongs to
        label = i % 4  # Round-robin: 0,1,2,3,0,1,2,3...
        A_list.append(A); B_list.append(B)
        op_list.append(op); label_list.append(label)

    # ── 1500 Trojan 1 targeted stimuli ──────────────────────────
    # Mix of trigger and near-miss inputs
    for i in range(1500):
        if i < 500:
            # Exact trigger: A=0xFFFF, B=0x0001, SUB
            A, B, op = 0xFFFF, 0x0001, 0x1
            label = 1
        elif i < 1000:
            # Near-miss: A=0xFFFF but wrong opcode
            A = 0xFFFF
            B = random.randint(0, 0xFFFF)
            op = random.choice([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
            label = 0
        else:
            # Near-miss: correct opcode but wrong A
            A = random.randint(0, 0xFFFE)
            B = 0x0001
            op = 0x1
            label = 0
        A_list.append(A); B_list.append(B)
        op_list.append(op); label_list.append(label)

    # ── 1000 Sequential burst to arm Trojan 2 ──────────────────
    # First 511: clean label, then 489: Trojan 2 label
    for i in range(1000):
        A  = random.randint(0, 0x7FFF)
        B  = random.randint(0, 0x7FFF)
        op = random.choice([0, 1, 4, 5])
        label = 2 if i >= 511 else 0
        A_list.append(A); B_list.append(B)
        op_list.append(op); label_list.append(label)

    # ── Corner cases for edge coverage ──────────────────────────
    corners = [
        (0x0000, 0x0000, 0x0, 0), (0xFFFF, 0xFFFF, 0x0, 0),
        (0x7FFF, 0x0001, 0x0, 0), (0x8000, 0x0001, 0x1, 0),
        (0x0001, 0x0001, 0x2, 0), (0x000A, 0x0003, 0x3, 0),
        (0xFFFF, 0x0000, 0x3, 0), (0x1234, 0xABCD, 0x4, 0),
        (0xFF00, 0x0008, 0xB, 0), (0x8000, 0x0001, 0xD, 0),
        (0xF000, 0x0004, 0xE, 0), (0x000F, 0x0004, 0xF, 0),
    ]
    # Repeat corners to fill remaining slots
    needed = NUM_CYCLES - len(A_list)
    for i in range(needed):
        A, B, op, label = corners[i % len(corners)]
        A_list.append(A); B_list.append(B)
        op_list.append(op); label_list.append(label)

    print(f"[GEN] Generated {len(A_list)} stimulus vectors")
    return A_list[:NUM_CYCLES], B_list[:NUM_CYCLES], op_list[:NUM_CYCLES], label_list[:NUM_CYCLES]


# ── Step 2: Write hex stimulus files for Verilog $readmemh ────
def write_hex_files(A_list, B_list, op_list, label_list):
    print("[HEX] Writing stimulus hex files...")

    def write_hex(path, values, width=4):
        with open(path, 'w') as f:
            for v in values:
                f.write(f"{v:0{width}x}\n")

    write_hex(SIM_DIR / "stim_A.hex",     A_list,     width=4)
    write_hex(SIM_DIR / "stim_B.hex",     B_list,     width=4)
    write_hex(SIM_DIR / "stim_op.hex",    op_list,    width=1)
    write_hex(SIM_DIR / "stim_label.hex", label_list, width=1)
    print("[HEX] Hex files written.")


# ── Step 3: Compile and run Verilog simulation ────────────────
def run_simulation():
    print("[SIM] Compiling Verilog harness...")

    src_files = [
        "alu_dataset_harness.v",
        "alu_16bit.v", "alu_arithmetic.v", "alu_logic.v",
        "alu_shifter.v", "alu_flags.v",
        "trojan1_flag_tamper.v",
        "trojan2_counter_payload.v",
        "trojan3_sidechannel.v",
    ]
    src_paths = [str(SIM_DIR / f) for f in src_files]
    out_vvp   = str(SIM_DIR / "dataset_sim.vvp")

    compile_cmd = [IVERILOG_PATH, "-o", out_vvp] + src_paths
    result = subprocess.run(compile_cmd, capture_output=True, text=True, cwd=str(SIM_DIR))

    if result.returncode != 0:
        print(f"[ERROR] Compilation failed:\n{result.stderr}")
        raise RuntimeError("iverilog compile failed")
    print("[SIM] Compilation successful. Running simulation...")

    sim_result = subprocess.run(
        [VVP_PATH, out_vvp],
        capture_output=True, text=True, cwd=str(SIM_DIR)
    )
    print(sim_result.stdout)
    if sim_result.returncode != 0:
        print(f"[ERROR] Simulation failed:\n{sim_result.stderr}")
        raise RuntimeError("vvp simulation failed")
    print("[SIM] Simulation complete.")


# ── Step 4: Parse raw CSV and engineer features ───────────────
def engineer_features(A_list, B_list, op_list, label_list):
    print("[CSV] Parsing simulation output and engineering features...")

    raw_csv = SIM_DIR / "raw_sim_output.csv"
    df = pd.read_csv(raw_csv)

    # ── Parse hex columns written by Verilog $fwrite ──────────
    for col in ['A', 'B', 'clean_result', 't1_result', 't2_result', 't3_result']:
        df[col] = df[col].apply(lambda x: int(str(x).strip(), 16))
    for col in ['opcode', 't3_leakage']:
        df[col] = df[col].apply(lambda x: int(str(x).strip(), 16))
    # ── Computed features from operands ─────────────────────
    df['A_dec']        = df['A']
    df['B_dec']        = df['B']
    df['A_hamming']    = df['A_dec'].apply(lambda x: bin(x).count('1'))
    df['B_hamming']    = df['B_dec'].apply(lambda x: bin(x).count('1'))
    df['op_category']  = df['opcode'].apply(lambda x:
        0 if x <= 3 else (1 if x <= 10 else 2))  # 0=arith,1=logic,2=shift

    # ── Flag divergence features ─────────────────────────────
    # Detect where clean vs trojan flags differ
    df['flag_div_t1']  = ((df['clean_Z'] != df['t1_Z']) |
                          (df['clean_V'] != df['t1_V'])).astype(int)
    df['result_div_t2']= (df['clean_result'] != df['t2_result']).astype(int)
    df['result_div_t3']= (df['clean_result'] != df['t3_result']).astype(int)

    # ── Switching activity delta (anomaly signal) ─────────────
    df['switch_delta_t1'] = (df['t1_toggles']  - df['clean_toggles']).abs()
    df['switch_delta_t2'] = (df['t2_toggles']  - df['clean_toggles']).abs()
    df['switch_delta_t3'] = (df['t3_toggles']  - df['clean_toggles']).abs()
    df['leakage_norm']    = df['leakage_toggles'] / 8.0  # Normalize to [0,1]

    # ── Rolling window features (sliding window of 5 cycles) ──
    for col in ['clean_toggles', 't1_toggles', 't2_toggles',
                't3_toggles', 'leakage_toggles', 'flag_toggles']:
        df[f'{col}_roll5'] = df[col].rolling(5, min_periods=1).mean()
        df[f'{col}_std5']  = df[col].rolling(5, min_periods=1).std().fillna(0)

    # ── Trojan-specific risk indicators ──────────────────────
    df['t1_trigger_pattern'] = (
        (df['A_dec'] == 0xFFFF) &
        (df['B_dec'] == 0x0001) &
        (df['opcode'] == 1)
    ).astype(int)

    df['t2_high_activity'] = (df['t2_toggles'] > df['clean_toggles'] * 1.5).astype(int)
    df['t3_leakage_active'] = (df['leakage_toggles'] > 0).astype(int)

    # ── Sub-module risk index (Localization — Phase 9 preview) ─
    # Arithmetic sub-block risk
    df['risk_arithmetic'] = np.where(df['opcode'] <= 3,
        df['switch_delta_t2'] + df['flag_div_t1'], 0)
    # Logic sub-block risk
    df['risk_logic'] = np.where((df['opcode'] >= 4) & (df['opcode'] <= 10),
        df['switch_delta_t1'], 0)
    # Shifter sub-block risk
    df['risk_shifter'] = np.where(df['opcode'] >= 11,
        df['switch_delta_t2'], 0)
    # Flags sub-block risk
    df['risk_flags'] = df['flag_div_t1'] * 2 + df['flag_toggles']
    # Side-channel sub-block risk
    df['risk_sidechannel'] = df['leakage_norm'] * 10 + df['t3_leakage_active']

    # ── Final label column ────────────────────────────────────
    label_map = {0: "clean", 1: "trojan1_flag",
                 2: "trojan2_counter", 3: "trojan3_side"}
    df['trojan_label']    = df['label'].map(label_map)
    df['trojan_binary']   = (df['label'] > 0).astype(int)  # 0=clean, 1=any trojan

    print(f"[CSV] Feature engineering complete. Shape: {df.shape}")
    return df


# ── Step 5: Save final dataset ────────────────────────────────
def save_dataset(df):
    # Select final feature columns for ML training
    feature_cols = [
        # Raw features
        'A_dec', 'B_dec', 'opcode', 'A_hamming', 'B_hamming', 'op_category',
        # Flag signals
        'clean_Z', 'clean_C', 'clean_V', 'clean_S',
        'flag_div_t1', 'result_div_t2', 'result_div_t3',
        # Switching activity
        'clean_toggles', 't1_toggles', 't2_toggles', 't3_toggles',
        'leakage_toggles', 'flag_toggles',
        # Delta features
        'switch_delta_t1', 'switch_delta_t2', 'switch_delta_t3', 'leakage_norm',
        # Rolling window
        'clean_toggles_roll5', 'clean_toggles_std5',
        't3_toggles_roll5', 't3_toggles_std5',
        'leakage_toggles_roll5', 'leakage_toggles_std5',
        # Risk indicators
        't1_trigger_pattern', 't2_high_activity', 't3_leakage_active',
        # Sub-module risk (Phase 9)
        'risk_arithmetic', 'risk_logic', 'risk_shifter',
        'risk_flags', 'risk_sidechannel',
        # Labels
        'trojan_label', 'trojan_binary',
    ]

    out_path = OUT_DIR / "alu_trojan_dataset.csv"
    df[feature_cols].to_csv(out_path, index=False)

    print(f"\n{'='*55}")
    print(f"  DATASET SAVED: {out_path}")
    print(f"{'='*55}")
    print(f"  Total samples  : {len(df)}")
    print(f"  Features       : {len(feature_cols) - 2}")
    print(f"  Label dist     :")
    print(df['trojan_label'].value_counts().to_string(header=False))
    print(f"  Binary dist    : clean={df['trojan_binary'].value_counts()[0]}  "
          f"trojan={df['trojan_binary'].value_counts()[1]}")
    print(f"{'='*55}")


# ── Main Pipeline ─────────────────────────────────────────────
if __name__ == "__main__":
    print("="*55)
    print("  Phase 6: Hardware Trojan Dataset Generator")
    print("="*55)

    # Step 1: Generate stimulus
    A_list, B_list, op_list, label_list = generate_stimulus()

    # Step 2: Write hex files
    write_hex_files(A_list, B_list, op_list, label_list)

    # Step 3: Run simulation
    run_simulation()

    # Step 4: Engineer features
    df = engineer_features(A_list, B_list, op_list, label_list)

    # Step 5: Save
    save_dataset(df)

    print("\n[DONE] Phase 6 complete. Ready for ML training (Phase 7).")
