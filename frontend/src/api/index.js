/**
 * =========================================================
 * 全息网络洞察系统 — 前端 API 对接模块
 * 集中管理所有后端接口请求
 * =========================================================
 * 后端地址修改位置：
 *   将下方 BASE_URL 的端口/域名改为你的后端实际地址
 *   开发环境: http://127.0.0.1:5000
 *   生产环境: https://your-domain.com
 * =========================================================
 */
import axios from 'axios'

// ---- 修改此处对接后端地址 ----
const BASE_URL = 'http://127.0.0.1:5001/api'
// ---- 修改结束 ----

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器 — 自动添加 JWT 令牌
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 — 统一处理错误
api.interceptors.response.use(
  (response) => response.data,   // 直接返回 data 层
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      // 登录页的 401 不跳转，直接交 handleLogin 处理
      if (status === 401 && !window.location.href.includes('/login')) {
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('userRole')
        window.location.href = '/login'
      }
      return Promise.reject(data || { code: status, message: '请求失败' })
    }
    return Promise.reject({ code: 0, message: '网络异常，请检查后端是否启动' })
  }
)

// ==================== 认证接口 ====================
export const authAPI = {
  login(data) { return api.post('/auth/login', data) },
  register(data) { return api.post('/auth/register', data) },
  logout() { return api.post('/auth/logout') },
  current() { return api.get('/auth/current') }
}

// ==================== 仪表盘接口 ====================
export const dashboardAPI = {
  summary() { return api.get('/dashboard/summary') }
}

// ==================== 设备接口 ====================
export const deviceAPI = {
  list(params) { return api.get('/devices', { params }) },
  detail(id) { return api.get(`/devices/${id}`) },
  create(data) { return api.post('/devices', data) },
  update(id, data) { return api.put(`/devices/${id}`, data) },
  delete(id) { return api.delete(`/devices/${id}`) }
}

// ==================== 告警接口 ====================
export const alertAPI = {
  list(params) { return api.get('/alerts', { params }) },
  detail(id) { return api.get(`/alerts/${id}`) },
  process(id) { return api.put(`/alerts/${id}`) },
  batchProcess(data) { return api.post('/alerts/batch', data) }
}

// ==================== 指标接口 ====================
export const metricsAPI = {
  list(params) { return api.get('/metrics', { params }) },
  getByDevice(id) { return api.get(`/metrics/${id}`) }
}

// ==================== 数据上传接口 ====================
export const dataAPI = {
  preview(params) { return api.get('/data/preview', { params }) },
  upload(formData) { return api.post('/data/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }) },
  history() { return api.get('/data/upload/history') },
  confirmImport(data) { return api.post('/data/upload/confirm', data) },
  downloadFile(id) { return api.get(`/data/upload/download/${id}`, { responseType: 'blob' }) },
  previewHistory(id) { return api.get(`/data/upload/preview/${id}`) }
}

// ==================== 数据分析接口 ====================
export const analysisAPI = {
  statistics(params) { return api.get('/analysis/statistics', { params }) },
  aiAnalysis(data) { return api.post('/analysis/ai', data) }
}

// ==================== AI 大模型分析接口 (DeepSeek) ===================
const DEEPSEEK_API_KEY = 'sk-ca3731f7e9a24e12a28484137b086923'
const DEEPSEEK_BASE_URL = 'https://api.deepseek.com/v1'

/**
 * 调用 DeepSeek 大模型进行网络智能分析
 */
export const deepseekAPI = {
  async analyze({ scenario, targetDevice, dateRange, prompt, systemPrompt }) {
    const response = await axios.post(`${DEEPSEEK_BASE_URL}/chat/completions`, {
      model: 'deepseek-v4-flash',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt }
      ],
      temperature: 0.3,
      max_tokens: 4096,
      stream: false
    }, {
      headers: {
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
        'Content-Type': 'application/json'
      },
      timeout: 60000
    })
    return response.data
  }
}

// ==================== 可视化看板接口 ====================
export const visualizationAPI = {
  data() { return api.get('/visualization/data') }
}

// ==================== 报表接口 ====================
export const reportAPI = {
  list(params) { return api.get('/reports', { params }) },
  generate(data) { return api.post('/reports/generate', data) },
  download(id) { return api.get(`/reports/download/${id}`, { responseType: 'blob' }) },
  delete(id) { return api.delete(`/reports/${id}`) }
}

// ==================== 系统管理接口 ====================
export const adminAPI = {
  users(params) { return api.get('/admin/users', { params }) },
  deleteUser(id) { return api.delete(`/admin/users/${id}`) },
  logs(params) { return api.get('/admin/logs', { params }) }
}

export default api
