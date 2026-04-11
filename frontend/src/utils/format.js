export function formatPrice(value) {
  if (value == null) return '—'
  return new Intl.NumberFormat('ru-BY', {
    style: 'currency',
    currency: 'BYN',
    minimumFractionDigits: 2,
  }).format(value)
}

export function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatMileage(km) {
  if (km == null) return '—'
  return new Intl.NumberFormat('ru-RU').format(km) + ' км'
}

export const statusLabels = {
  new: 'Новая',
  in_review: 'В работе',
  approved: 'Одобрена',
  rejected: 'Отклонена',
  draft: 'Черновик',
  active: 'Активен',
  completed: 'Завершён',
  terminated: 'Расторгнут',
  pending: 'Ожидает',
  paid: 'Оплачен',
  overdue: 'Просрочен',
  success: 'Успешно',
  failed: 'Ошибка',
}

export const roleLabels = {
  client: 'Лизингополучатель',
  lease_manager: 'Лизинговая компания',
  supplier: 'Поставщик',
  admin: 'Администратор',
}

export const userTypeLabels = {
  individual: 'Физическое лицо',
  ie: 'Индивидуальный предприниматель',
  company: 'Юридическое лицо',
}

export function getRegistrationDate(createdAt) {
  if (!createdAt) return ''
  const d = new Date(createdAt)
  const months = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
  ]
  return `На сайте с ${months[d.getMonth()]} ${d.getFullYear()} года`
}
