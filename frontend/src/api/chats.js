import api from './index'

export const chatsApi = {
  list: () => api.get('/chats/'),
  get: (id) => api.get(`/chats/${id}`),
  getMessages: (chatId, params) =>
    api.get(`/chats/${chatId}/messages`, { params }),
  sendMessage: (chatId, data) =>
    api.post(`/chats/${chatId}/messages`, data),
}
