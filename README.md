# 🛡️ AI-Based Hardware Trojan Detection System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Verilog HDL](https://img.shields.io/badge/HDL-Verilog--2001-red.svg?logo=verilog&logoColor=white)](https://en.wikipedia.org/wiki/Verilog)
[![XGBoost](https://img.shields.io/badge/ML%20Engine-XGBoost-orange.svg)](https://xgboost.ai/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Tailwind-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Computer Organization and Architecture Project**  
> **SRM Institute of Science and Technology**  
> An end-to-end framework that couples **Verilog HDL simulation** of a 16-bit RISC ALU with **XGBoost Machine Learning** to detect stealthy hardware Trojans from circuit switching activity and telemetry.

---

## 📌 Project Overview

Modern integrated circuits (ICs) are often designed and fabricated across untrusted third-party foundries, creating vulnerabilities to **Hardware Trojans (HTs)**. These malicious circuit modifications remain dormant during standard testing and activate only under rare operational triggers.

Because physical silicon fabrication is inaccessible, this project implements a **complete virtualized hardware security flow**:
1. **Hardware Emulation in Verilog**: Designed a synthesizable 16-bit RISC ALU with standard arithmetic, logic, and barrel shifter units.
2. **Trojan Design & Insertion**: Implemented 3 realistic Trojan attack vectors (control flag tampering, counter-based aging bombs, and side-channel power leakage).
3. **Automated Telemetry Dataset**: Simulated 10,500 clock cycles using Icarus Verilog (`iverilog`) and extracted 37 hardware switching and flag divergence features.
4. **Machine Learning Classifier**: Trained an **XGBoost** model to classify circuit states into `Clean`, `Trojan 1 (Flag)`, `Trojan 2 (Counter)`, or `Trojan 3 (Side-Channel)`.
5. **Interactive Dashboard & Autonomous Testing Bot**: A React + Tailwind web UI where users can input any operands to scan the circuit or let a randomized **Auto-Test Bot** continuously stress-test the hardware.

---

## 🏗️ Hardware Architecture (16-Bit RISC ALU)

The simulated processor datapath executes 16 distinct operations with four status flags (**Z**ero, **C**arry, O**v**erflow, **S**ign):

| Opcode | Mnemonic | Operation Category | Description |
|:---:|:---:|:---:|---|
| `0000` | **ADD** | Arithmetic | $A + B$ (signed overflow & carry tracked) |
| `0001` | **SUB** | Arithmetic | $A - B$ |
| `0010` | **MUL** | Arithmetic | $A \times B$ (lower 16 bits) |
| `0011` | **DIV** | Arithmetic | $A / B$ (integer quotient) |
| `0100` | **AND** | Logic | $A \ \& \ B$ |
| `0101` | **OR** | Logic | $A \ \| \ B$ |
| `0110` | **XOR** | Logic | $A \oplus B$ |
| `0111` | **NOT** | Logic | $\sim A$ |
| `1000` | **NAND**| Logic | $\sim (A \ \& \ B)$ |
| `1001` | **NOR** | Logic | $\sim (A \ \| \ B)$ |
| `1010` | **XNOR**| Logic | $\sim (A \oplus B)$ |
| `1011` | **SHL** | Barrel Shifter | Logical Shift Left ($A \ll B[3:0]$) |
| `1012` | **SHR** | Barrel Shifter | Logical Shift Right ($A \gg B[3:0]$) |
| `1101` | **SAR** | Barrel Shifter | Arithmetic Shift Right ($A \ggg B[3:0]$) |
| `1110` | **ROL** | Barrel Shifter | Rotate Left by $B[3:0]$ |
| `1111` | **ROR** | Barrel Shifter | Rotate Right by $B[3:0]$ |

---

## 👾 Implemented Hardware Trojan Taxonomies

```
                  ┌──────────────────────────────┐
                  │ 16-Bit RISC ALU Datapath     │
                  └──────────────┬───────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Trojan 1: Flag   │   │ Trojan 2: Aging  │   │ Trojan 3: Power  │
│ Tampering        │   │ Counter Bomb     │   │ Side-Channel     │
├──────────────────┤   ├──────────────────┤   ├──────────────────┤
│ Rare Trigger:    │   │ Digital Trigger: │   │ Always-On:       │
│ A=0xFFFF,B=0x0001│   │ Operates after   │   │ Zero functional  │
│ SUB instruction  │   │ 512 clock cycles │   │ output change    │
├──────────────────┤   ├──────────────────┤   ├──────────────────┤
│ Payload: Inverts │   │ Payload: Flips   │   │ Payload: High-   │
│ Z and V flags;   │   │ MSB of result    │   │ toggle dummy FFs │
│ output stays OK  │   │ post-threshold   │   │ leak power info  │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

1. **Trojan 1 (`trojan1_flag_tamper.v`)**:
   * **Trigger**: Rare operand combination ($p \approx 2^{-32}$): `A == 16'hFFFF`, `B == 16'h0001`, and `opcode == SUB`.
   * **Payload**: Corrupts conditional branching by inverting **Zero (Z)** and **Overflow (V)** flags while leaving the numerical ALU result unaltered.
2. **Trojan 2 (`trojan2_counter_payload.v`)**:
   * **Trigger**: 9-bit internal clock counter. Remains dormant during the first 512 operations to evade manufacturing burn-in screening.
   * **Payload**: Once armed ($\ge 512$), flips the Most Significant Bit (MSB `result[15]`) of all subsequent calculations.
3. **Trojan 3 (`trojan3_sidechannel.v`)**:
   * **Trigger**: Always active.
   * **Payload**: Modulates 16 internal phantom flip-flops based on operands. Induces elevated dynamic switching power and electromagnetic leakage without altering a single bit of functional output.

---

## 🧠 Machine Learning Detection Engine

### 1. Engineered Hardware Features (37 Signals)
* **Operand Metrics**: Hamming weight of $A$, Hamming weight of $B$, instruction category (arithmetic, logic, shift).
* **Verilog ALU Status**: Core status flags ($Z, C, V, S$).
* **Switching Activity Telemetry**: Cycle toggle count, rolling window 5-cycle mean toggles, standard deviation of toggles, and phantom leakage ratio.
* **Risk & Proximity Indices**: Trigger pattern proximity, flag divergence ratio, and cumulative activity index.

### 2. XGBoost Performance
* **Total Dataset**: 10,500 simulation cycles (8,400 train / 2,100 test).
* **Accuracy**: **45.14%** across complex 4-class multi-trojan classification.
* **Exploit Trigger Recall**: **97.08% confidence** on detecting rare flag tampering attacks.

---

## 💻 Web Application & Autonomous Testing Bot

The repository includes a modern web dashboard built with **React**, **Tailwind CSS**, and **FastAPI**:

* **Manual Input Scanner**: Enter any hex or decimal inputs (e.g., `A = 0xFFFF`, `B = 0x0001`, `SUB`) and click **Scan Circuit** to receive an instant verdict (**CLEAN** vs. **TROJAN DETECTED**) along with explainable AI reasoning.
* **Autonomous Testing Bot**:
  * Randomly generates hardware test vectors.
  * Clocks the simulated Verilog ALU.
  * Streams live pass/fail logs with live telemetry counters (**Tests Run**, **Clean Passed**, **Trojans Caught**).
  * Includes a continuous auto-scanner with start/stop controls.

---

## 📁 Repository Structure

```text
├── alu_16bit/                      # Verilog HDL Hardware Sources
│   ├── alu_16bit.v                 # Top-level synthesizable 16-bit ALU
│   ├── alu_arithmetic.v            # Adder / Subtractor / Multiplier / Divider
│   ├── alu_logic.v                 # Logic gates (AND, OR, XOR, NAND, etc.)
│   ├── alu_shifter.v               # Barrel shifter & rotator
│   ├── alu_flags.v                 # Status flag computation (Z, C, V, S)
│   ├── trojan1_flag_tamper.v       # Trojan 1 source
│   ├── trojan2_counter_payload.v   # Trojan 2 source
│   ├── trojan3_sidechannel.v       # Trojan 3 source
│   ├── tb_trojans.v                # Trojan verification testbench
│   └── alu_dataset_harness.v       # 4-core parallel simulation logging harness
├── ml_results/                     # Trained ML Models & Metrics
│   ├── model_xgb.json              # Trained XGBoost model file
│   ├── model_xgb.pkl               # Serialized Python pickle model
│   ├── scaler.pkl                  # Feature normalizer
│   ├── label_encoder.pkl           # Target label encoder
│   ├── cm_xgb.png                  # Test confusion matrix plot
│   └── fi_xgb.png                  # Top feature importance plot
├── dashboard/                      # React + Tailwind Frontend
│   ├── src/
│   │   ├── App.jsx                 # Core UI with Input Scanner & Auto-Test Bot
│   │   └── index.css               # Styling and theme
│   ├── dist/                       # Built static bundle served by FastAPI
│   └── package.json
├── alu_trojan_dataset.csv          # Generated 10,500-sample dataset
├── generate_dataset.py             # Stimulus engine & Verilog simulation runner
├── train_ml_models.py              # XGBoost training & cross-validation script
├── backend_api.py                  # FastAPI REST backend & web server
└── README.md
```

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
1. **Python 3.10+** (with pip)
2. **Icarus Verilog** (`iverilog` & `vvp`) added to your system `PATH`
3. **Node.js 18+** (optional, only if modifying the frontend)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/hardware-trojan-detection.git
cd hardware-trojan-detection
```

### 2. Install Python Dependencies
```bash
pip install fastapi uvicorn xgboost scikit-learn pandas numpy matplotlib seaborn
```

### 3. (Optional) Re-simulate Verilog Dataset & Train Model
```bash
# Generate 10,500 simulation cycles via Icarus Verilog
python generate_dataset.py

# Train the XGBoost Classifier
python train_ml_models.py
```

### 4. Launch the Application
```bash
python backend_api.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 🧪 Quick Test Vectors

Try these inputs in the dashboard to see immediate verdicts:

* **Clean Arithmetic**: `A = 0x0010`, `B = 0x0005`, `Operation = ADD`  
  $\rightarrow$ Result: `0x0015` | **Verdict: ✅ CIRCUIT IS CLEAN**
* **Trojan 1 Exploit Trigger**: `A = 0xFFFF`, `B = 0x0001`, `Operation = SUB`  
  $\rightarrow$ Result: `0xFFFE` | **Verdict: 🚨 HARDWARE TROJAN DETECTED (trojan1_flag)**
* **Automated Bot**: Click **"Test 10 Random Inputs"** or **"Start Bot"** to observe automated random vector stress testing in real time.

---

## 📜 Academic Attribution

* **Institution**: SRM Institute of Science and Technology
* **Department**: Computer Science and Engineering
* **Course**: Computer Organization and Architecture (Semester 5)
* **Topic**: AI-Assisted Hardware Security & Trojan Detection in VLSI Datapaths
