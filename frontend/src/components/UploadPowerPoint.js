import axios from "axios";
import { useState, useRef } from "react";
import FormMessage from './FormMessage';

const UploadPowerPoint = () => {

    const [powerPoint, setPowerPoint] = useState(null)
    const [isLoading, setLoading] = useState(false)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState("")
    const inputRef = useRef(null)

    const handleSubmit = async (event) => {
        event.preventDefault()
        setLoading(true)
        setError("")
        setSuccess("")

        if (!powerPoint) {
            setError("Please select a file.")
            setLoading(false)
            return
        }

        const formData = new FormData()
        formData.append('powerPoint', powerPoint)

        try {
            const response = await axios.post("http://127.0.0.1:5000/document/upload-ppt",
                formData
            )

                setSuccess(response.data?.message || "URL processed successfully.")
                setTimeout(() => setSuccess(""), 3000)

                if (inputRef.current) {
                    inputRef.current.value = ""
                }

                setPowerPoint(null)

        } catch (err) {
            console.error("Upload Error:", err)
            const errorMessage = err.response?.data?.error || "An error occurred.";
            
            setError(errorMessage)
            setTimeout(() => setError(""), 3000)

            if (inputRef.current) {
                inputRef.current.value = ""
            }

        } finally {
            setLoading(false)
        }
    }

    return (

        <div className="form-container">
            <form onSubmit={handleSubmit}>
                <input
                type="file"
                onChange={(event) => {
                    const file = event.target.files[0];
                    setPowerPoint(file);
                }}
                accept=".ppt, .pptx"
                ref={inputRef}
                className="form-input"
                />
                <button type="submit" disabled={isLoading || !powerPoint} className="form-button">
                {isLoading ? "Loading ..." : "Upload PowerPoint"}
                </button>
                
                <FormMessage error={error} success={success} />

            </form>
        </div>

    )
}

export default UploadPowerPoint