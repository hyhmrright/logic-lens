'use strict'
// Reproduces original behavior; assertions intentionally describe observed defects.
const assert = require('node:assert/strict')
const root = '/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-rtiignqt/workspace/'
const Range = require(root + 'classes/range')
const Comparator = require(root + 'classes/comparator')
const SemVer = require(root + 'classes/semver')
const satisfies = require(root + 'functions/satisfies')
const minVersion = require(root + 'ranges/min-version')
let checks = 0
function check(name, f) { f(); checks++; console.log('REPRODUCED: ' + name) }

check('Comparator constructor loses options', () => {
  assert.equal(new Range(new Comparator('>=1.2.3')).test('1.2.4'), true)
  assert.throws(() => new Range(new Comparator('>=1.2.3-alpha')).test('1.2.3-beta'), TypeError)
  assert.equal(new Range('>=1.2.3-alpha').test('1.2.3-beta'), true)
  assert.throws(() => new Range(new Comparator('>=1.2.3'), { includePrerelease: true }).test('1.2.4-beta'), TypeError)
  assert.equal(new Range(new Comparator('>=1.2.3'), { loose: true }).test('01.2.4'), false)
  assert.equal(new Range('>=1.2.3', { loose: true }).test('01.2.4'), true)
})
check('Wildcard OR drops explicit prerelease', () => {
  assert.equal(new Range('1.2.3-alpha').test('1.2.3-alpha'), true)
  for (const s of ['* || 1.2.3-alpha', '1.2.3-alpha || *']) {
    assert.equal(new Range(s).range, '')
    assert.equal(new Range(s).test('1.2.3-alpha'), false)
  }
  assert.equal(new Range('* || 1.2.3-alpha').test('1.2.3'), true)
})
check('Zero lower-bound removal admits excluded prerelease', () => {
  assert.equal(new Comparator('>=0.0.0').test('0.0.0-0'), false)
  assert.equal(new Range('>=0.0.0 <0.0.0-alpha').range, '<0.0.0-alpha')
  assert.equal(satisfies('0.0.0-0', '>=0.0.0 <0.0.0-alpha'), true)
  assert.equal(satisfies('0.0.0', '>=0.0.0 <0.0.0-alpha'), false)
})
check('Loose caret tests textual zero', () => {
  assert.equal(new SemVer('00.2.3', { loose: true }).version, '0.2.3')
  assert.equal(satisfies('0.5.0', '^00.2.3', { loose: true }), true)
  assert.equal(satisfies('0.5.0', '^0.2.3', { loose: true }), false)
  assert.equal(satisfies('0.0.4', '^0.00.3', { loose: true }), true)
  assert.equal(satisfies('0.0.4', '^0.0.3', { loose: true }), false)
})
check('Strict range repairs repeated build separator', () => {
  assert.throws(() => new SemVer('1.2.3+foo+bar'), TypeError)
  assert.throws(() => new Comparator('1.2.3+foo+bar'), TypeError)
  assert.equal(new Range('1.2.3+foo+bar').range, '1.2.3')
  assert.equal(satisfies('1.2.3', '1.2.3+foo+bar'), true)
  assert.equal(satisfies('1.2.3', '1.2.3+foo'), true)
})
check('Hyphen lower-bound build swallows prerelease suffix', () => {
  const options = { includePrerelease: true }
  assert.equal(new Range('1.2.3+build - 2.3.4', options).range, '>=1.2.3 <2.3.5-0')
  assert.equal(satisfies('1.2.3-alpha', '1.2.3+build - 2.3.4', options), false)
  assert.equal(satisfies('1.2.3-alpha', '1.2.3 - 2.3.4', options), true)
})
check('Pairwise intersection assumes a dense version order', () => {
  assert.equal(new Range('>1.0.0').intersects(new Range('<1.0.1')), true)
  assert.equal(minVersion('>1.0.0 <1.0.1'), null)
  assert.equal(minVersion('>1.0.0 <1.0.2').version, '1.0.1')
  assert.equal(new Range('>1.0.0').test('1.0.1'), true)
  assert.equal(new Range('<1.0.1').test('1.0.1'), false)
  assert.equal(new Range('>1.0.0').test('1.0.1-alpha'), false)
})
console.log(JSON.stringify({ runtime: process.version, reproducedGroups: checks, sourceModified: false }))
