import api from './index'

export const chatsApi = {
  list: () => api.get('/chats/'),
  get: (id) => api.get(`/chats/${id}`),
  getMessages: (chatId, params) =>
    api.get(`/chats/${chatId}/messages`, { params }),
  sendMessage: (chatId, data) =>
    api.post(`/chats/${chatId}/messages`, data),
  sendMessageWithAttachment: (chatId, { messageText, file }) => {
    const fd = new FormData()
    fd.append('message_text', messageText)
    fd.append('file', file)
    return api.post(`/chats/${chatId}/messages/attachment`, fd)
  },
}
