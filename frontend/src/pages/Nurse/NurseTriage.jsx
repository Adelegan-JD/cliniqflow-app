import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import TriageForm from "../../components/TriageForm";
import { api } from "../../utils/api";
import { supabase } from "../../utils/supabaseClient";

const NurseTriage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { patientId } = useParams();
  const [patient, setPatient] = useState(location.state?.patient || null);

  useEffect(() => {
    if (!patient) {
      const savedPatient = sessionStorage.getItem("nurseTriagePatient");
      if (savedPatient) {
        const parsed = JSON.parse(savedPatient);
        if (parsed?.patientId === patientId) {
          setPatient(parsed);
          return;
        }
      }
      navigate("/nurse-dashboard", { replace: true });
    }
  }, [patient, patientId, navigate]);

  useEffect(() => {
    if (patient) {
      sessionStorage.setItem("nurseTriagePatient", JSON.stringify(patient));
    }
    return () => {
      sessionStorage.removeItem("nurseTriagePatient");
    };
  }, [patient]);

  const handleCancel = () => {
    navigate("/nurse-dashboard");
  };

  const handleSave = async (id, vitals, triageStatus) => {
    const payload = {
      visit_id: patient.visit_id || patient.visitId || null,
      patient_id: patient.patientId || patient.patient_id || id,
      vitals,
      urgency_level: triageStatus || "normal",
    };

    try {
      let triagedPatient;

      if (import.meta.env.CLINIQ_AUTH_MODE === "supabase") {
        let updateData, updateError;

        // Try both column naming variants depending on your schema
        ({ data: updateData, error: updateError } = await supabase
          .from("nurse_triage_queue")
          .update({ status: "triaged", urgency: payload.triageStatus })
          .eq("patientId", payload.patientId)
          .select("*")
          .single());

        if (updateError) {
          ({ data: updateData, error: updateError } = await supabase
            .from("nurse_triage_queue")
            .update({ status: "triaged", urgency: payload.triageStatus })
            .eq("patient_id", payload.patientId)
            .select("*")
            .single());
        }

        if (updateError) throw updateError;

        const { error: recordError } = await supabase
          .from("nurse_triage_records")
          .insert([
            {
              patientId: payload.patientId,
              patient_id: payload.patientId,
              name: patient.name,
              age: patient.age,
              sex: patient.sex,
              urgencyLevel: payload.triageStatus,
              vitals,
              triagedAt: new Date().toISOString(),
            },
          ]);

        if (recordError) throw recordError;

        triagedPatient = {
          ...patient,
          status: "triaged",
          urgency: payload.triageStatus,
          triageStatus: payload.triageStatus,
          vitals,
          triagedAt: new Date().toISOString(),
        };
      } else {
        const result = await api.post("/nurse/triage", payload);
        triagedPatient = {
          ...patient,
          status: "triaged",
          urgency: result.patient?.urgency || payload.urgency_level,
          triageStatus: payload.urgency_level,
          vitals,
          triagedAt: result.record?.triagedAt || new Date().toISOString(),
        };
      }

      navigate("/nurse-dashboard", {
        state: { triagedPatient },
        replace: true,
      });
    } catch (error) {
      console.error("Triage save failed", error);
      alert(`Failed to save triage. Try again. ${error?.message || ""}`);
    }
  };

  if (!patient) {
    return (
      <div className="p-8 text-center text-slate-600">
        Loading patient data... Redirecting to nurse dashboard.
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-8">
      <TriageForm
        patient={patient}
        onCancel={handleCancel}
        onSave={handleSave}
        initialVitals={patient.vitals}
      />
    </div>
  );
};

export default NurseTriage;
