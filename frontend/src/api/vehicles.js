import api from './index'

export const vehiclesApi = {
  list: (params) => api.get('/vehicles/', { params }),
  get: (id) => api.get(`/vehicles/${id}`),
  create: (data) => api.post('/vehicles/', data),
  update: (id, data) => api.patch(`/vehicles/${id}`, data),
  delete: (id) => api.delete(`/vehicles/${id}`),

  uploadImage: (vehicleId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/vehicles/${vehicleId}/images`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteImage: (vehicleId, imageId) =>
    api.delete(`/vehicles/${vehicleId}/images/${imageId}`),
}
