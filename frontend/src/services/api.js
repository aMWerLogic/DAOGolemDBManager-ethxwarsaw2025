import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});

export const apiService = {
    // Upload file
    uploadFile: async (file, annotation = 'WEB_UPLOAD', btl = 3600) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('annotation', annotation);
        formData.append('btl', btl);

        const response = await api.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Get all batches
    getBatches: async () => {
        const response = await api.get('/batches');
        return response.data;
    },

    // Get batch info
    getBatchInfo: async (batchId) => {
        const response = await api.get(`/batch/${batchId}`);
        return response.data;
    },

    // Download file by batch ID
    downloadFile: async (batchId) => {
        const response = await api.get(`/download/${batchId}`, {
            responseType: 'blob',
        });
        return response.data;
    },

    // Search by annotation
    searchByAnnotation: async (key, value = null) => {
        const params = { key };
        if (value) params.value = value;

        console.log('Searching with params:', params);
        const response = await api.get('/search', { params });
        console.log('Search response:', response.data);
        return response.data;
    },

    // Search by numeric range
    searchNumericRange: async (key, minVal, maxVal) => {
        const response = await api.get('/search/numeric', {
            params: { key, min_val: minVal, max_val: maxVal }
        });
        return response.data;
    },

    // Get all annotations
    getAllAnnotations: async () => {
        const response = await api.get('/annotations');
        return response.data;
    },

    // Get API status
    getStatus: async () => {
        const response = await api.get('/status');
        return response.data;
    },
};

export default apiService;