import api from './index'

export const authApi = {
  login: (identifier, password) =>
    api.post('/auth/login', { identifier, password }),

  register: (data) =>
    api.post('/auth/register', data),
}
