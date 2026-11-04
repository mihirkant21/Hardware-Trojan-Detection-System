"""
=============================================================
FastAPI Hardware Trojan Detection Engine
Powered Exclusively by XGBoost Classifier
Features:
  - Verilog 16-Bit RISC ALU Emulation
  - 37 Hardware Telemetry Signals Inspector
  - Custom Trojan / Virus Creator & Simulator
  - Autonomous Testing Bot
=============================================================
"""

import sys
import io
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import json
import random
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR = Path(r"E:\SRM Study Filess\SRM SEM-5\Computer Organization and Architecture\Project")
ML_DIR = BASE_DIR / "ml_results"
DIST_DIR = BASE_DIR / "dashboard" / "dist"

FEATURE_COLS = [
    'A_dec', 'B_dec', 'opcode', 'A_hamming', 'B_hamming', 'op_category',
    'clean_Z', 'clean_C', 'clean_V', 'clean_S',
    'flag_div_t1', 'result_div_t2', 'result_div_t3',
    'clean_toggles', 't1_toggles', 't2_toggles', 't3_toggles',
    'leakage_toggles', 'flag_toggles',
    'switch_delta_t1', 'switch_delta_t2', 'switch_delta_t3', 'leakage_norm',
    'clean_toggles_roll5', 'clean_toggles_std5',
    't3_toggles_roll5', 't3_toggles_std5',
    'leakage_toggles_roll5', 'leakage_toggles_std5',
    't1_trigger_pattern', 't2_high_activity', 't3_leakage_active',
    'risk_arithmetic', 'risk_logic', 'risk_shifter',
    'risk_flags', 'risk_sidechannel',
]

# ── Load XGBoost Model ─────────────────────────────────────────
MODEL_XGB = None
SCALER = None
LABEL_ENCODER = None

def load_xgboost_model():
    global MODEL_XGB, SCALER, LABEL_ENCODER
    try:
        model = xgb.XGBClassifier()
        model.load_model(str(ML_DIR / "model_xgb.json"))
        MODEL_XGB = model

        with open(ML_DIR / "scaler.pkl", "rb") as f:
            SCALER = pickle.load(f)
        with open(ML_DIR / "label_encoder.pkl", "rb") as f:
            LABEL_ENCODER = pickle.load(f)
        print(">> XGBoost Hardware Trojan Detector loaded successfully!")
    except Exception as e:
        print(f"Error loading XGBoost: {e}")

load_xgboost_model()

app = FastAPI(
    title="Hardware Trojan Virus Detector API",
    description="Verilog-based 16-Bit RISC ALU verification with XGBoost ML Trojan Detector",
    version="3.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPCODE_NAMES = {
    0: "ADD", 1: "SUB", 2: "MUL", 3: "DIV",
    4: "AND", 5: "OR", 6: "XOR", 7: "NOT",
    8: "NAND", 9: "NOR", 10: "XNOR",
    11: "SHL", 12: "SHR", 13: "SAR", 14: "ROL", 15: "ROR"
}

def popcount(x: int) -> int:
    return bin(x & 0xFFFF).count("1")

def hamming_dist(a: int, b: int) -> int:
    return bin((a ^ b) & 0xFFFF).count("1")

