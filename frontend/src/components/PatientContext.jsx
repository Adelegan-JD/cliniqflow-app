import { createContext, useState, useContext } from "react";

const PatientContext = createContext();

export function PatientProvider({ children }) {
  const [patients, setPatients] = useState([]);

  const addPatient = (patientData) => {
    const newPatient = {
      id: Date.now(),
      status: "waiting",
      date: new Date().toLocaleDateString(),
      ...patientData,
    };
    setPatients((prev) => [...prev, newPatient]);
  };

  const sendToDoctor = (id) => {
    setPatients((prev) =>
      prev.map((p) =>
        p.id === id ? { ...p, status: "sent" } : p
      )
    );
  };

  return (
    <PatientContext.Provider value={{ patients, addPatient, sendToDoctor }}>
      {children}
    </PatientContext.Provider>
  );
}

export const usePatients = () => useContext(PatientContext);