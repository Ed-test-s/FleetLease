import api from './index'

export const favoritesApi = {
  list: () => api.get('/favorites/'),
  ids: () => api.get('/favorites/ids'),
  add: (vehicleId) => api.post(`/favorites/${vehicleId}`),
  remove: (vehicleId) => api.delete(`/favorites/${vehicleId}`),
}