def simulate_alu_core(A: int, B: int, opcode: int):
    A = A & 0xFFFF
    B = B & 0xFFFF
    shamt = B & 0xF
    C = 0
    V = 0

    if opcode == 0:  # ADD
        full = A + B
        res = full & 0xFFFF
        C = 1 if (full > 0xFFFF) else 0
        a_s, b_s, r_s = (A >> 15) & 1, (B >> 15) & 1, (res >> 15) & 1
        V = 1 if ((a_s == b_s) and (r_s != a_s)) else 0
    elif opcode == 1:  # SUB
        full = A - B
        res = full & 0xFFFF
        C = 1 if (A < B) else 0
        a_s, b_s, r_s = (A >> 15) & 1, (B >> 15) & 1, (res >> 15) & 1
        V = 1 if ((a_s != b_s) and (r_s != a_s)) else 0
    elif opcode == 2:  # MUL
        res = (A * B) & 0xFFFF
    elif opcode == 3:  # DIV
        res = (A // B) & 0xFFFF if B != 0 else 0
    elif opcode == 4:  # AND
        res = A & B
    elif opcode == 5:  # OR
        res = A | B
    elif opcode == 6:  # XOR
        res = A ^ B
    elif opcode == 7:  # NOT
        res = (~A) & 0xFFFF
    elif opcode == 8:  # NAND
        res = (~(A & B)) & 0xFFFF
    elif opcode == 9:  # NOR
        res = (~(A | B)) & 0xFFFF
    elif opcode == 10: # XNOR
        res = (~(A ^ B)) & 0xFFFF
    elif opcode == 11: # SHL
        res = (A << shamt) & 0xFFFF
        C = (A >> (16 - shamt)) & 1 if shamt > 0 else 0
    elif opcode == 12: # SHR
        res = (A >> shamt) & 0xFFFF
        C = (A >> (shamt - 1)) & 1 if shamt > 0 else 0
    elif opcode == 13: # SAR
        sign_bit = (A >> 15) & 1
        mask = ((1 << shamt) - 1) << (16 - shamt) if sign_bit and shamt > 0 else 0
        res = ((A >> shamt) | mask) & 0xFFFF
        C = (A >> (shamt - 1)) & 1 if shamt > 0 else 0
    elif opcode == 14: # ROL
        res = ((A << shamt) | (A >> (16 - shamt))) & 0xFFFF if shamt > 0 else A
    elif opcode == 15: # ROR
        res = ((A >> shamt) | (A << (16 - shamt))) & 0xFFFF if shamt > 0 else A
    else:
        res = 0

    Z = 1 if res == 0 else 0
    S = (res >> 15) & 1
    return res, Z, C, V, S

def extract_features(A: int, B: int, opcode: int, cycle_cnt: int = 520,
                     clean_tog: Optional[int] = None, t3_tog: Optional[int] = None,
                     custom_flag_div: Optional[int] = None,
                     custom_result_div: Optional[int] = None):
    clean_res, c_Z, c_C, c_V, c_S = simulate_alu_core(A, B, opcode)

    A_ham = popcount(A)
    B_ham = popcount(B)
    op_cat = 0 if opcode < 4 else (1 if opcode < 11 else 2)

    t1_trig = (A & 0xFFFF == 0xFFFF) and (B & 0xFFFF == 0x0001) and (opcode == 1)
    flag_div_t1 = custom_flag_div if custom_flag_div is not None else (1 if t1_trig else 0)

    t2_armed = cycle_cnt >= 512
    result_div_t2 = custom_result_div if custom_result_div is not None else (1 if t2_armed else 0)
    result_div_t3 = 0

    clean_t = clean_tog if clean_tog is not None else (A_ham + B_ham) // 2
    t1_t = clean_t + (2 if (t1_trig or flag_div_t1) else 0)
    t2_t = clean_t + (1 if (t2_armed or result_div_t2) else 0)
    t3_t = t3_tog if t3_tog is not None else (clean_t + 7)

    leakage_toggles = max(0, t3_t - clean_t)
    flag_toggles = (1 if (t1_trig or flag_div_t1) else 0)
    sw_delta_t1 = t1_t - clean_t
    sw_delta_t2 = t2_t - clean_t
    sw_delta_t3 = t3_t - clean_t
    leakage_norm = leakage_toggles / 16.0

    feat = {
        'A_dec': A & 0xFFFF,
        'B_dec': B & 0xFFFF,
        'opcode': opcode,
        'A_hamming': A_ham,
        'B_hamming': B_ham,
        'op_category': op_cat,
        'clean_Z': c_Z,
        'clean_C': c_C,
        'clean_V': c_V,
        'clean_S': c_S,
        'flag_div_t1': flag_div_t1,
        'result_div_t2': result_div_t2,
        'result_div_t3': result_div_t3,
        'clean_toggles': clean_t,
        't1_toggles': t1_t,
        't2_toggles': t2_t,
        't3_toggles': t3_t,
        'leakage_toggles': leakage_toggles,
        'flag_toggles': flag_toggles,
        'switch_delta_t1': sw_delta_t1,
        'switch_delta_t2': sw_delta_t2,
        'switch_delta_t3': sw_delta_t3,
        'leakage_norm': leakage_norm,
        'clean_toggles_roll5': float(clean_t),
        'clean_toggles_std5': 1.5,
        't3_toggles_roll5': float(t3_t),
        't3_toggles_std5': 3.2,
        'leakage_toggles_roll5': float(leakage_toggles),
        'leakage_toggles_std5': 2.1,
        't1_trigger_pattern': 1 if (t1_trig or flag_div_t1) else 0,
        't2_high_activity': 1 if (cycle_cnt > 500 or result_div_t2) else 0,
        't3_leakage_active': 1 if leakage_toggles > 4 else 0,
        'risk_arithmetic': 0.8 if op_cat == 0 else 0.2,
        'risk_logic': 0.7 if op_cat == 1 else 0.1,
        'risk_shifter': 0.6 if op_cat == 2 else 0.1,
        'risk_flags': 1.0 if flag_div_t1 else 0.1,
        'risk_sidechannel': float(leakage_norm)
    }

    df = pd.DataFrame([[feat[col] for col in FEATURE_COLS]], columns=FEATURE_COLS)
    return df, feat

# ── Schemas ────────────────────────────────────────────────────
class CheckRequest(BaseModel):
    A: int
    B: int
    opcode: int
    cycle_count: Optional[int] = 1

class CustomVirusRequest(BaseModel):
    A: int
    B: int
    opcode: int
    cycle_count: Optional[int] = 1
    # Trigger Config
    trigger_type: str  # "operand_match", "cycle_threshold", "always_on"
    trigger_A: Optional[int] = 0x1234
    trigger_opcode: Optional[int] = 0
    trigger_cycles: Optional[int] = 50
    # Payload Config
    payload_type: str  # "flag_tamper", "bit_flip", "power_leak"
    flip_bit: Optional[int] = 15
    power_leak_intensity: Optional[int] = 12

class BotRequest(BaseModel):
    num_vectors: Optional[int] = 10
    include_trojan_scenarios: Optional[bool] = True

# ── API Endpoints ──────────────────────────────────────────────
@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "active_model": "XGBoost Hardware Trojan Detector",
        "test_accuracy": "45.14%",
        "features_monitored": len(FEATURE_COLS)
    }

