// Helpers shared by the availability grid and the solver payload.
// Must stay in sync with backend/src/data_input.py:
//   - only Monday-Friday are schedulable
//   - the availability grid uses 30-minute blocks (AVAILABILITY_BLOCK_MINUTES)
export const AVAILABILITY_BLOCK_MINUTES = 30

const WEEKDAY_NAMES = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

export function toMinutes(hhmm) {
  const [h, m] = String(hhmm || '0:0').split(':')
  return Number(h) * 60 + Number(m)
}

export function toHHMM(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

/** ISO dates (YYYY-MM-DD) of the working days between two dates, inclusive. */
export function workingDays(fechaInicio, fechaFin) {
  if (!fechaInicio || !fechaFin) return []
  const days = []
  const cursor = new Date(`${fechaInicio}T00:00:00`)
  const end = new Date(`${fechaFin}T00:00:00`)
  while (cursor <= end && days.length < 366) {
    const dow = cursor.getDay()
    if (dow >= 1 && dow <= 5) {
      days.push({
        fecha: cursor.toISOString().slice(0, 10),
        diaSemana: WEEKDAY_NAMES[dow],
      })
    }
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}

/** Grid rows: 30-minute blocks inside the daily window. */
export function timeBlocks(horaInicio, horaFin, step = AVAILABILITY_BLOCK_MINUTES) {
  const start = toMinutes(horaInicio || '09:00')
  const end = toMinutes(horaFin || '14:00')
  const blocks = []
  for (let t = start; t + step <= end; t += step) blocks.push(toHHMM(t))
  return blocks
}

/** Defense slots the solver will generate, for previewing capacity in the UI. */
export function defenseSlots(periodo) {
  if (!periodo) return []
  const dur = Number(periodo.duracion_defensa) || 30
  const days = workingDays(periodo.fecha_inicio, periodo.fecha_fin)
  const times = timeBlocks(periodo.hora_inicio_dia, periodo.hora_fin_dia, dur)
  return days.flatMap((d) => times.map((hora) => ({ ...d, hora })))
}
