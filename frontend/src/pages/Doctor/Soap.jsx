import React from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  ClipboardCheck,
  FileText,
  FlaskConical,
  MessageSquareQuote,
} from "lucide-react";

const Soap = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { patientId, sessionId } = useParams();

  const patient = location.state?.patient || {
    name: "Selected Patient",
    patientId,
    sessionId,
  };
  const transcript = Array.isArray(location.state?.transcript)
    ? location.state.transcript
    : [];

  const symptomSummary =
    transcript.length > 0
      ? transcript
          .slice(0, 5)
          .map((item) => item.text)
          .join(" ")
      : "No transcript snippets yet. Start and stop recording to generate consultation summary context.";

  return (
    <div className="flex flex-col flex-1 p-4 overflow-auto gap-6">
      <header className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-2">
          <ClipboardCheck className="text-blue-600" size={28} />
          SOAP Summary Review
        </h1>
        <div className="text-gray-600 mt-1 space-y-1">
          <p>
            Patient:{" "}
            <span className="font-semibold">
              {patient?.name || "Not selected"}
            </span>
          </p>
          <p className="text-sm">
            Patient ID:{" "}
            <span className="font-mono">
              {patient?.patientId || patientId || "N/A"}
            </span>
            <span className="mx-2">•</span>
            Session ID:{" "}
            <span className="font-mono">
              {patient?.sessionId || sessionId || "N/A"}
            </span>
          </p>
        </div>
      </header>

      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <FlaskConical size={18} className="text-emerald-600" />
          Model-ready SOAP Sections
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SoapCard
            title="Subjective"
            hint="Patient-reported symptoms and concerns from this session."
          />
          <SoapCard
            title="Objective"
            hint="Observed findings and measurable clinical indicators."
          />
          <SoapCard
            title="Assessment"
            hint="Clinical interpretation after consultation."
          />
          <SoapCard
            title="Plan"
            hint="Treatment, tests, prescriptions, and follow-up actions."
          />
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <MessageSquareQuote size={18} className="text-violet-600" />
          Symptom Summary (Session Context)
        </h2>
        <div className="rounded-lg border border-violet-200 bg-violet-50 p-4 text-sm text-violet-900 leading-relaxed">
          {symptomSummary}
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <FileText size={18} className="text-blue-600" />
          Transcript Preview
        </h2>

        <div className="rounded-lg border border-gray-200 p-4 bg-gray-50 max-h-80 overflow-y-auto space-y-2">
          {transcript.length ? (
            transcript.map((item, idx) => (
              <p key={item.id || idx} className="text-sm text-gray-700">
                {item.text}
              </p>
            ))
          ) : (
            <p className="text-sm text-gray-500">
              No transcript has been passed yet. Start consultation recording
              first.
            </p>
          )}
        </div>

        <div className="mt-4">
          <button
            onClick={() =>
              navigate(
                `/doctors-dashboard/recording-session/${patient?.patientId || patientId}/${patient?.sessionId || sessionId}`,
                {
                  state: { patient },
                },
              )
            }
            className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-black"
          >
            Back to Recording Session
          </button>
        </div>
      </section>
    </div>
  );
};

const SoapCard = ({ title, hint }) => (
  <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
    <h3 className="font-semibold text-gray-800">{title}</h3>
    <p className="text-sm text-gray-500 mt-1">{hint}</p>
  </div>
);

export default Soap;
