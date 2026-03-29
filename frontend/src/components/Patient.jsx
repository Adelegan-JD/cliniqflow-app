import React, { useState, useEffect, useRef } from "react";
import {
  User,
  FileText,
  ChevronRight,
  Edit3,
  Check,
  Plus,
  Trash2,
  Save,
  AlertTriangle,
  Clock,
  Pill,
  Mic,
  Square,
  Type,
  Activity,
} from "lucide-react";
import { api } from "../utils/api";
import { toast } from "react-toastify";

const STEPS = ["transcript", "soap", "prescription", "save"];

/** Parse age string (e.g. "5 years", "52", "8 months") to approximate years for dose check */
function parseAgeYears(ageStr) {
  if (!ageStr) return 18;
  const s = String(ageStr).toLowerCase();
  const num = parseFloat(s.replace(/[^\d.]+/g, ""));
  if (isNaN(num)) return 18;
  if (s.includes("month")) return Math.max(0, num / 12);
  return Math.min(120, Math.max(0, num));
}

const ConsultationRoom = ({ patient, onSave, onCancel }) => {
  const visitId = patient?.id || patient?.visit_id;
  const patientId = patient?.patient_id;

  const [step, setStep] = useState("transcript");
  const [inputMode, setInputMode] = useState("recording"); // "recording" | "manual" — recording is default
  const [transcript, setTranscript] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [timer, setTimer] = useState(0);
  const recorderRef = useRef(null);

  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => setTimer((t) => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  useEffect(() => {
    return () => {
      const rec = recorderRef.current;
      if (rec && rec.state !== "inactive") rec.stop();
    };
  }, []);

  const [soapLoading, setSoapLoading] = useState(false);
  const [soap, setSoap] = useState(null);
  const [soapEditMode, setSoapEditMode] = useState(false);
  const [editedSoap, setEditedSoap] = useState({ S: "", O: "", A: "", P: "" });
  const [prescriptions, setPrescriptions] = useState([]);
  const [newRx, setNewRx] = useState({
    drug_name: "",
    dose_mg: "",
    frequency: "",
    duration_days: "",
  });
  const [doseCheckResult, setDoseCheckResult] = useState(null);
  const [doseCheckLoading, setDoseCheckLoading] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [doctorNotes, setDoctorNotes] = useState("");
  const [saveLoading, setSaveLoading] = useState(false);

  const weightKg =
    parseFloat(patient?.vitals?.weight_kg) ||
    parseFloat(patient?.vitals?.weight) ||
    50;
  const ageYears = parseAgeYears(patient?.Age || patient?.age);

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const startRecording = async () => {
    setTimer(0);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        const form = new FormData();
        form.append("file", blob, "recording.webm");
        form.append("session_id", "frontend");
        form.append("chunk_index", "0");
        setIsTranscribing(true);
        try {
          const getToken = (await import("../utils/uitils")).getToken;
          const token = await getToken();
          if (!token) {
            toast.error("Please sign in to use recording");
            setIsTranscribing(false);
            return;
          }
          const r = await fetch("/translate/chunk", {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: form,
          });
          const raw = await r.text();
          let data;
          try { data = raw ? JSON.parse(raw) : {}; } catch { data = raw; }
          if (r.ok) {
            const text = data.chunk_conversation ||
              (data.full_conversation || "").replace(/^\[Chunk \d+\]\s*\n?/i, "").trim() ||
              (Array.isArray(data.segments) ? data.segments.map((s) => s.translation).filter(Boolean).join("\n") : "");
            if (text) setTranscript((prev) => (prev ? prev + "\n\n" + text : text));
          } else {
            const err = data?.error?.message || data?.detail || raw?.slice(0, 200) || `Error ${r.status}`;
            toast.error(`Transcription failed: ${err}`);
          }
        } catch (err) {
          toast.error(err?.message || "Transcription failed");
        } finally {
          setIsTranscribing(false);
        }
      };
      recorder.start();
      recorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      toast.error("Unable to access microphone");
    }
  };

  const stopRecording = () => {
    const rec = recorderRef.current;
    if (rec && rec.state !== "inactive") rec.stop();
    setIsRecording(false);
  };

  const handleContinueFromTranscript = () => {
    if (!transcript.trim()) {
      toast.error("Please enter the consultation transcript");
      return;
    }
    setStep("soap");
    generateSoap();
  };

  const generateSoap = async () => {
    setSoapLoading(true);
    try {
      const ageVal = patient?.Age ?? patient?.age;
      const sexVal = patient?.gender ?? patient?.sex;
      const res = await api.post(
        `/visits/${visitId}/doctor-conversation`,
        {
          transcript: transcript.trim(),
          patient_age: ageVal != null && ageVal !== "" ? String(ageVal) : null,
          patient_sex: sexVal != null && sexVal !== "" ? String(sexVal) : null,
          triage_vitals: patient?.vitals && Object.keys(patient.vitals).length > 0 ? patient.vitals : null,
        }
      );
      const note = res.soap_note || {};
      const s = {
        S: note.subjective || "",
        O: note.objective || "",
        A: note.assessment || "",
        P: note.plan || "",
      };
      setSoap(s);
      setEditedSoap(s);
    } catch (e) {
      toast.error(e?.message || "Failed to generate SOAP notes");
    } finally {
      setSoapLoading(false);
    }
  };

  const handleConfirmSoap = () => {
    const final = soapEditMode ? editedSoap : soap;
    if (!final?.S && !final?.O && !final?.A && !final?.P) {
      toast.error("SOAP summary is empty");
      return;
    }
    setSoap(final);
    setSoapEditMode(false);
    setStep("prescription");
  };

  const runDoseCheck = async () => {
    if (!newRx.drug_name.trim() || !newRx.dose_mg || !newRx.frequency) {
      toast.error("Enter drug name, dose (mg/day), and frequency");
      return;
    }
    const doseMg = parseInt(newRx.dose_mg, 10);
    const freq = parseInt(newRx.frequency, 10);
    if (isNaN(doseMg) || doseMg <= 0 || isNaN(freq) || freq <= 0) {
      toast.error("Invalid dose or frequency");
      return;
    }
    setDoseCheckLoading(true);
    setDoseCheckResult(null);
    try {
      const res = await api.post("/ai/dose-check", {
        visit_id: visitId,
        drug: newRx.drug_name.trim(),
        age_years: Math.round(ageYears),
        weight_kg: weightKg,
        frequency_per_day: freq,
        chosen_dose_mg_per_day: doseMg,
      });
      setDoseCheckResult(res);
    } catch (e) {
      toast.error(e?.message || "Dose check failed");
    } finally {
      setDoseCheckLoading(false);
    }
  };

  const addPrescription = (skipCheck = false) => {
    if (!newRx.drug_name.trim() || !newRx.dose_mg || !newRx.frequency) return;
    const doseMg = parseInt(newRx.dose_mg, 10);
    const freq = parseInt(newRx.frequency, 10);
    const duration = newRx.duration_days ? parseInt(newRx.duration_days, 10) : null;
    const result = doseCheckResult || {
      safe: true,
      warnings: [],
      recommended_range_mg_per_day: { min: 0, max: doseMg },
      max_mg_per_day: doseMg,
      event_id: "",
      allow_override: true,
    };
    const isSafe = result.safe || skipCheck;
    const needsOverride = !result.safe && !skipCheck;
    if (needsOverride && !overrideReason.trim()) {
      toast.error("Please enter override reason");
      return;
    }
    setPrescriptions((prev) => [
      ...prev,
      {
        drug_name: newRx.drug_name.trim(),
        dose_mg_per_day: doseMg,
        frequency_per_day: freq,
        duration_days: duration,
        is_safe: isSafe,
        dose_check_result: {
          safe: result.safe,
          warnings: result.warnings || [],
          recommended_range_mg_per_day: result.recommended_range_mg_per_day,
          max_mg_per_day: result.max_mg_per_day,
        },
        override_reason: !result.safe && overrideReason.trim() ? overrideReason.trim() : null,
      },
    ]);
    setNewRx({ drug_name: "", dose_mg: "", frequency: "", duration_days: "" });
    setDoseCheckResult(null);
    setOverrideReason("");
  };

  const removePrescription = (idx) => {
    setPrescriptions((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSaveVisit = async () => {
    const finalSoap = soapEditMode ? editedSoap : soap;
    if (!finalSoap) {
      toast.error("SOAP summary is required");
      return;
    }
    setSaveLoading(true);
    try {
      await api.post("/doctor/save-visit", {
        visit_id: visitId,
        patient_id: patientId,
        transcript: transcript.trim(),
        soap_summary: {
          subjective: finalSoap.S,
          objective: finalSoap.O,
          assessment: finalSoap.A,
          plan: finalSoap.P,
        },
        prescriptions: prescriptions.map((p) => ({
          drug_name: p.drug_name,
          dose_mg_per_day: p.dose_mg_per_day,
          frequency_per_day: p.frequency_per_day,
          duration_days: p.duration_days,
          is_safe: p.is_safe,
          dose_check_result: p.dose_check_result,
          override_reason: p.override_reason || undefined,
        })),
        doctor_notes: doctorNotes.trim() || undefined,
      });
      toast.success("Visit saved successfully");
      onSave?.();
    } catch (e) {
      toast.error(e?.message || "Failed to save visit");
    } finally {
      setSaveLoading(false);
    }
  };

  const stepIndex = STEPS.indexOf(step);

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-sm shrink-0">
        <div className="flex items-center gap-4">
          <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
            <User size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-800 uppercase tracking-tight">
              {patient?.name || "Patient Consultation"}
            </h2>
            <p className="text-sm text-slate-500">
              Age: {patient?.Age ?? patient?.age ?? "—"} • Weight: {weightKg} kg • PID: {patient?.pid ?? patientId ?? "—"}
            </p>
          </div>
        </div>
        <div className="flex gap-2 items-center">
          {STEPS.map((s, i) => (
            <span
              key={s}
              className={`text-[10px] uppercase font-bold px-2 py-1 rounded ${
                stepIndex >= i
                  ? "bg-blue-100 text-blue-700"
                  : "bg-slate-100 text-slate-400"
              }`}
            >
              {i + 1}
            </span>
          ))}
          <button
            onClick={onCancel}
            className="ml-4 px-4 py-2 text-slate-600 hover:bg-slate-100 font-semibold rounded-lg"
          >
            Cancel
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-8">
        {/* Step 1: Transcript */}
        {step === "transcript" && (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Mode toggle */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
              <p className="text-xs font-bold text-slate-500 uppercase mb-3">Input method</p>
              <div className="flex gap-2">
                <button
                  onClick={() => setInputMode("recording")}
                  className={`px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                    inputMode === "recording"
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  <Mic size={18} />
                  Start Recording
                </button>
                <button
                  onClick={() => setInputMode("manual")}
                  className={`px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                    inputMode === "manual"
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  <Type size={18} />
                  Type Manually
                </button>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              {/* Recording UI (default) */}
              {inputMode === "recording" && (
                <div className="relative p-8 border-b border-slate-100 flex flex-col items-center">
                  <div className="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none">
                    <Activity size={300} strokeWidth={1} />
                  </div>
                  <div
                    className={`w-24 h-24 rounded-full flex items-center justify-center transition-all ${
                      isRecording ? "bg-red-500 scale-110 shadow-xl shadow-red-200" : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    <Mic size={40} className={isRecording ? "text-white animate-pulse" : ""} />
                  </div>
                  <p className="mt-4 text-4xl font-mono font-black text-slate-800">{formatTime(timer)}</p>
                  <p className="text-slate-500 text-sm mt-1">
                    {isTranscribing ? "Transcribing…" : isRecording ? "Recording…" : "Click to start recording"}
                  </p>
                  <div className="mt-6 flex gap-4">
                    {!isRecording ? (
                      <button
                        onClick={startRecording}
                        className="px-8 py-3 bg-slate-900 text-white rounded-full font-bold flex items-center gap-2 hover:bg-blue-600"
                      >
                        <Mic size={20} /> Start Recording
                      </button>
                    ) : (
                      <button
                        onClick={stopRecording}
                        className="px-8 py-3 bg-red-600 text-white rounded-full font-bold flex items-center gap-2 hover:bg-red-700"
                      >
                        <Square size={20} /> Stop & Process
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Transcript area (shared) */}
              <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                <h3 className="font-bold text-slate-700 flex items-center gap-2">
                  <FileText size={18} className="text-blue-500" />
                  Consultation Transcript
                </h3>
                {isTranscribing && (
                  <span className="text-xs bg-amber-50 text-amber-700 px-3 py-1 rounded-full font-semibold animate-pulse">
                    Transcribing…
                  </span>
                )}
              </div>
              <textarea
                className="w-full min-h-[200px] p-6 text-slate-700 leading-relaxed focus:outline-none resize-none border-0"
                placeholder={
                  inputMode === "manual"
                    ? "Patient: I have had a fever and headache for three days.\n\nDoctor: Any nausea or vomiting?\n\nPatient: I feel slightly nauseous but no vomiting."
                    : "Transcript will appear here after you stop recording."
                }
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                readOnly={isTranscribing}
              />
              <div className="px-6 py-4 border-t border-slate-100 flex justify-end">
                <button
                  onClick={handleContinueFromTranscript}
                  disabled={!transcript.trim()}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold rounded-lg flex items-center gap-2"
                >
                  Continue to SOAP
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <Clock size={20} className="text-amber-500" />
                Patient Vitals (from triage)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-slate-50 p-3 rounded-xl">
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Blood Pressure</p>
                  <p className="text-lg font-black text-slate-700">
                    {patient?.vitals?.bpSystolic && patient?.vitals?.bpDiastolic
                      ? `${patient.vitals.bpSystolic}/${patient.vitals.bpDiastolic} mmHg`
                      : "—"}
                  </p>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl">
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Heart Rate</p>
                  <p className="text-lg font-black text-slate-700">
                    {patient?.vitals?.heartRate ? `${patient.vitals.heartRate} bpm` : "—"}
                  </p>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl">
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Temperature</p>
                  <p className="text-lg font-black text-slate-700">
                    {patient?.vitals?.temperature ? `${patient.vitals.temperature}°C` : "—"}
                  </p>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl">
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Weight</p>
                  <p className="text-lg font-black text-slate-700">
                    {weightKg} kg
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: SOAP */}
        {step === "soap" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
                <h3 className="font-bold text-slate-700">SOAP Summary</h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => setSoapEditMode(!soapEditMode)}
                    className="px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-slate-100 rounded-lg flex items-center gap-1"
                  >
                    <Edit3 size={14} />
                    {soapEditMode ? "View" : "Edit"}
                  </button>
                  <button
                    onClick={generateSoap}
                    disabled={soapLoading}
                    className="px-3 py-1.5 text-sm font-semibold text-blue-600 hover:bg-blue-50 rounded-lg"
                  >
                    {soapLoading ? "Generating…" : "Regenerate"}
                  </button>
                </div>
              </div>
              <div className="p-6 space-y-4">
                {soapLoading ? (
                  <p className="text-slate-500">Generating SOAP notes…</p>
                ) : soap ? (
                  ["S", "O", "A", "P"].map((key) => (
                    <div key={key}>
                      <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                        {key === "S" && "Subjective"}
                        {key === "O" && "Objective"}
                        {key === "A" && "Assessment"}
                        {key === "P" && "Plan"}
                      </label>
                      {soapEditMode ? (
                        <textarea
                          className="w-full min-h-[80px] p-3 border border-slate-200 rounded-lg text-slate-700"
                          value={editedSoap[key] || ""}
                          onChange={(e) =>
                            setEditedSoap((prev) => ({ ...prev, [key]: e.target.value }))
                          }
                        />
                      ) : (
                        <div className="p-3 bg-slate-50 rounded-lg text-slate-700 whitespace-pre-wrap">
                          {(soapEditMode ? editedSoap[key] : soap[key]) || "—"}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500">No SOAP data yet. Click Regenerate.</p>
                )}
              </div>
              <div className="px-6 py-4 border-t border-slate-100 flex justify-end">
                <button
                  onClick={handleConfirmSoap}
                  disabled={!soap}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-bold rounded-lg flex items-center gap-2"
                >
                  <Check size={18} />
                  Confirm Summary
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Prescription */}
        {step === "prescription" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h3 className="font-bold text-slate-700 mb-4 flex items-center gap-2">
                <Pill size={20} className="text-blue-500" />
                Medication Prescription
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4">
                <input
                  type="text"
                  placeholder="Drug name"
                  className="col-span-2 px-3 py-2 border border-slate-200 rounded-lg"
                  value={newRx.drug_name}
                  onChange={(e) => setNewRx((p) => ({ ...p, drug_name: e.target.value }))}
                />
                <input
                  type="number"
                  placeholder="Dose mg/day"
                  className="px-3 py-2 border border-slate-200 rounded-lg"
                  value={newRx.dose_mg}
                  onChange={(e) => setNewRx((p) => ({ ...p, dose_mg: e.target.value }))}
                />
                <input
                  type="number"
                  placeholder="Freq/day"
                  className="px-3 py-2 border border-slate-200 rounded-lg"
                  value={newRx.frequency}
                  onChange={(e) => setNewRx((p) => ({ ...p, frequency: e.target.value }))}
                />
                <input
                  type="number"
                  placeholder="Days"
                  className="px-3 py-2 border border-slate-200 rounded-lg"
                  value={newRx.duration_days}
                  onChange={(e) => setNewRx((p) => ({ ...p, duration_days: e.target.value }))}
                />
              </div>
              <div className="flex flex-wrap gap-2 mb-4 items-center">
                <button
                  onClick={runDoseCheck}
                  disabled={doseCheckLoading}
                  className="px-4 py-2 bg-slate-800 text-white font-semibold rounded-lg hover:bg-slate-700"
                >
                  {doseCheckLoading ? "Checking…" : "Check Dose Safety"}
                </button>
                <button
                  onClick={() => addPrescription(true)}
                  disabled={!newRx.drug_name.trim() || !newRx.dose_mg || !newRx.frequency}
                  className="px-4 py-2 bg-slate-200 text-slate-700 font-semibold rounded-lg hover:bg-slate-300 flex items-center gap-1"
                  title="Add prescription without dose safety check (e.g. drug not in formulary)"
                >
                  <Plus size={16} />
                  Add without check
                </button>
                {doseCheckResult && (
                  <>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-bold flex items-center gap-1 ${
                        doseCheckResult.safe
                          ? "bg-green-100 text-green-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {doseCheckResult.safe ? (
                        <Check size={16} />
                      ) : (
                        <AlertTriangle size={16} />
                      )}
                      {doseCheckResult.safe ? "Safe" : "Warning"}
                    </span>
                    {!doseCheckResult.safe && doseCheckResult.warnings?.length > 0 && (
                      <span className="text-sm text-amber-700">
                        {doseCheckResult.warnings.join(" ")}
                      </span>
                    )}
                    <button
                      onClick={() => addPrescription(false)}
                      className="px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 flex items-center gap-1"
                    >
                      <Plus size={16} />
                      Add {doseCheckResult.safe ? "" : "(Override)"}
                    </button>
                    {!doseCheckResult.safe && (
                      <input
                        type="text"
                        placeholder="Override reason"
                        className="px-3 py-2 border border-slate-200 rounded-lg w-48"
                        value={overrideReason}
                        onChange={(e) => setOverrideReason(e.target.value)}
                      />
                    )}
                  </>
                )}
              </div>

              {prescriptions.length > 0 && (
                <div className="mt-6 border-t border-slate-200 pt-4">
                  <p className="text-xs font-bold text-slate-500 uppercase mb-2">Added prescriptions</p>
                  <ul className="space-y-2">
                    {prescriptions.map((p, idx) => (
                      <li
                        key={idx}
                        className="flex justify-between items-center py-2 px-3 bg-slate-50 rounded-lg"
                      >
                        <span>
                          <strong>{p.drug_name}</strong> — {p.dose_mg_per_day} mg/day, {p.frequency}x/day
                          {p.duration_days && ` × ${p.duration_days} days`}
                          {!p.is_safe && (
                            <span className="ml-2 text-amber-600 text-xs">(Override)</span>
                          )}
                        </span>
                        <button
                          onClick={() => removePrescription(idx)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-6 flex justify-between items-end">
                <textarea
                  placeholder="Doctor notes (optional)"
                  className="flex-1 mr-4 min-h-[60px] p-3 border border-slate-200 rounded-lg"
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                />
                <button
                  onClick={handleSaveVisit}
                  disabled={saveLoading}
                  className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg flex items-center gap-2 shrink-0"
                >
                  <Save size={20} />
                  {saveLoading ? "Saving…" : "Save Visit"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConsultationRoom;
