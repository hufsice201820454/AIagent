import axios from 'axios'

const API_URL = '/api'

axios.defaults.baseURL = API_URL

export const companyService = {
  getOEMCompanies: (params) => axios.get('/companies/oem', { params }),
  getOEMCompany: (id) => axios.get(`/companies/oem/${id}`),
  toggleFavorite: (id) => axios.post(`/companies/oem/${id}/favorite`),
  getFavorites: () => axios.get('/companies/favorites'),
  getFinancialSummary: () => axios.get('/companies/financials/summary')
}

export const newsService = {
  getNews: (params) => axios.get('/news', { params }),
  getNewsItem: (id) => axios.get(`/news/${id}`),
  getCompanyNews: (oemId, limit = 10) => axios.get(`/news/company/${oemId}/latest`, { params: { limit } })
}

export const reportService = {
  getReports: (params) => axios.get('/reports', { params }),
  getReport: (id) => axios.get(`/reports/${id}`),
  getReportByCode: (code) => axios.get(`/reports/code/${code}`),
  generateReport: (data) => axios.post('/reports/generate', data),
  runAnalysis: (data) => axios.post('/reports/analysis', data)
}

export const userService = {
  getCurrentUser: () => axios.get('/users/me'),
  updateUser: (data) => axios.put('/users/me', data)
}
