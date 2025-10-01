import UploadForm from "./components/UploadForm";

export default function App() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="max-w-2xl w-full bg-white p-8 rounded-2xl shadow-lg">
        <h1 className="text-2xl font-bold mb-4 text-center">
          AI Video Creator
        </h1>
        <UploadForm />
      </div>
    </div>
  );
}
