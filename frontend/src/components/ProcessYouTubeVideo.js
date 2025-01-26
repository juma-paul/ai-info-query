import axios from "axios";
import { useState } from "react";
import FormMessage from "./FormMessage";

const ProcessYouTubeVideo = () => {
    const [videoUrl, setVideoUrl] = useState("");
    const [isLoading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError("");
        setSuccess("");

        if (!videoUrl) {
            setError("Please enter a YouTube URL.");
            setLoading(false);
            return;
        }

        try {
            const response = await axios.post("http://127.0.0.1:5000/document/process-video", {
                video_url: videoUrl,
            });

            setSuccess(response.data?.message || "Video processed successfully.");
            setTimeout(() => setSuccess(""), 3000);
            setVideoUrl("");

        } catch (err) {
            console.error("Processing Error:", err);
            const errorMessage = err.response?.data?.error || "An error occurred while processing the video.";
            setError(errorMessage);
            setTimeout(() => setError(""), 3000);
        } finally {
            setLoading(false);
        }
    };

    return (

        <div className="form-container">
            <form onSubmit={handleSubmit}>
                <input
                type="url"
                placeholder="Enter YouTube video URL"
                value={videoUrl}
                onChange={(event) => setVideoUrl(event.target.value)}
                className="form-input"
                />
                <button type="submit" disabled={isLoading || !videoUrl} className="form-button">
                {isLoading ? "Processing..." : "Process Video"}
                </button>
                
                <FormMessage error={error} success={success} />

            </form>
        </div>

    )
}

export default ProcessYouTubeVideo;
