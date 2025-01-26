import axios from "axios"
import { useState, useRef } from "react"
import FormMessage from "./FormMessage"

const UploadPdf = () => {

    const [pdf, setPdf] = useState(null)
    const [isLoading, setLoading] = useState(false)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState("")
    const fileInputRef = useRef(null)

    const handleFileChange = (event) => {
        const file = event.target.files[0]
        setPdf(file)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError("")
        setSuccess("")

        const formData = new FormData()
        formData.append('pdf', pdf)

        try {
            const response = await axios.post("http://127.0.0.1:5000/document/upload-pdf", formData, {
                headers: {
                    'Content-Type': 'application/form-data'
                }
            })
            setSuccess(response.data?.message || "URL processed successfully.")
            setTimeout(() => setSuccess(""), 2000)

            // Reset the file input
            if (fileInputRef.current) {
                fileInputRef.current.value = ""
            }

            setPdf(null)

        } catch (err) {
            console.error("Upload error:", err)
            const errorMessage = err.response?.data?.error || "An error occurred.";

            setError(errorMessage)
            setTimeout(() => setError(""), 2000)
            
            // Reset the file input
            if (fileInputRef.current) {
                fileInputRef.current.value = ""
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
                name="pdf"
                onChange={handleFileChange}
                accept=".pdf"
                ref={fileInputRef}
                className="form-input"
                />
                <button type="submit" disabled={isLoading || !pdf} className="form-button">
                {isLoading ? "Loading ..." : "Upload PDF"}
                </button>

                <FormMessage error={error} success={success} />
                
            </form>
        </div>

    )
}

export default UploadPdf