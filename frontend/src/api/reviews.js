import api from './index'

export const reviewsApi = {
  create: (data) => api.post('/reviews/', data),
  getForUser: (userId, params) =>
    api.get(`/reviews/user/${userId}`, { params }),
}
