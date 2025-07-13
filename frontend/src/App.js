import React, { useState } from "react";
import axios from "axios";
import "animate.css";
import "./App.css"; // Optional: custom neon styles

const API_URL = "http://localhost:5000";

function App() {
  const [token, setToken] = useState("");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("success");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [recommendInput, setRecommendInput] = useState("");
  const [recommendResult, setRecommendResult] = useState("");

  const login = async () => {
    console.log("Attempting login with:", { username, password });
    try {
      const response = await axios.post(`${API_URL}/login`, { username, password });
      console.log("Login response:", response);
      setToken(response.data.token);
      setMessage("✅ Logged in successfully!");
      setMessageType("success");
      console.log("Token set:", response.data.token);
    } catch (error) {
      setMessage("❌ Login failed.");
      setMessageType("error");
      console.error("Login error:", error);
    }
  };

  const register = async () => {
    console.log("Attempting registration with:", { username, password });
    if (!username || !password) {
      setMessage("⚠️ Please enter username and password.");
      setMessageType("error");
      return;
    }
    try {
      const response = await axios.post(`${API_URL}/register`, { username, password });
      console.log("Registration response:", response);
      setMessage("✅ Registration successful! Please login.");
      setMessageType("success");
    } catch (error) {
      console.error("Registration error:", error);
      setMessage(
        error.response?.data?.error?.[0]?.msg ||
        error.response?.data?.message ||
        "❌ Registration failed."
      );
      setMessageType("error");
    }
  };

  const logout = () => {
    console.log("Logging out...");
    setToken("");
    setMessage("Logged out.");
    setMessageType("success");
    setFile(null);
    setRecommendInput("");
    setRecommendResult("");
  };

  const uploadFile = async () => {
    console.log("Starting file upload...");

    if (!file) {
      console.warn("❌ No file selected.");
      setMessage("⚠️ Please select a file first.");
      setMessageType("error");
      return;
    }

    if (!token) {
      console.warn("❌ No token found.");
      setMessage("⚠️ Please login first.");
      setMessageType("error");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);

      console.log("Prepared FormData:");
      console.log("File name:", file.name);
      console.log("Token used:", `Bearer ${token}`);

      // *** IMPORTANT: DO NOT set Content-Type header manually here ***
      // Let Axios set it automatically for multipart/form-data with boundary
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`, 
          // No Content-Type here
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          console.log(`Upload progress: ${percentCompleted}%`);
        },
      });

      console.log("Upload response:", response.data);
      setMessage(`✅ File uploaded!\n🔗 IPFS Hash:\n${response.data.ipfs_hash}`);
      setMessageType("success");
    } catch (error) {
      console.error("❌ Upload failed:", error);
      console.log("Response data (if any):", error?.response?.data);
      setMessage("❌ File upload failed.");
      setMessageType("error");
    }
  };

  const getRecommendation = async () => {
    console.log("Fetching AI recommendation...");

    if (!token) {
      setMessage("⚠️ Please login first.");
      setMessageType("error");
      console.warn("No token, user not logged in");
      return;
    }

    if (!recommendInput.trim()) {
      setMessage("⚠️ Enter comma-separated numbers for features.");
      setMessageType("error");
      return;
    }

    try {
      const features = recommendInput
        .split(",")
        .map((f) => parseFloat(f.trim()))
        .filter((f) => !isNaN(f));

      if (features.length === 0) {
        setMessage("⚠️ Invalid input for features.");
        setMessageType("error");
        return;
      }

      console.log("Sending features:", features);

      const response = await axios.post(
        `${API_URL}/recommend`,
        { features },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      console.log("AI recommendation response:", response.data);
      setRecommendResult(response.data.recommendation);
      setMessage("✅ Recommendation received!");
      setMessageType("success");
    } catch (error) {
      console.error("❌ Recommendation error:", error);
      setMessage("❌ Failed to get AI recommendation.");
      setMessageType("error");
    }
  };

  return (
    <div style={styles.background}>
      <div style={styles.container}>
        <h1 style={styles.heading}>⚡ BlockShareX</h1>

        {!token && (
          <>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
            />
            <button style={styles.button} onClick={register}>
              📝 Register
            </button>
            <button style={styles.button} onClick={login}>
              🔐 Login
            </button>
          </>
        )}

        {token && (
          <>
            <button style={styles.logoutButton} onClick={logout}>
              🚪 Logout
            </button>

            <label htmlFor="fileUpload" style={styles.fileLabel}>
              📁 Choose File
              <input
                id="fileUpload"
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
                style={styles.fileInput}
              />
            </label>

            {file && (
              <p className="file-name animate__animated animate__fadeInUp">
                🎯 Selected: {file.name}
              </p>
            )}

            <button
              style={{
                ...styles.button,
                marginTop: "10px",
                background: file ? styles.greenGradient : styles.disabled,
              }}
              onClick={uploadFile}
              disabled={!file}
            >
              ⬆️ Upload File
            </button>

            <div style={{ marginTop: 40 }}>
              <h3>🤖 AI Recommendation</h3>
              <input
                style={styles.input}
                placeholder="Features (comma-separated numbers)"
                value={recommendInput}
                onChange={(e) => setRecommendInput(e.target.value)}
              />
              <button style={styles.button} onClick={getRecommendation}>
                Get Recommendation
              </button>
              {recommendResult !== "" && (
                <p
                  className="animate__animated animate__fadeInUp"
                  style={{ marginTop: 10 }}
                >
                  Recommendation: <strong>{recommendResult}</strong>
                </p>
              )}
            </div>
          </>
        )}

        {message && (
          <pre
            className={`pop-message ${messageType} animate__animated animate__fadeInUp`}
            style={{ whiteSpace: "pre-wrap", marginTop: 20 }}
          >
            {message}
          </pre>
        )}
      </div>
    </div>
  );
}

// Same styles as before
const styles = {
  background: {
    backgroundImage:
      'url("https://images.unsplash.com/photo-1620207418302-439b387441b0?auto=format&fit=crop&w=2400&q=80")',
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
    height: "100vh",
    width: "100vw",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
    overflow: "hidden",
  },
  container: {
    backdropFilter: "blur(16px)",
    backgroundColor: "rgba(255, 0, 150, 0.1)",
    border: "2px solid rgba(255, 255, 255, 0.2)",
    padding: "40px",
    borderRadius: "20px",
    boxShadow: "0 0 30px rgba(255, 0, 200, 0.5)",
    width: "90%",
    maxWidth: "500px",
    textAlign: "center",
    fontFamily: "'Orbitron', sans-serif",
    color: "#fff",
    zIndex: 2,
  },
  heading: {
    fontSize: "34px",
    marginBottom: "30px",
    textShadow: "0 0 10px rgba(255, 0, 200, 0.7)",
  },
  input: {
    padding: "12px",
    margin: "10px 0",
    borderRadius: "8px",
    border: "none",
    fontSize: "1rem",
    backgroundColor: "#022f2f",
    color: "#00ffea",
    width: "100%",
  },
  button: {
    padding: "12px 24px",
    fontSize: "16px",
    border: "none",
    borderRadius: "10px",
    cursor: "pointer",
    width: "100%",
    marginTop: "12px",
    background: "linear-gradient(135deg, #ff00cc 0%, #333399 100%)",
    color: "#fff",
    transition: "transform 0.2s ease-in-out",
  },
  greenGradient: "linear-gradient(135deg, #00ffcc, #0066ff)",
  disabled: "gray",
  fileLabel: {
    display: "block",
    marginTop: "20px",
    padding: "12px 24px",
    background: "linear-gradient(135deg, #ff0080, #7928ca)",
    color: "#fff",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "14px",
  },
  fileInput: {
    display: "none",
  },
  logoutButton: {
    backgroundColor: "#ff0055",
    color: "white",
    border: "none",
    borderRadius: "10px",
    padding: "10px 20px",
    cursor: "pointer",
    fontWeight: "bold",
    marginBottom: "20px",
    width: "100%",
  },
};

export default App;
