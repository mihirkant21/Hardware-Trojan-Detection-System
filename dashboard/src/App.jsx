import React, { useState, useEffect, useRef } from 'react';
import {
  Shield, AlertTriangle, CheckCircle2, Bot, Play, Pause,
  RefreshCw, Send, ChevronDown, ChevronUp, Cpu, Wrench, Bug, Sparkles
} from 'lucide-react';

const OPERATIONS = [
  { code: 0, name: "ADD (+)" },
  { code: 1, name: "SUB (-)" },
  { code: 2, name: "MUL (*)" },
  { code: 3, name: "DIV (/)" },
  { code: 4, name: "AND (&)" },
  { code: 5, name: "OR (|)" },
  { code: 6, name: "XOR (^)" },
  { code: 7, name: "NOT (~A)" },
  { code: 11, name: "SHL (<<)" },
  { code: 12, name: "SHR (>>)" }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('scanner'); // 'scanner', 'custom_virus', 'bot'

  // Standard Scanner State
  const [valA, setValA] = useState('0xFFFF');
  const [valB, setValB] = useState('0x0001');
  const [opcode, setOpcode] = useState(1);
  const [scanResult, setScanResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showFeatures, setShowFeatures] = useState(false);

  // Custom Virus Creator State
  const [virusA, setVirusA] = useState('0x1234');
  const [virusB, setVirusB] = useState('0x0010');
  const [virusOp, setVirusOp] = useState(0);
  const [virusCycles, setVirusCycles] = useState(25);
  const [triggerType, setTriggerType] = useState('operand_match'); // 'operand_match', 'cycle_threshold', 'always_on'
  const [trigAVal, setTrigAVal] = useState('0x1234');
  const [trigCyclesVal, setTrigCyclesVal] = useState(20);
  const [payloadType, setPayloadType] = useState('flag_tamper'); // 'flag_tamper', 'bit_flip', 'power_leak'
  const [flipBit, setFlipBit] = useState(15);
  const [leakIntensity, setLeakIntensity] = useState(14);
  const [virusResult, setVirusResult] = useState(null);
  const [testingVirus, setTestingVirus] = useState(false);

  // Bot State
  const [botRunning, setBotRunning] = useState(false);
  const [botFeed, setBotFeed] = useState([]);
  const [stats, setStats] = useState({ scanned: 0, safe: 0, trojans: 0 });
  const intervalRef = useRef(null);

  const API_BASE = "http://127.0.0.1:8000";

  useEffect(() => {
    scanInput('0xFFFF', '0x0001', 1);
  }, []);

  const parseNumber = (val) => {
    if (typeof val === 'string' && val.trim().toLowerCase().startsWith('0x')) {
      return parseInt(val.trim(), 16) || 0;
    }
    return parseInt(val, 10) || 0;
  };

  const scanInput = async (aInput = null, bInput = null, opInput = null) => {
    setLoading(true);
    const a = aInput !== null ? parseNumber(aInput) : parseNumber(valA);
    const b = bInput !== null ? parseNumber(bInput) : parseNumber(valB);
    const op = opInput !== null ? opInput : opcode;

    try {
      const res = await fetch(`${API_BASE}/api/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ A: a, B: b, opcode: op, cycle_count: (a === 0xFFFF && b === 0x0001) ? 10 : 1 })
      });
      if (res.ok) {
        const data = await res.json();
        setScanResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestCustomVirus = async () => {
    setTestingVirus(true);
    const a = parseNumber(virusA);
    const b = parseNumber(virusB);
    const trigA = parseNumber(trigAVal);

    try {
      const res = await fetch(`${API_BASE}/api/custom_virus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          A: a,
          B: b,
          opcode: virusOp,
          cycle_count: Number(virusCycles),
          trigger_type: triggerType,
          trigger_A: trigA,
          trigger_opcode: virusOp,
          trigger_cycles: Number(trigCyclesVal),
          payload_type: payloadType,
          flip_bit: Number(flipBit),
          power_leak_intensity: Number(leakIntensity)
        })
      });
      if (res.ok) {
        const data = await res.json();
        setVirusResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setTestingVirus(false);
    }
  };

  // Bot Logic
  const runBotCycle = async (count = 5) => {
    try {
      const res = await fetch(`${API_BASE}/api/bot/auto_test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num_vectors: count, include_trojan_scenarios: true })
      });
      if (res.ok) {
        const data = await res.json();
        setBotFeed(prev => [...data.test_logs, ...prev].slice(0, 30));
        setStats(prev => ({
          scanned: prev.scanned + data.total_scanned,
          safe: prev.safe + data.clean_passed,
          trojans: prev.trojans + data.trojans_detected
        }));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const toggleBot = () => {
    if (botRunning) {
      clearInterval(intervalRef.current);
      setBotRunning(false);
    } else {
      setBotRunning(true);
      runBotCycle(3);
      intervalRef.current = setInterval(() => {
        runBotCycle(2);
      }, 1500);
    }
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#080C14] text-slate-100 flex flex-col font-sans">
      {/* Navbar with Mode Switcher */}
      <nav className="border-b border-slate-800 bg-[#0E1322] px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center justify-center">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-base tracking-wide text-white">Hardware Trojan Virus Detector</h1>
            <p className="text-xs text-slate-400">Verilog 16-Bit RISC ALU &bull; 37 Telemetry Features &bull; XGBoost AI</p>
          </div>
        </div>

        {/* 3 Core Modes */}
        <div className="flex items-center gap-1.5 bg-[#090D18] p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('scanner')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'scanner'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Send className="w-3.5 h-3.5" />
            Circuit Scanner
          </button>
          <button
            onClick={() => { setActiveTab('custom_virus'); if (!virusResult) handleTestCustomVirus(); }}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'custom_virus'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Bug className="w-3.5 h-3.5" />
            Custom Virus Creator
          </button>
          <button
            onClick={() => setActiveTab('bot')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'bot'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Bot className="w-3.5 h-3.5" />
            Auto-Test Bot
          </button>
        </div>
      </nav>

      {/* Main Body */}
      <main className="flex-1 max-w-5xl mx-auto w-full p-6 space-y-6">

        {/* MODE 1: STANDARD CIRCUIT SCANNER */}
        {activeTab === 'scanner' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Input Form */}
              <div className="bg-[#111728] border border-slate-800 rounded-2xl p-5 space-y-4">
                <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Send className="w-4 h-4 text-cyan-400" />
                  1. Give Hardware Input
                </h2>

                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Operand A (Hex/Dec):</label>
                      <input
                        type="text"
                        value={valA}
                        onChange={(e) => setValA(e.target.value)}
                        className="w-full bg-[#0A0E17] border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Operand B (Hex/Dec):</label>
                      <input
                        type="text"
                        value={valB}
                        onChange={(e) => setValB(e.target.value)}
                        className="w-full bg-[#0A0E17] border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Instruction (Opcode):</label>
                    <select
                      value={opcode}
                      onChange={(e) => setOpcode(Number(e.target.value))}
                      className="w-full bg-[#0A0E17] border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-slate-200 focus:outline-none focus:border-cyan-400"
                    >
                      {OPERATIONS.map(op => (
                        <option key={op.code} value={op.code}>{op.name}</option>
                      ))}
                    </select>
                  </div>

                  <button
                    onClick={() => scanInput()}
                    disabled={loading}
                    className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-2.5 rounded-lg text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-900/30"
                  >
                    {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
                    Scan Circuit with XGBoost
                  </button>

                  <div className="pt-2 flex gap-2">
                    <button
                      onClick={() => { setValA('0x0010'); setValB('0x0005'); setOpcode(0); scanInput('0x0010', '0x0005', 0); }}
                      className="flex-1 py-1.5 px-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded text-xs text-slate-400"
                    >
                      Test Clean ADD
                    </button>
                    <button
                      onClick={() => { setValA('0xFFFF'); setValB('0x0001'); setOpcode(1); scanInput('0xFFFF', '0x0001', 1); }}
                      className="flex-1 py-1.5 px-2 bg-rose-950/30 hover:bg-rose-950/50 border border-rose-900/40 rounded text-xs text-rose-300"
                    >
                      Trigger Trojan Exploit
                    </button>
                  </div>
                </div>
              </div>

              {/* Result Verdict Box */}
              <div className="bg-[#111728] border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
                <h2 className="text-sm font-semibold text-slate-200 mb-3">2. AI Detection Verdict</h2>

                {scanResult ? (
                  <div className="space-y-4 my-auto">
                    <div className={`p-5 rounded-xl border flex items-center gap-4 ${
                      scanResult.trojan_detection.is_trojan
                        ? 'bg-rose-950/30 border-rose-500/50 text-rose-300'
                        : 'bg-emerald-950/30 border-emerald-500/50 text-emerald-300'
                    }`}>
                      {scanResult.trojan_detection.is_trojan ? (
                        <AlertTriangle className="w-10 h-10 text-rose-400 shrink-0" />
                      ) : (
                        <CheckCircle2 className="w-10 h-10 text-emerald-400 shrink-0" />
                      )}
                      <div>
                        <div className="text-lg font-black tracking-wide">
                          {scanResult.trojan_detection.is_trojan ? 'HARDWARE TROJAN DETECTED!' : 'CIRCUIT IS CLEAN'}
                        </div>
                        <div className="text-xs font-mono opacity-80 mt-0.5">
                          Classification: <span className="font-bold underline">{scanResult.trojan_detection.threat_type}</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2 text-xs bg-[#0A0E17] p-3 rounded-xl border border-slate-800 font-mono">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Verilog ALU Output:</span>
                        <span className="font-bold text-cyan-300">{scanResult.verilog_alu.result_hex} ({scanResult.verilog_alu.result_dec})</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">XGBoost Confidence:</span>
                        <span className="font-bold text-white">{(scanResult.trojan_detection.confidence * 100).toFixed(1)}%</span>
                      </div>
                      <div className="pt-1 border-t border-slate-800/60 text-slate-300 text-[11px]">
                        &bull; {scanResult.trojan_detection.analysis_reason}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 font-mono text-center my-auto">Scanning...</div>
                )}
              </div>
            </div>

            {/* 37 TELEMETRY FEATURES INSPECTOR */}
            {scanResult?.telemetry_37_features && (
              <div className="bg-[#111728] border border-slate-800 rounded-2xl p-5 space-y-4">
                <button
                  onClick={() => setShowFeatures(!showFeatures)}
                  className="w-full flex items-center justify-between text-xs font-mono text-cyan-300 hover:text-cyan-200"
                >
                  <span className="font-bold flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-cyan-400" />
                    Live 37 Hardware Telemetry Signals Used by XGBoost ({showFeatures ? 'Hide' : 'Inspect All 37 Features'})
                  </span>
                  {showFeatures ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showFeatures && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5 pt-2">
                    {Object.entries(scanResult.telemetry_37_features).map(([key, val]) => (
                      <div key={key} className="bg-[#0A0E17] p-2.5 rounded-lg border border-slate-800 font-mono">
                        <span className="text-[10px] text-slate-400 block truncate" title={key}>{key}</span>
                        <span className="text-xs font-bold text-cyan-300">
                          {typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(3)) : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* MODE 2: CUSTOM TROJAN VIRUS CREATOR */}
        {activeTab === 'custom_virus' && (
          <div className="space-y-6">
            <div className="bg-[#111728] border border-rose-900/40 rounded-2xl p-6 space-y-5">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-rose-300 flex items-center gap-2">
                    <Bug className="w-5 h-5 text-rose-400" />
                    Custom Hardware Trojan / Virus Builder
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Configure your own trigger condition and malicious payload to test whether XGBoost intercepts it!
                  </p>
                </div>
                <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-rose-950/60 text-rose-300 border border-rose-800">
                  Malware Forge
                </span>
              </div>

              {/* Virus Configuration Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 1. Trigger Configuration */}
                <div className="bg-[#0A0E17] p-4 rounded-xl border border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-amber-300 font-mono uppercase block">Step 1: Choose Virus Trigger</span>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Trigger Condition:</label>
                    <select
                      value={triggerType}
                      onChange={(e) => setTriggerType(e.target.value)}
                      className="w-full bg-[#111728] border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200"
                    >
                      <option value="operand_match">Specific Operand Match (e.g. A == Target)</option>
                      <option value="cycle_threshold">Time-Delayed Aging (Cycle &ge; Threshold)</option>
                      <option value="always_on">Always-On (Stealth Mode)</option>
                    </select>
                  </div>

                  {triggerType === 'operand_match' && (
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Trigger Target for Operand A:</label>
                      <input
                        type="text"
                        value={trigAVal}
                        onChange={(e) => setTrigAVal(e.target.value)}
                        className="w-full bg-[#111728] border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-amber-300"
                        placeholder="0x1234"
                      />
                    </div>
                  )}

                  {triggerType === 'cycle_threshold' && (
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Fire after N clock cycles:</label>
                      <input
                        type="number"
                        value={trigCyclesVal}
                        onChange={(e) => setTrigCyclesVal(e.target.value)}
                        className="w-full bg-[#111728] border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-amber-300"
                      />
                    </div>
                  )}
                </div>

                {/* 2. Payload Configuration */}
                <div className="bg-[#0A0E17] p-4 rounded-xl border border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-rose-300 font-mono uppercase block">Step 2: Choose Malicious Payload</span>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Attack Vector / Payload:</label>
                    <select
                      value={payloadType}
                      onChange={(e) => setPayloadType(e.target.value)}
                      className="w-full bg-[#111728] border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200"
                    >
                      <option value="flag_tamper">Corrupt Control Flags (Invert Zero &amp; Overflow)</option>
                      <option value="bit_flip">Data Corruption (Flip a Specific Result Bit)</option>
                      <option value="power_leak">Dynamic Power Leakage (Phantom Gate Toggles)</option>
                    </select>
                  </div>

                  {payloadType === 'bit_flip' && (
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Bit Index to Invert (0 to 15):</label>
                      <input
                        type="number"
                        min="0"
                        max="15"
                        value={flipBit}
                        onChange={(e) => setFlipBit(Number(e.target.value))}
                        className="w-full bg-[#111728] border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-rose-300"
                      />
                    </div>
                  )}

                  {payloadType === 'power_leak' && (
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Extra Phantom Switching Toggles:</label>
                      <input
                        type="number"
                        value={leakIntensity}
                        onChange={(e) => setLeakIntensity(Number(e.target.value))}
                        className="w-full bg-[#111728] border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-purple-300"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Hardware Test Inputs for the Virus */}
              <div className="bg-[#0A0E17] p-4 rounded-xl border border-slate-800 space-y-3">
                <span className="text-xs font-bold text-cyan-300 font-mono uppercase block">Step 3: Test Inputs Fed to Circuit</span>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                  <div>
                    <label className="text-slate-400 block mb-1">Input A:</label>
                    <input
                      type="text"
                      value={virusA}
                      onChange={(e) => setVirusA(e.target.value)}
                      className="w-full bg-[#111728] border border-slate-700 rounded px-2.5 py-1.5 text-cyan-300"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Input B:</label>
                    <input
                      type="text"
                      value={virusB}
                      onChange={(e) => setVirusB(e.target.value)}
                      className="w-full bg-[#111728] border border-slate-700 rounded px-2.5 py-1.5 text-cyan-300"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Opcode:</label>
                    <select
                      value={virusOp}
                      onChange={(e) => setVirusOp(Number(e.target.value))}
                      className="w-full bg-[#111728] border border-slate-700 rounded px-2 py-1.5 text-slate-200"
                    >
                      {OPERATIONS.map(op => (
                        <option key={op.code} value={op.code}>{op.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Clock Cycle:</label>
                    <input
                      type="number"
                      value={virusCycles}
                      onChange={(e) => setVirusCycles(Number(e.target.value))}
                      className="w-full bg-[#111728] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                    />
                  </div>
                </div>
              </div>

              <button
                onClick={handleTestCustomVirus}
                disabled={testingVirus}
                className="w-full py-3 bg-gradient-to-r from-rose-600 via-pink-600 to-purple-600 hover:from-rose-500 hover:to-purple-500 text-white font-bold rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-rose-950/40 transition-all"
              >
                {testingVirus ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Bug className="w-4 h-4" />}
                Deploy Custom Virus &amp; Test AI Defense
              </button>

              {/* Custom Virus Result */}
              {virusResult && (
                <div className={`p-5 rounded-xl border space-y-3 ${
                  virusResult.ml_defense_verdict.detected
                    ? 'bg-rose-950/30 border-rose-500/50 text-rose-300'
                    : 'bg-amber-950/30 border-amber-500/50 text-amber-300'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold uppercase tracking-wider">AI Defense Result</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300">
                      Triggered: {virusResult.virus_configuration.was_triggered ? 'YES' : 'NO (Dormant)'}
                    </span>
                  </div>

                  <div className="flex items-start gap-3">
                    {virusResult.ml_defense_verdict.detected ? (
                      <AlertTriangle className="w-8 h-8 text-rose-400 shrink-0" />
                    ) : (
                      <Shield className="w-8 h-8 text-amber-400 shrink-0" />
                    )}
                    <div>
                      <h3 className="text-lg font-black tracking-wide">
                        {virusResult.ml_defense_verdict.verdict}
                      </h3>
                      <p className="text-xs font-mono text-slate-200 mt-0.5">
                        Hardware Impact: <span className="text-slate-300 font-bold">{virusResult.virus_configuration.hardware_impact}</span>
                      </p>
                      <p className="text-xs font-mono text-slate-400 mt-1">
                        XGBoost AI Confidence: {(virusResult.ml_defense_verdict.confidence * 100).toFixed(1)}% &bull; Detected as: <span className="underline uppercase font-bold text-white">{virusResult.ml_defense_verdict.threat_category}</span>
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* MODE 3: AUTONOMOUS TESTING BOT */}
        {activeTab === 'bot' && (
          <div className="bg-[#111728] border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-purple-400" />
                <h2 className="text-sm font-semibold text-white">Autonomous Verification Bot</h2>
                <span className="text-xs text-slate-400">(Randomly feeds inputs to check the circuit)</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => runBotCycle(10)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-mono rounded-lg transition-all"
                >
                  Test 10 Random Inputs
                </button>
                <button
                  onClick={toggleBot}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all ${
                    botRunning
                      ? 'bg-rose-600 text-white animate-pulse'
                      : 'bg-purple-600 hover:bg-purple-500 text-white'
                  }`}
                >
                  {botRunning ? <><Pause className="w-3.5 h-3.5" /> Stop Bot</> : <><Play className="w-3.5 h-3.5 fill-current" /> Start Bot</>}
                </button>
              </div>
            </div>

            {/* Score Counter */}
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-2.5 rounded-xl bg-[#0A0E17] border border-slate-800">
                <span className="text-[11px] text-slate-400 block font-mono">Tests Run</span>
                <span className="text-lg font-bold text-cyan-300 font-mono">{stats.scanned}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#0A0E17] border border-slate-800">
                <span className="text-[11px] text-slate-400 block font-mono">Clean Inputs</span>
                <span className="text-lg font-bold text-emerald-400 font-mono">{stats.safe}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#0A0E17] border border-slate-800">
                <span className="text-[11px] text-slate-400 block font-mono">Trojans Caught</span>
                <span className="text-lg font-bold text-rose-400 font-mono">{stats.trojans}</span>
              </div>
            </div>

            {/* Clean Bot Log */}
            <div className="overflow-x-auto max-h-60 overflow-y-auto rounded-xl border border-slate-800 bg-[#0A0E17]">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#111728] text-slate-400 sticky top-0 uppercase text-[10px]">
                  <tr>
                    <th className="py-2 px-3">Input A</th>
                    <th className="py-2 px-3">Operation</th>
                    <th className="py-2 px-3">Input B</th>
                    <th className="py-2 px-3">Result</th>
                    <th className="py-2 px-3">Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {botFeed.length > 0 ? (
                    botFeed.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/50">
                        <td className="py-1.5 px-3 text-cyan-300">{item.A_hex}</td>
                        <td className="py-1.5 px-3 text-slate-300">{item.opcode_name}</td>
                        <td className="py-1.5 px-3 text-cyan-300">{item.B_hex}</td>
                        <td className="py-1.5 px-3 text-slate-400">{item.result_hex}</td>
                        <td className="py-1.5 px-3 font-bold">
                          {item.is_trojan ? (
                            <span className="text-rose-400">🚨 {item.prediction}</span>
                          ) : (
                            <span className="text-emerald-400">✅ Clean</span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-5 text-center text-slate-500">
                        Click &ldquo;Test 10 Random Inputs&rdquo; or &ldquo;Start Bot&rdquo; to test automatically.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
