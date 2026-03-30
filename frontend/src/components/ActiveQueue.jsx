// import { useEffect, useState } from "react"

// function ActiveQueue() {
//   const [queue, setQueue] = useState([])

//   useEffect(() => {
//     fetch("http://localhost:8000/queue")
//       .then(res => res.json())
//       .then(data => setQueue(data))
//   }, [])

//   const sendToDoctor = (id) => {
//     fetch(`http://localhost:8000/send_to_doctor/${id}`, {
//       method: "PUT"
//     })
//       .then(res => res.json())
//       .then(() => {
//         alert("Sent to doctor")
//       })
//   }

//   return (
//     <div>
//       {queue.map((patient) => (
//         <div key={patient.id} className="p-4 border mb-2 rounded">
//           <p><strong>Name:</strong> {patient.first_name}</p>
//           <p><strong>Priority:</strong> {patient.priority_level}</p>

//           <button
//             onClick={() => sendToDoctor(patient.id)}
//             className="mt-2 bg-red-500 text-white px-4 py-1 rounded"
//           >
//             Send to Doctor
//           </button>
//         </div>
//       ))}
//     </div>
//   )
// }

// export default ActiveQueue


// import { useEffect, useState } from "react";

// function ActiveQueue() {
//   const [queue, setQueue] = useState([]);

//   useEffect(() => {
//     // Mock data instead of fetch
//     setQueue([
//       { id: 1, first_name: "Patient A", priority_level: "High" },
//       { id: 2, first_name: "Patient B", priority_level: "Medium" },
//       { id: 3, first_name: "Patient C", priority_level: "Low" },
//     ]);
//   }, []);

//   const sendToDoctor = (id) => {
//     alert(`Sent patient ${id} to doctor`);
//   };

//   return (
//     <div>
//       {queue.map((patient) => (
//         <div key={patient.id} className="p-4 border mb-2 rounded">
//           <p><strong>Name:</strong> {patient.first_name}</p>
//           <p><strong>Priority:</strong> {patient.priority_level}</p>

//           <button
//             onClick={() => sendToDoctor(patient.id)}
//             className="mt-2 bg-red-500 text-white px-4 py-1 rounded"
//           >
//             Send to Doctor
//           </button>
//         </div>
//       ))}
//     </div>
//   );
// }

// export default ActiveQueue;
export default function ActiveQueue({ patients, onSendToDoctor }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Active Queue</h2>

      {patients.length === 0 && (
        <p className="text-gray-500">No patients yet</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {patients.map((patient) => (
          <div
            key={patient.id}
            className="border rounded p-4 flex flex-col justify-between"
          >
            <div>
              <p className="text-sm sm:text-base">
                <strong>Name:</strong>{" "}
                {patient.firstName} {patient.middleName} {patient.lastName}
              </p>

              <p className="text-sm sm:text-base mt-1">
                <strong>Priority:</strong>{" "}
                <span className="font-bold">{patient.level}</span>
              </p>
            </div>

            <button
              onClick={() => onSendToDoctor(patient.id)}
              className="bg-red-500 text-white px-3 py-2 rounded mt-3 text-sm sm:text-base hover:bg-red-600 transition"
            >
              Send to Doctor
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}