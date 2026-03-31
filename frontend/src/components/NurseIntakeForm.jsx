
import { useState } from "react";
import VoiceButton from "./VoiceButton";

export default function NurseIntakeForm({ onSubmit = () => {} }) {
  const [formData, setFormData] = useState({
    firstName: "",
    middleName: "",
    lastName: "",
    age: "",
    sex: "",
    weight: "",
    temperature: "",
    respiratoryRate: "",
    pulse: "",
    symptoms: "",
  });

  const [isEstimated, setIsEstimated] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const runTriage = () => {
    const temp = Number(formData.temperature);
    const rr = Number(formData.respiratoryRate);
    const symptoms = formData.symptoms.toLowerCase();

    let level = "GREEN";
    let color = "green";
    let reasons = [];

    if (temp >= 39) {
      level = "RED";
      color = "red";
      reasons.push("Very high fever detected");
    }

    if (rr >= 30) {
      level = "RED";
      color = "red";
      reasons.push("High respiratory rate");
    }

    if (symptoms.includes("difficulty breathing")) {
      level = "RED";
      color = "red";
      reasons.push("Difficulty breathing reported");
    }

    if (level !== "RED" && temp >= 38) {
      level = "YELLOW";
      color = "yellow";
      reasons.push("Fever detected");
    }

    if (reasons.length === 0) {
      reasons.push("Vitals within normal range");
    }

    onSubmit({ 
      ...formData,
      level,
      color,
      reasons,
});
  };

  return (
  <div className="bg-white rounded-lg shadow p-4 sm:p-6 w-full">
    <h2 className="text-lg sm:text-xl font-semibold mb-6">
      Nurse Intake Form
    </h2>

    {/* Name Section */}
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium mb-1">
          First Name
        </label>
        <input
          type="text"
          name="firstName"
          value={formData.firstName}
          onChange={handleChange}
          className="w-full border rounded px-3 py-2"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">
          Middle Name
        </label>
        <input
          type="text"
          name="middleName"
          value={formData.middleName}
          onChange={handleChange}
          className="w-full border rounded px-3 py-2"
        />
      </div>

      <div className="sm:col-span-2">
        <label className="block text-sm font-medium mb-1">
          Last Name
        </label>
        <input
          type="text"
          name="lastName"
          value={formData.lastName}
          onChange={handleChange}
          className="w-full border rounded px-3 py-2"
        />
      </div>
    </div>

    {/* Age + Sex */}
    <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium mb-1">
          Age
        </label>
        <input
          type="number"
          name="age"
          value={formData.age}
          onChange={handleChange}
          className="w-full border rounded px-3 py-2"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">
          Sex
        </label>
        <div className="flex gap-6">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="sex"
              value="male"
              checked={formData.sex === "male"}
              onChange={handleChange}
              className="accent-teal-600"
            />
            Male
          </label>

          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="sex"
              value="female"
              checked={formData.sex === "female"}
              onChange={handleChange}
              className="accent-teal-600"
            />
            Female
          </label>
        </div>
      </div>
    </div>

    {/* Weight */}
    <div className="mt-6 flex flex-col sm:flex-row sm:items-center gap-4">
      <div className="flex-1">
        <label className="block text-sm font-medium mb-1">
          Weight
        </label>
        <input
          type="number"
          name="weight"
          value={formData.weight}
          onChange={handleChange}
          className="w-full border rounded px-3 py-2"
        />
      </div>

      <button
        type="button"
        onClick={() => setIsEstimated(!isEstimated)}
        className="flex items-center gap-2 mt-2 sm:mt-6"
      >
        <div
          className={`w-10 h-5 rounded-full relative transition-colors ${
            isEstimated ? "bg-teal-500" : "bg-gray-300"
          }`}
        >
          <div
            className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-all ${
              isEstimated ? "right-1" : "left-1"
            }`}
          ></div>
        </div>
        <span className="text-sm">Estimated</span>
      </button>
    </div>

    {/* Vital Signs */}
    <div className="mt-8">
      <h3 className="font-semibold mb-4">Vital Signs</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm mb-1">
            Temperature (°C)
          </label>
          <input
            type="number"
            name="temperature"
            value={formData.temperature}
            onChange={handleChange}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm mb-1">
            Respiratory Rate (breaths/min)
          </label>
          <input
            type="number"
            name="respiratoryRate"
            value={formData.respiratoryRate}
            onChange={handleChange}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div className="sm:col-span-2">
          <label className="block text-sm mb-1">
            Pulse (bpm)
          </label>
          <input
            type="number"
            name="pulse"
            value={formData.pulse}
            onChange={handleChange}
            className="w-full border rounded px-3 py-2"
          />
        </div>
      </div>
    </div>

    {/* Symptoms */}
    <div className="mt-6">
      <label className="block text-sm font-medium mb-1">
        Symptoms
      </label>
      <textarea
        rows="3"
        name="symptoms"
        value={formData.symptoms}
        onChange={handleChange}
        placeholder="Enter symptoms..."
        className="w-full border rounded px-3 py-2"
      />
    </div>

    {/* Voice */}
    <div className="mt-4">
      <VoiceButton />
    </div>

    {/* Submit */}
    <button
      type="button"
      onClick={runTriage}
      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded mt-6 transition"
    >
      Submit Intake
    </button>
  </div>
);

}
