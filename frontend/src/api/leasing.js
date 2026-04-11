import api from './index'

export const leasingApi = {
  calculate: (data) => api.post('/leasing/calculator', data),

  createRequest: (data) => api.post('/leasing/requests', data),
  listRequests: (params) => api.get('/leasing/requests', { params }),
  getRequest: (id) => api.get(`/leasing/requests/${id}`),
  updateRequestStatus: (id, status) =>
    api.patch(`/leasing/requests/${id}/status`, { status }),

  createContract: (data) => api.post('/leasing/contracts', data),
  listContracts: (params) => api.get('/leasing/contracts', { params }),
  getContract: (id) => api.get(`/leasing/contracts/${id}`),
  updateContractStatus: (id, status) =>
    api.patch(`/leasing/contracts/${id}/status`, { status }),

  generateSchedule: (contractId) =>
    api.post(`/leasing/contracts/${contractId}/schedule`),
  getSchedule: (contractId) =>
    api.get(`/leasing/contracts/${contractId}/schedule`),

  makePayment: (data) => api.post('/leasing/payments', data),

  createPurchaseContract: (data) =>
    api.post('/leasing/purchase-contracts', data),
}
