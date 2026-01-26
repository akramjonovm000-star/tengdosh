import axios from 'axios';

const api = axios.create({
    baseURL: '/grant/api/v1',
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('grant_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('grant_token');
            window.location.reload(); // Force logout
        }
        return Promise.reject(error);
    }
);

export default api;