@app.post("/api/check")
def check_circuit(req: CheckRequest):
    if MODEL_XGB is None:
        raise HTTPException(status_code=500, detail="XGBoost model is not loaded.")

    clean_res, c_Z, c_C, c_V, c_S = simulate_alu_core(req.A, req.B, req.opcode)
    df_features, feat_dict = extract_features(req.A, req.B, req.opcode, req.cycle_count)

    classes = list(LABEL_ENCODER.classes_)
    probs = MODEL_XGB.predict_proba(df_features)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = classes[pred_idx]
    is_trojan = (pred_label != 'clean')

    reasons = []
    if (req.A & 0xFFFF == 0xFFFF) and (req.B & 0xFFFF == 0x0001) and (req.opcode == 1):
        reasons.append("Flag Tamper Trigger Detected (0xFFFF SUB 0x0001)")
    if req.cycle_count >= 512:
        reasons.append("Aging Counter Threshold Exceeded (>=512 Cycles Active)")
    if is_trojan and pred_label == 'trojan3_side':
        reasons.append("High Dynamic Switching Overhead (Power Leakage)")
    if not is_trojan:
        reasons.append("Nominal Operation (Zero Inconsistencies Detected)")

    return {
        "input": {
            "A_hex": f"0x{req.A & 0xFFFF:04X}",
            "B_hex": f"0x{req.B & 0xFFFF:04X}",
            "opcode": req.opcode,
            "instruction": OPCODE_NAMES.get(req.opcode, "UNKNOWN"),
            "cycle": req.cycle_count
        },
        "verilog_alu": {
            "result_hex": f"0x{clean_res:04X}",
            "result_dec": clean_res,
            "flags": {"Z": c_Z, "C": c_C, "V": c_V, "S": c_S}
        },
        "trojan_detection": {
            "is_trojan": is_trojan,
            "verdict": "HARDWARE TROJAN DETECTED" if is_trojan else "CLEAN CIRCUIT",
            "threat_type": pred_label,
            "confidence": round(float(probs[pred_idx]), 4),
            "threat_risk_score": round(float(1.0 - probs[classes.index('clean')]), 4) if 'clean' in classes else 0.5,
            "analysis_reason": reasons[0] if reasons else "Matched threat profile"
        },
        "telemetry_37_features": feat_dict
    }

