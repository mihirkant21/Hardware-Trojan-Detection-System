"""
=============================================================
Hardware Trojan Detection: XGBoost Classifier Engine
Project: AI-Based Hardware Trojan Detection System
=============================================================
Model:
  XGBoost (Gradient Boosted Decision Trees)
  - Selected by user for maximum aggressive threat detection
  - Multi-class classification: clean, trojan1_flag, trojan2_counter, trojan3_side
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

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
import xgboost as xgb

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report, roc_auc_score
)

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR    = Path(r"E:\SRM Study Filess\SRM SEM-5\Computer Organization and Architecture\Project")
DATASET     = BASE_DIR / "alu_trojan_dataset.csv"
RESULTS_DIR = BASE_DIR / "ml_results"
RESULTS_DIR.mkdir(exist_ok=True)

plt.style.use("dark_background")

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


def load_data():
    print("=" * 60)
    print("  Loading Verilog Hardware Telemetry Dataset...")
    print("=" * 60)
    df = pd.read_csv(DATASET)
    print(f"  Shape       : {df.shape}")
    print(f"  Distribution:\n{df['trojan_label'].value_counts().to_string()}\n")

    X = df[FEATURE_COLS].fillna(0)
    y_multi  = df['trojan_label']
    y_binary = df['trojan_binary']

    le = LabelEncoder()
    y_multi_enc = le.fit_transform(y_multi)

    X_train, X_test, ym_train, ym_test, yb_train, yb_test = train_test_split(
        X, y_multi_enc, y_binary,
        test_size=0.20, random_state=42, stratify=y_multi_enc
    )

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    print(f"  Train size  : {len(X_train)}")
    print(f"  Test size   : {len(X_test)}\n")

    return X_train, X_test, X_train_sc, X_test_sc, ym_train, ym_test, yb_train, yb_test, le, scaler, df


def train_xgboost(X_train, X_test, ym_train, ym_test, le):
    print("=" * 60)
    print("  Training Hardware Trojan Detection Model: XGBoost")
    print("=" * 60)

    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        eval_metric='mlogloss',
        random_state=42, n_jobs=-1,
        objective='multi:softprob',
        num_class=len(le.classes_)
    )
    model.fit(X_train, ym_train, eval_set=[(X_test, ym_test)], verbose=False)

    y_pred = model.predict(X_test)
    acc = accuracy_score(ym_test, y_pred)
    f1 = f1_score(ym_test, y_pred, average='weighted')
    prec = precision_score(ym_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(ym_test, y_pred, average='weighted', zero_division=0)

    proba = model.predict_proba(X_test)
    auc = roc_auc_score(ym_test, proba, multi_class='ovr', average='weighted')

    print("\n" + "-" * 50)
    print("  Evaluation Results (Test Set 2,100 Cycles)")
    print("-" * 50)
    print(f"  Accuracy  : {acc:.4f} ({acc*100:.2f}%)")
    print(f"  F1 Score  : {f1:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  ROC-AUC   : {auc:.4f}")
    print(f"\n{classification_report(ym_test, y_pred, target_names=le.classes_, zero_division=0)}")

    # Confusion matrix plot
    fig, ax = plt.subplots(figsize=(8, 6))
    cm = confusion_matrix(ym_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=le.classes_, yticklabels=le.classes_, ax=ax,
                linewidths=0.5, linecolor='#333')
    ax.set_title("XGBoost — Hardware Trojan Confusion Matrix", fontsize=14, pad=12, color='white')
    ax.set_xlabel("Predicted", color='white')
    ax.set_ylabel("Actual", color='white')
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "cm_xgb.png", dpi=150, facecolor='#1a1a2e')
    plt.close()

    # Feature importance plot
    fi_df = pd.DataFrame({'feature': FEATURE_COLS, 'importance': model.feature_importances_})
    fi_df = fi_df.nlargest(15, 'importance').sort_values('importance')

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(fi_df['feature'], fi_df['importance'], color='#00D4FF', height=0.7)
    ax.set_title("XGBoost — Top 15 Detection Signatures", fontsize=13, color='white', pad=10)
    ax.set_xlabel("Importance Weight", color='white')
    ax.tick_params(colors='white')
    ax.spines[['top', 'right']].set_visible(False)
    for bar in bars:
        ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
                f'{bar.get_width():.3f}', va='center', fontsize=8, color='#aaa')
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "fi_xgb.png", dpi=150, facecolor='#1a1a2e')
    plt.close()

    # Save model in JSON and PKL formats
    model.save_model(str(RESULTS_DIR / "model_xgb.json"))
    with open(RESULTS_DIR / "model_xgb.pkl", "wb") as f:
        pickle.dump(model, f)

    # Save summary metrics
    metrics_df = pd.DataFrame([{
        "Model": "XGBoost",
        "Accuracy": round(acc, 4),
        "F1_Weighted": round(f1, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "ROC_AUC": round(auc, 4)
    }])
    metrics_df.to_csv(RESULTS_DIR / "ml_metrics_summary.csv", index=False)

    print(f"  [SAVED] XGBoost Model: ml_results/model_xgb.json & model_xgb.pkl")
    print(f"  [SAVED] Plots: cm_xgb.png, fi_xgb.png")
    print(f"  [SAVED] Metrics: ml_metrics_summary.csv")

    return model


if __name__ == "__main__":
    X_train, X_test, X_train_sc, X_test_sc, ym_train, ym_test, yb_train, yb_test, le, scaler, df = load_data()

    with open(RESULTS_DIR / "scaler.pkl", 'wb') as f:
        pickle.dump(scaler, f)
    with open(RESULTS_DIR / "label_encoder.pkl", 'wb') as f:
        pickle.dump(le, f)

    train_xgboost(X_train, X_test, ym_train, ym_test, le)
    print("\n" + "=" * 60)
    print("  XGBoost Training Complete!")
    print("=" * 60)
