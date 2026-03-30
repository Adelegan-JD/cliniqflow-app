import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { ClipboardList, FileText, Stethoscope } from "lucide-react";

const queuePatients = [
  {
    patientId: "PT-001-AB",
    sessionId: "VS-2026-0001",
    name: "Amina Bello",
    age: 34,
    sex: "Female",
    status: "awaiting_consultation",
  },
  {
    patientId: "PT-002-TO",
    sessionId: "VS-2026-0002",
    name: "Tunde Okafor",
    age: 41,
    sex: "Male",
    status: "awaiting_triage",
  },
  {
    patientId: "PT-003-GN",
    sessionId: "VS-2026-0003",
    name: "Grace Nwosu",
    age: 27,
    sex: "Female",
    status: "visit_ended",
  },
  {
    patientId: "PT-004-IS",
    sessionId: "VS-2026-0004",
    name: "Ibrahim Sani",
    age: 58,
    sex: "Male",
    status: "awaiting_consultation",
  },
  {
    patientId: "PT-005-CE",
    sessionId: "VS-2026-0005",
    name: "Chioma Eze",
    age: 22,
    sex: "Female",
    status: "awaiting_triage",
  },
  {
    patientId: "PT-006-KA",
    sessionId: "VS-2026-0006",
    name: "Kunle Adeyemi",
    age: 46,
    sex: "Male",
    status: "visit_ended",
  },
];

const statusPriority = {
  awaiting_consultation: 1,
  awaiting_triage: 2,
  visit_ended: 3,
};

const statusMeta = {
  awaiting_consultation: {
    label: "Ready for Consultation",
    badge: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  awaiting_triage: {
    label: "Awaiting Triage",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
  },
  visit_ended: {
    label: "Visit Ended",
    badge: "bg-gray-100 text-gray-700 border-gray-200",
  },
};

const PatientsQueue = () => {
  const navigate = useNavigate();

  const sortedPatients = useMemo(() => {
    return [...queuePatients].sort(
      (a, b) => statusPriority[a.status] - statusPriority[b.status],
    );
  }, []);

  return (
    <div className="flex flex-col flex-1 p-4 overflow-auto">
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-2">
          <ClipboardList className="text-blue-600" size={28} />
          Patient Queue
        </h1>
        <p className="text-gray-600 mt-1">
          Patients are automatically prioritized by care readiness:
          consultation, triage, then completed visits.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex flex-wrap items-center gap-3">
          <h2 className="text-xl font-semibold flex items-center gap-2 mr-auto">
            <Stethoscope size={20} className="text-gray-700" />
            Queue Overview
          </h2>
          <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            Total Patients: {sortedPatients.length}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-[820px]">
            <thead className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider">
              <tr>
                <th className="px-6 py-4 font-medium">Name</th>
                <th className="px-6 py-4 font-medium">Patient ID</th>
                <th className="px-6 py-4 font-medium">Session ID</th>
                <th className="px-6 py-4 font-medium">Age</th>
                <th className="px-6 py-4 font-medium">Sex</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Records</th>
                <th className="px-6 py-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sortedPatients.map((patient) => {
                const meta = statusMeta[patient.status];
                const triageCompleted =
                  patient.status === "awaiting_consultation";
                const awaitingTriage = patient.status === "awaiting_triage";
                const visitEnded = patient.status === "visit_ended";

                return (
                  <tr
                    key={`${patient.patientId}-${patient.sessionId}`}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {patient.name}
                    </td>
                    <td className="px-6 py-4 text-gray-700 font-mono text-xs">
                      {patient.patientId}
                    </td>
                    <td className="px-6 py-4 text-gray-700 font-mono text-xs">
                      {patient.sessionId}
                    </td>
                    <td className="px-6 py-4 text-gray-700">{patient.age}</td>
                    <td className="px-6 py-4 text-gray-700">{patient.sex}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${meta.badge}`}
                      >
                        {meta.label}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <a
                        href={`#records-${patient.patientId}-${patient.sessionId}`}
                        className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium"
                      >
                        <FileText size={16} />
                        Records
                      </a>
                    </td>
                    <td className="px-6 py-4">
                      {triageCompleted ? (
                        <button
                          onClick={() =>
                            navigate(
                              `/doctors-dashboard/recording-session/${patient.patientId}/${patient.sessionId}`,
                              {
                                state: { patient },
                              },
                            )
                          }
                          className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition-colors"
                        >
                          Start Consultation
                        </button>
                      ) : awaitingTriage ? (
                        <button
                          disabled
                          className="px-4 py-2 rounded-lg bg-gray-200 text-gray-500 text-sm font-semibold cursor-not-allowed"
                        >
                          Start Consultation
                        </button>
                      ) : visitEnded ? (
                        <span className="text-sm text-gray-500 font-semibold">
                          Visit Ended
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400 font-medium">
                          Not Available
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PatientsQueue;
