'use strict'
const fs = require('fs'), path = require('path')
const source = path.join(process.cwd(), 'classes/range.js')
if (require.resolve(source) !== source) throw Error('unexpected module path')
const Range = require(source)
const c = JSON.parse(fs.readFileSync(0, 'utf8')).case
const options = { includePrerelease: c.includePrerelease }
let expected, actual, details
if (process.argv[2] === 'union') {
  const a = new Range(c.a, options), b = new Range(c.b, options)
  const combined = new Range(c.a + ' || ' + c.b, options)
  expected = a.test(c.version) || b.test(c.version)
  actual = combined.test(c.version)
  details = { a: a.range, b: b.range, combined: combined.range }
} else {
  const range = new Range(c.range, options), singleton = new Range(c.version, options)
  if (!singleton.test(c.version)) throw Error('invalid singleton oracle')
  expected = range.test(c.version)
  actual = range.intersects(singleton, options)
  details = { range: range.range, singleton: singleton.range, reverse: singleton.intersects(range, options) }
}
process.stdout.write(JSON.stringify({status: expected === actual ? 'pass' : 'violation', observation: {expected, actual, details, runtime: process.version, module: source}, sources: ['classes/range.js','classes/comparator.js','classes/semver.js','internal/re.js','internal/parse-options.js']}))
