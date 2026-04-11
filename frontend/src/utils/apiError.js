/**
 * Текст ошибки из ответа FastAPI/axios для показа пользователю.
 * @param {unknown} err
 * @param {string} [fallback]
 */
export function formatApiError(err, fallback = 'Произошла ошибка') {
  const e = err && typeof err === 'object' ? err : {}
  const res = 'response' in e ? e.response : undefined
  if (!res) {
    const msg = 'message' in e && typeof e.message === 'string' ? e.message : ''
    if (/network/i.test(msg) || msg === 'Network Error') {
      return 'Не удалось связаться с сервером. Проверьте, что API запущен и доступен.'
    }
    return fallback
  }

  const data = res.data
  const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : undefined

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          const loc = Array.isArray(item.loc) ? item.loc.filter(Boolean).join(' → ') : ''
          return loc ? `${loc}: ${item.msg}` : String(item.msg)
        }
        return typeof item === 'string' ? item : JSON.stringify(item)
      })
      .filter(Boolean)
    if (parts.length) return parts.join('; ')
  }

  if (detail && typeof detail === 'object' && 'msg' in detail) {
    return String(detail.msg)
  }

  return fallback
}
