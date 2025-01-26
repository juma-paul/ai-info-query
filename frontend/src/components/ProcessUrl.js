import axios from "axios";
import { useState, useRef } from "react";
import FormMessage from "./FormMessage";

const ProcessUrl = () => {
  const [url, setUrl] = useState("");
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const inputRef = useRef(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    if (!url.trim()) {
      setError("Please enter a valid URL.");
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post("http://127.0.0.1:5000/document/process-url", {
        url,
      });

      setSuccess(response.data?.message || "URL processed successfully.");
      setTimeout(() => setSuccess(""), 3000);

      if (inputRef.current) {
        inputRef.current.value = "";
      }

      setUrl("");
      
    } catch (err) {
      console.error("Processing Error:", err);
      const errorMessage = err.response?.data?.error || "An error occurred.";
      setError(errorMessage);
      setTimeout(() => setError(""), 3000);

      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    
    <div className="form-container">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter website URL"
          onChange={(event) => setUrl(event.target.value)}
          ref={inputRef}
          className="form-input"
        />
        <button type="submit" disabled={isLoading || !url.trim()} className="form-button">
          {isLoading ? "Processing..." : "Process URL"}
        </button>
        
        <FormMessage error={error} success={success} />

      </form>
    </div>

  )
}

export default ProcessUrl
