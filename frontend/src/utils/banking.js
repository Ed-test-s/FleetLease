/**
 * Счёт считается полным для участия в сделках (как на бэкенде):
 * IBAN, название банка, адрес отделения и SWIFT.
 */
export function hasBankRequisites(user) {
  const list = user?.bank_accounts || []
  const nz = (x) => x != null && String(x).trim() !== ''
  return list.some(
    (a) =>
      nz(a.iban) &&
      nz(a.bank_name) &&
      nz(a.bank_address) &&
      nz(a.swift),
  )
}
