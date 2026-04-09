import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8002';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add CORS handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.config && error.response?.status === 403) {
      // Retry without auth header for CORS
      delete error.config.headers['Authorization'];
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);

// Sections
export const getSections = () => api.get('/sections');
export const getLocations = () => api.get('/locations');
export const getOASSkills = () => api.get('/oas-skills');
export const getBadges = () => api.get('/badges');

// Term Plans
export const getTermPlans = (includeDeleted = false) => api.get('/term-plans', { params: { include_deleted: includeDeleted } });
export const getTermPlan = (id) => api.get(`/term-plans/${id}`);
export const createTermPlan = (data) => api.post('/term-plans', data);
export const createMeeting = (data) => api.post('/meetings', data);
export const updateTermPlan = (id, data) => api.put(`/term-plans/${id}`, data);
export const deleteTermPlan = (id, permanent = false) => api.delete(`/term-plans/${id}`, { params: { permanent } });
export const restoreTermPlan = (id) => api.post(`/term-plans/${id}/restore`);
export const getDeletedTermPlans = () => api.get('/deleted-term-plans');

// Meetings
export const getMeetings = (planId, includeDeleted = false) => api.get(`/term-plans/${planId}/meetings`, { params: { include_deleted: includeDeleted } });
export const getMeeting = (id) => api.get(`/meetings/${id}`);
// Update meeting title
export const updateMeeting = (id, title) => api.put(`/meetings/${id}`, null, { params: { title } });
// Delete/restore meetings
export const deleteMeeting = (id, permanent = false) => api.delete(`/meetings/${id}`, { params: { permanent } });
export const restoreMeeting = (id) => api.post(`/meetings/${id}/restore`);
export const getDeletedMeetings = () => api.get('/deleted-meetings');

export const generateMeeting = (id) => {
  // Get AI settings from localStorage
  const settings = JSON.parse(localStorage.getItem('scout_architect_settings') || '{}');
  const use_llm = settings.use_ai_generation || false;
  const model = settings.ollama_model || 'gemma3:12b';
  
  return api.post(`/meetings/${id}/generate`, {}, {
    params: { use_llm, model }
  });
};

// Generate all meetings for a term plan
export const generateAllMeetings = (planId) => {
  const settings = JSON.parse(localStorage.getItem('scout_architect_settings') || '{}');
  const use_llm = settings.use_ai_generation || false;
  const model = settings.ollama_model || 'gemma3:12b';
  
  return api.post(`/term-plans/${planId}/generate-meetings`, {}, {
    params: { use_llm, model }
  });
};

// Downloads
export const downloadPDF = (url) => window.open(url, '_blank');
export const downloadMD = (url) => window.open(url, '_blank');

export default api;