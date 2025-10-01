import { useState } from "react";
import axios from "axios";

export default function UploadForm() {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [references, setReferences] = useState([]);
  const [loading, setLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please upload a video file.");
      return;
    }

    setLoading(true);
    setError(null);
    setVideoUrl("");
    const formData = new FormData();
    formData.append("video", file);
    formData.append("prompt", prompt);
    if (references && references.length) {
      for (const f of references) formData.append("references", f);
    }

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/process",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setVideoUrl("http://127.0.0.1:8000" + res.data.video_url);
    } catch (err) {
      console.error(err);
      const detail =
        err?.response?.data?.detail || err?.message || "Unknown error";
      setError(`Error processing video: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Upload Video</label>
          <input
            type="file"
            name="video"
            accept="video/*"
            required
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium">
            Upload Reference Images
          </label>
          <input
            type="file"
            name="references"
            accept="image/*"
            multiple
            onChange={(e) => setReferences(Array.from(e.target.files || []))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Prompt</label>
          <textarea
            name="prompt"
            rows="3"
            className="w-full border rounded p-2"
            placeholder="E.g. Create a motivational video about John..."
            required
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400"
          disabled={loading}
        >
          {loading ? "Processing..." : "Process"}
        </button>
      </form>

      {error && (
        <div className="mt-4 text-.red-500">
          <p>{error}</p>
        </div>
      )}

      {videoUrl && (
        <div className="mt-4">
          <h2 className="font-semibold">Your Video:</h2>
          <video src={videoUrl} controls className="w-full mt-2 rounded" />
        </div>
      )}
    </div>
  );
}
