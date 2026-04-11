import api from './index'

export const usersApi = {
  getMe: () => api.get('/users/me'),
  updateMe: (data) => api.patch('/users/me', data),
  uploadAvatar: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/users/me/avatar', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getUser: (id) => api.get(`/users/${id}`),
  listUsers: (params) => api.get('/users/', { params }),

  addContact: (data) => api.post('/users/me/contacts', data),
  deleteContact: (id) => api.delete(`/users/me/contacts/${id}`),

  addBankAccount: (data) => api.post('/users/me/bank-accounts', data),
  deleteBankAccount: (id) => api.delete(`/users/me/bank-accounts/${id}`),

  upsertLeaseTerms: (data) => api.put('/users/me/lease-terms', data),

  toggleActive: (id) => api.patch(`/users/${id}/toggle-active`),
  changeRole: (id, role) => api.patch(`/users/${id}/role`, null, { params: { role } }),
}
