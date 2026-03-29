import React, { useState } from "react";
import { api } from "../utils/api";
import { User, Activity, ArrowLeft, CheckCircle, Clock, AlertTriangle, Info, Loader2 } from "lucide-react";

export default function TriageForm({ patient, onCancel, onSave, initialVitals }) {
  const [vitals, setVitals] = useState({
    temperature: initialVitals?.temperature || "",
    bpSystolic: initialVitals?.bpSystolic || "",
    bpDiastolic: initialVitals?.bpDiastolic || "",
    heartRate: initialVitals?.heartRate || "",
    respiratoryRate: initialVitals?.respiratoryRate || "",
    oxygenSaturation: initialVitals?.oxygenSaturation || "",
    weight: initialVitals?.weight || "",
    height: initialVitals?.height || "",
    bmi: initialVitals?.bmi || "",
  });

  const [triageStatus, setTriageStatus] = useState(null); // 'emergency' | 'urgent' | 'normal' | null
  const [triageMethod, setTriageMethod] = useState(null); // 'rule_based' | 'llm' | null
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const calculateBMI = (weight, height) => {
    if (weight && height) {
      const heightInMeters = height / 100;
      return (weight / (heightInMeters * heightInMeters)).toFixed(1);
    }
    return "";
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    let updatedVitals = { ...vitals, [name]: value };

    if (name === "weight" || name === "height") {
      updatedVitals.bmi = calculateBMI(
        name === "weight" ? value : updatedVitals.weight,
        name === "height" ? value : updatedVitals.height
      );
    }

    setVitals(updatedVitals);
    // Clear previous status if they change vitals after evaluation
    if (triageStatus) setTriageStatus(null);
    if (triageMethod) setTriageMethod(null);
    if (errorMessage) setErrorMessage("");
  };

const handleEvaluate = async () => {
  // Basic validation to ensure essential fields for evaluation aren't empty
  if (!vitals.bpSystolic || !vitals.bpDiastolic || !vitals.respiratoryRate) {
    setErrorMessage("Please fill in blood pressure and respiratory rate to evaluate.");
    return;
  }

  setIsEvaluating(true);
  setErrorMessage("");
  setTriageStatus(null);
  setTriageMethod(null);

  const ageStr = patient.age != null && patient.age !== ""
    ? (typeof patient.age === "number" ? `${patient.age} years` : String(patient.age))
    : null;

  const payload = {
    patient_age: ageStr || null,
    patient_sex: patient.gender ? patient.gender.toLowerCase() : "unknown",
    temperature: vitals.temperature ? parseFloat(vitals.temperature) : null,
    bp_systolic: vitals.bpSystolic ? parseInt(vitals.bpSystolic, 10) : null,
    bp_diastolic: vitals.bpDiastolic ? parseInt(vitals.bpDiastolic, 10) : null,
    heart_rate: vitals.heartRate ? parseInt(vitals.heartRate, 10) : null,
    respiratory_rate: vitals.respiratoryRate ? parseInt(vitals.respiratoryRate, 10) : null,
    oxygen_saturation: vitals.oxygenSaturation ? parseFloat(vitals.oxygenSaturation) : null,
    weight_kg: vitals.weight ? parseFloat(vitals.weight) : null,
    height_cm: vitals.height ? parseFloat(vitals.height) : null,
  };

  try {
    // Call backend using your api.js helper
    const data = await api.post("/nlp/vitals-urgency", payload);

    setTriageStatus(data.urgency_level);
    setTriageMethod(data.method || null);

  } catch (error) {
    console.error("Error fetching urgency level:", error);
    setErrorMessage("Failed to evaluate vitals. Please try again.");
  } finally {
    setIsEvaluating(false);
  }
};

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(patient.id, vitals, triageStatus);
  };

  const renderAlertBanner = () => {
    if (!triageStatus) return null;

    const methodBadge = triageMethod === "llm" ? (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${triageStatus === "normal" ? "bg-green-200/80 text-green-800" : "bg-white/20"}`}>AI-assisted</span>
    ) : triageMethod === "rule_based" ? (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${triageStatus === "normal" ? "bg-green-200/80 text-green-800" : "bg-white/20"}`}>Rule-based</span>
    ) : null;

    if (triageStatus === "emergency") {
      return (
        <div className="mb-6 bg-red-600 text-white p-4 rounded-xl shadow-md flex items-start gap-4 animate-in fade-in slide-in-from-top-2 duration-300">
          <AlertTriangle size={28} className="shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-black text-xl tracking-wide uppercase">Emergency</h3>
              {methodBadge}
            </div>
            <p className="font-medium text-red-50">Patient requires immediate medical attention.</p>
          </div>
        </div>
      );
    }

    if (triageStatus === "urgent") {
      return (
        <div className="mb-6 bg-yellow-100 border border-yellow-300 text-yellow-800 p-4 rounded-xl shadow-sm flex items-start gap-4 animate-in fade-in slide-in-from-top-2 duration-300">
          <AlertTriangle size={28} className="text-yellow-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-lg tracking-wide uppercase">Urgent</h3>
              {methodBadge}
            </div>
            <p className="font-medium text-yellow-700">Patient requires prompt medical attention.</p>
          </div>
        </div>
      );
    }

    if (triageStatus === "normal") {
      return (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-800 p-3 rounded-xl shadow-sm flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="bg-green-100 p-1.5 rounded-full shrink-0">
            <CheckCircle size={20} className="text-green-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-sm tracking-wide uppercase text-green-700">Normal</h3>
              {methodBadge}
            </div>
            <p className="text-sm text-green-600 font-medium">Vitals appear stable.</p>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="flex-1 overflow-auto p-4 sm:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Top Actions */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onCancel}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft size={16} />
            Back to Queue
          </button>
          <h2 className="text-xl font-bold text-slate-800">Triage Assessment</h2>
        </div>

        {/* Dynamic Alert Banner */}
        {renderAlertBanner()}

        {errorMessage && (
          <div className="mb-6 bg-slate-100 border-l-4 border-slate-400 text-slate-700 p-4 rounded-r-xl flex items-center gap-3">
            <Info size={20} className="text-slate-500" />
            <p className="text-sm font-medium">{errorMessage}</p>
          </div>
        )}

        {/* Patient Information Section (Read Only) */}
        <div className={`bg-white rounded-xl border shadow-sm overflow-hidden transition-colors duration-300 ${triageStatus === "emergency" ? "border-red-300 shadow-red-100" : "border-slate-200"}`}>
          <div className={`border-b px-6 py-4 flex items-center gap-2 transition-colors duration-300 ${triageStatus === "emergency" ? "bg-red-50 border-red-200" : "bg-slate-50 border-slate-200"}`}>
            <User className={triageStatus === "emergency" ? "text-red-500" : "text-blue-500"} size={20} />
            <h3 className={`font-semibold ${triageStatus === "emergency" ? "text-red-900" : "text-slate-800"}`}>Patient Information</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Name</p>
                <p className="font-semibold text-slate-800">{patient.name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Patient ID</p>
                <p className="font-mono text-slate-800">{patient.id}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Age / Gender</p>
                <p className="font-medium text-slate-800">
                  {patient.age} / {patient.gender}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Time of Arrival</p>
                <p className="font-medium text-slate-800 flex items-center gap-1">
                  <Clock size={14} className="text-slate-400" />
                  {patient.arrivalTime}
                </p>
              </div>
              {patient.contact && (
                <div className="lg:col-span-2">
                  <p className="text-sm font-medium text-slate-500 mb-1">Contact</p>
                  <p className="font-medium text-slate-800">{patient.contact}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Vitals Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="text-emerald-500" size={20} />
              <h3 className="font-semibold text-slate-800">Vital Signs Parameters</h3>
            </div>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Temperature (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  name="temperature"
                  required
                  value={vitals.temperature}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g. 36.5"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Blood Pressure (mmHg)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    name="bpSystolic"
                    required
                    value={vitals.bpSystolic}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-center"
                    placeholder="Sys"
                  />
                  <span className="text-slate-400 font-medium">/</span>
                  <input
                    type="number"
                    name="bpDiastolic"
                    required
                    value={vitals.bpDiastolic}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-center"
                    placeholder="Dia"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Heart Rate (bpm)
                </label>
                <input
                  type="number"
                  name="heartRate"
                  required
                  value={vitals.heartRate}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g. 72"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Respiratory Rate (/min)
                </label>
                <input
                  type="number"
                  name="respiratoryRate"
                  required
                  value={vitals.respiratoryRate}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g. 16"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  SpO2 (%) <span className="text-slate-400 font-normal">(optional)</span>
                </label>
                <input
                  type="number"
                  min="80"
                  max="100"
                  step="0.5"
                  name="oxygenSaturation"
                  value={vitals.oxygenSaturation}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g. 98"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Weight (kg)
                </label>
                <input
                  type="number"
                  step="0.1"
                  name="weight"
                  value={vitals.weight}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g. 70.0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Height (cm)
                </label>
                <input
                  type="number"
                  name="height"
                  value={vitals.height}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  placeholder="e.g. 175"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  BMI (Auto)
                </label>
                <input
                  type="text"
                  name="bmi"
                  readOnly
                  value={vitals.bmi}
                  className="w-full px-4 py-2 border border-slate-200 bg-slate-50 rounded-lg outline-none text-slate-500 font-bold"
                  placeholder="calculated..."
                />
              </div>
            </div>
          </div>

          <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex flex-col sm:flex-row justify-end items-center gap-3">
            <button
              type="button"
              onClick={handleEvaluate}
              disabled={isEvaluating}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2 bg-slate-100 text-slate-700 font-medium rounded-lg border border-slate-300 hover:bg-slate-200 hover:text-slate-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isEvaluating ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Evaluating...
                </>
              ) : (
                "Evaluate Vitals"
              )}
            </button>

            <button
              type="submit"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <CheckCircle size={18} />
              Complete Triage
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
