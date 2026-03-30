// export default function TriageResult({ result }) {
//   if (!result) {
//     return (
//       <div className="p-6 bg-white shadow rounded text-gray-400 text-center">
//         Triage result will appear here
//       </div>
//     );
//   }

//   const colors = {
//     RED: "bg-red-600",
//     YELLOW: "bg-yellow-500",
//     GREEN: "bg-green-600",
//   };

//   return (
//     <div className={`p-6 text-white rounded ${colors[result.level]}`}>
//       <h2 className="text-2xl font-bold mb-3">{result.level}</h2>
//       <ul className="list-disc ml-5">
//         {result.reasons.map((r, i) => (
//           <li key={i}>{r}</li>
//         ))}
//       </ul>

//       <button className="mt-4 bg-black px-4 py-2 rounded">
//         Send to Doctor
//       </button>
//     </div>
//   );
// }
export default function TriageResult({ result, onSendToDoctor }) {
  if (!result) {
    return (
      <div className="p-6 bg-white shadow rounded text-gray-400 text-center">
        Triage result 
      </div>
    );
  }

  const colors = {
    RED: "bg-red-600",
    YELLOW: "bg-yellow-500",
    GREEN: "bg-green-600",
  };

  return (
    <div className={`p-6 text-white rounded ${colors[result.level]}`}>
      <h2 className="text-2xl font-bold mb-3">{result.level}</h2>
      <ul className="list-disc ml-5">
        {result.reasons.map((r, i) => (
          <li key={i}>{r}</li>
        ))}
      </ul>

      <button
        onClick={() => onSendToDoctor(result.id)}   
        className="mt-4 bg-black px-4 py-2 rounded hover:bg-gray-800 transition"
      >
        Send to Doctor
      </button>
    </div>
  );
}