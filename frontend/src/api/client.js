import axios from "axios";

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
let activeApiBaseUrl = configuredApiUrl || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: activeApiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for loading states if needed
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    apiClient.defaults.baseURL = activeApiBaseUrl;
    console.error("API Error:", error);
    return Promise.reject(error);
  },
);

export default apiClient;
