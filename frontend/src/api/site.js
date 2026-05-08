import api from './index'

export const siteApi = {
  /** Публичная страница «О компании» */
  getAbout: () => api.get('/site/about'),

  /** Редактирование (только admin, Bearer из interceptor) */
  getAboutAdmin: () => api.get('/admin/about'),

  patchAbout: (data) => api.patch('/admin/about', data),

  uploadAboutImage: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/admin/about/upload-image', fd)
  },
}