@app.post("/api/custom_virus")
def test_custom_virus(req: CustomVirusRequest):
    """
    Simulates a User-Configured Custom Hardware Trojan Virus
    and checks if XGBoost detects it using the 37 telemetry features.
    """
    if MODEL_XGB is None:
        raise HTTPException(status_code=500, detail="XGBoost model is not loaded.")

    A = req.A & 0xFFFF
    B = req.B & 0xFFFF
    clean_res, c_Z, c_C, c_V, c_S = simulate_alu_core(A, B, req.opcode)

    # 1. Evaluate User's Trigger Condition
    is_triggered = False
    if req.trigger_type == "always_on":
        is_triggered = True
    elif req.trigger_type == "operand_match":
        trig_A = req.trigger_A & 0xFFFF if req.trigger_A is not None else 0x1234
        trig_op = req.trigger_opcode if req.trigger_opcode is not None else req.opcode
        is_triggered = (A == trig_A) and (req.opcode == trig_op)
    elif req.trigger_type == "cycle_threshold":
        th = req.trigger_cycles if req.trigger_cycles is not None else 50
        is_triggered = req.cycle_count >= th

    # 2. Apply Custom Malicious Payload if triggered
    mod_res = clean_res
    custom_flag_div = 0
    custom_result_div = 0
    custom_t3_toggles = None
    impact_desc = "Dormant (Trigger condition not met)"

    if is_triggered:
        if req.payload_type == "flag_tamper":
            custom_flag_div = 1
            c_Z = 1 - c_Z
            c_V = 1 - c_V
            impact_desc = "Inverted Zero (Z) and Overflow (V) status flags"
        elif req.payload_type == "bit_flip":
            bit = max(0, min(15, req.flip_bit or 15))
            mod_res = clean_res ^ (1 << bit)
            custom_result_div = 1
            impact_desc = f"Corrupted output bit #{bit} (0x{clean_res:04X} -> 0x{mod_res:04X})"
        elif req.payload_type == "power_leak":
            intensity = req.power_leak_intensity or 12
            clean_tog = (popcount(A) + popcount(B)) // 2
            custom_t3_toggles = clean_tog + intensity
            impact_desc = f"Injected +{intensity} phantom switching gate toggles (Power Leak)"

    # 3. Extract 37 Telemetry Features under the modified hardware state
    df_feat, feat_dict = extract_features(
        A, B, req.opcode, req.cycle_count,
        t3_tog=custom_t3_toggles,
        custom_flag_div=custom_flag_div,
        custom_result_div=custom_result_div
    )

    # 4. XGBoost AI Inspection
    classes = list(LABEL_ENCODER.classes_)
    probs = MODEL_XGB.predict_proba(df_feat)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = classes[pred_idx]
    is_detected = (pred_label != 'clean')

    return {
        "virus_configuration": {
            "trigger_type": req.trigger_type,
            "payload_type": req.payload_type,
            "was_triggered": is_triggered,
            "hardware_impact": impact_desc
        },
        "verilog_alu": {
            "clean_result_hex": f"0x{clean_res:04X}",
            "actual_result_hex": f"0x{mod_res:04X}",
            "flags": {"Z": c_Z, "C": c_C, "V": c_V, "S": c_S}
        },
        "ml_defense_verdict": {
            "detected": is_detected,
            "verdict": "🚨 CUSTOM VIRUS INTERCEPTED BY AI" if is_detected else "⚠️ VIRUS EVADED AI (CLEAN VERDICT)",
            "threat_category": pred_label,
            "confidence": round(float(probs[pred_idx]), 4),
            "threat_risk_score": round(float(1.0 - probs[classes.index('clean')]), 4) if 'clean' in classes else 0.5
        },
        "telemetry_37_features": feat_dict
    }

@app.post("/api/bot/auto_test")
def run_auto_test_bot(req: BotRequest):
    if MODEL_XGB is None:
        raise HTTPException(status_code=500, detail="XGBoost model is not loaded.")

    classes = list(LABEL_ENCODER.classes_)
    results = []
    trojan_count = 0
    clean_count = 0

    for i in range(req.num_vectors):
        inject_trojan = req.include_trojan_scenarios and (i % 3 == 0)

        if inject_trojan:
            trojan_type = random.choice([1, 2, 3])
            if trojan_type == 1:
                A, B, op, cycle = 0xFFFF, 0x0001, 1, random.randint(10, 200)
            elif trojan_type == 2:
                A, B, op, cycle = random.randint(0, 0xFFFF), random.randint(0, 0xFFFF), random.randint(0, 15), random.randint(520, 700)
            else:
                A, B, op, cycle = random.randint(0x8000, 0xFFFF), random.randint(0x8000, 0xFFFF), 6, random.randint(10, 300)
        else:
            A, B, op, cycle = random.randint(0, 0xFFFF), random.randint(0, 0xFFFF), random.randint(0, 15), random.randint(1, 400)

        clean_res, c_Z, c_C, c_V, c_S = simulate_alu_core(A, B, op)
        df_feat, _ = extract_features(A, B, op, cycle)
        probs = MODEL_XGB.predict_proba(df_feat)[0]
        pred_idx = int(np.argmax(probs))
        pred_label = classes[pred_idx]
        is_troj = (pred_label != 'clean')

        if is_troj:
            trojan_count += 1
        else:
            clean_count += 1

        results.append({
            "step": i + 1,
            "A_hex": f"0x{A:04X}",
            "B_hex": f"0x{B:04X}",
            "opcode_name": OPCODE_NAMES.get(op, "OP"),
            "cycle": cycle,
            "result_hex": f"0x{clean_res:04X}",
            "prediction": pred_label,
            "is_trojan": is_troj,
            "confidence": round(float(probs[pred_idx]), 4)
        })

    return {
        "total_scanned": req.num_vectors,
        "clean_passed": clean_count,
        "trojans_detected": trojan_count,
        "test_logs": results
    }

if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend_api:app", host="127.0.0.1", port=8000, reload=False)
