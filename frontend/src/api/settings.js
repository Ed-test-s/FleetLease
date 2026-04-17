import api from './index'

export const settingsApi = {
  getAdmin: () => api.get('/admin/settings'),
  patchAdmin: (data) => api.patch('/admin/settings', data),
}
