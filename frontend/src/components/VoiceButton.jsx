// export default function VoiceButton() {
//   return (
//     <button
//       className="border p-2 rounded w-full"
//       onClick={() => alert("Voice input demo")}
//     >
//       🎤 Voice Input
//     </button>
//   );
// }
export default function VoiceButton({ onResult }) {
  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };
  };

  return (
    <button onClick={startListening}>
      🎤 Voice Input
    </button>
  );
}
