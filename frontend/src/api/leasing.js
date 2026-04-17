import api from './index'

export const leasingApi = {
  calculate: (data) => api.post('/leasing/calculator', data),

  // Lease requests (лизингополучатель -> лизингодатель)
  createRequest: (data) => api.post('/leasing/requests', data),
  listRequests: (params) => api.get('/leasing/requests', { params }),
  getRequest: (id) => api.get(`/leasing/requests/${id}`),
  updateRequestStatus: (id, status) =>
    api.patch(`/leasing/requests/${id}/status`, { status }),

  // Supplier requests (лизингодатель -> поставщик)
  createSupplierRequest: (data) => api.post('/leasing/supplier-requests', data),
  listSupplierRequests: (params) => api.get('/leasing/supplier-requests', { params }),
  getSupplierRequest: (id) => api.get(`/leasing/supplier-requests/${id}`),
  updateSupplierRequestStatus: (id, status) =>
    api.patch(`/leasing/supplier-requests/${id}/status`, { status }),

  // Contracts
  createContract: (data) => api.post('/leasing/contracts', data),
  listContracts: (params) => api.get('/leasing/contracts', { params }),
  getContract: (id) => api.get(`/leasing/contracts/${id}`),
  updateContractStatus: (id, status) =>
    api.patch(`/leasing/contracts/${id}/status`, { status }),
  updateContractFields: (id, data) =>
    api.patch(`/leasing/contracts/${id}/fields`, data),
  confirmContract: (id, confirmed) =>
    api.post(`/leasing/contracts/${id}/confirm`, { confirmed }),

  // Documents
  generateDocuments: (contractId) =>
    api.post(`/leasing/contracts/${contractId}/generate-documents`),
  getDocuments: (contractId) =>
    api.get(`/leasing/contracts/${contractId}/documents`),

  // Payment schedule
  generateSchedule: (contractId) =>
    api.post(`/leasing/contracts/${contractId}/schedule`),
  getSchedule: (contractId) =>
    api.get(`/leasing/contracts/${contractId}/schedule`),

  // Payments
  makePayment: (data) => api.post('/leasing/payments', data),

  // Purchase contracts (legacy)
  createPurchaseContract: (data) =>
    api.post('/leasing/purchase-contracts', data),
}
