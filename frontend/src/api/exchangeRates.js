import api from './index'

export const exchangeRatesApi = {
  get: () => api.get('/exchange-rates'),
}
