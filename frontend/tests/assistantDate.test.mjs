import test from 'node:test'
import assert from 'node:assert/strict'
import { limaDate, lastAllowedDate, selectionError } from '../src/assistantDate.js'

test('Lima date is ISO formatted across midnight and year boundary', () => {
  assert.equal(limaDate(new Date('2027-01-01T04:59:59Z')), '2026-12-31')
  assert.equal(limaDate(new Date('2027-01-01T05:00:00Z')), '2027-01-01')
  assert.equal(lastAllowedDate('2026-12-31'), '2027-01-07')
})

test('date range and slot start are enforced', () => {
  const now = new Date('2026-11-07T20:00:00Z')
  assert.match(selectionError('2026-11-06', 'S16', now), /fecha/)
  assert.match(selectionError('2026-11-15', 'S16', now), /fecha/)
  assert.match(selectionError('2026-02-30', 'S16', now), /válida/)
  assert.match(selectionError('2026-11-07', 'S15', now), /comenzó/)
  assert.equal(selectionError('2026-11-07', 'S16', now), '')
  assert.match(selectionError('2026-11-07', 'S16', new Date('2026-11-08T05:00:00Z')), /fecha/)
})
