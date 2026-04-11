import api from './index'

export const referencesApi = {
  getBrands: () => api.get('/references/brands'),
  createBrand: (name) => api.post('/references/brands', { name }),
  createModel: (brand_id, name) => api.post('/references/models', { brand_id, name }),

  getColours: () => api.get('/references/colours'),
  createColour: (name) => api.post('/references/colours', { name }),

  getRegions: () => api.get('/references/regions'),
}
