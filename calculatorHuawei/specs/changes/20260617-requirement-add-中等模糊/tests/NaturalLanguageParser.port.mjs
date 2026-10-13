// specs/changes/20260617-requirement-add-中等模糊/tests/NaturalLanguageParser.port.mjs
// aid-workflow 20260617: Issue #25 单位换算扩展 — Node 端口
// 1:1 端口:与 ArkTS NaturalLanguageParser.ets 一一对应
// 覆盖 area/time/speed 中英文别名 + 零回归 spot check

import { NaturalLanguageParser } from './UnitConverter.port.impl.mjs'

let pass = 0
let fail = 0
const failures = []

function assertParse(input, expected, name) {
  const r = NaturalLanguageParser.parse(input)
  if (r === null) {
    fail++
    failures.push(`FAIL ${name}: parse(${JSON.stringify(input)}) → null (expected ${JSON.stringify(expected)})`)
    return
  }
  let ok = true
  for (const k of Object.keys(expected)) {
    if (r[k] !== expected[k]) {
      ok = false
      fail++
      failures.push(`FAIL ${name}: parse(${JSON.stringify(input)}).${k} = ${r[k]}, expected ${expected[k]}`)
      break
    }
  }
  if (ok) pass++
}

function assertNull(input, name) {
  const r = NaturalLanguageParser.parse(input)
  if (r === null) {
    pass++
  } else {
    fail++
    failures.push(`FAIL ${name}: parse(${JSON.stringify(input)}) should be null, got ${JSON.stringify(r)}`)
  }
}

console.log('--- Issue #25 NL area 中文 ---')
assertParse('100亩转平方米', { value: 100, from: 'mu', to: 'm2', category: 'area' }, 'NL_CN_A01_100mu_to_m2')
assertParse('1英亩转平方米', { value: 1, from: 'acre', to: 'm2', category: 'area' }, 'NL_CN_A02_1acre_to_m2')
assertParse('1公顷转平方米', { value: 1, from: 'hectare', to: 'm2', category: 'area' }, 'NL_CN_A03_1hectare_to_m2')
assertParse('1平方千米转平方米', { value: 1, from: 'km2', to: 'm2', category: 'area' }, 'NL_CN_A04_1km2_to_m2')
assertParse('100平方英尺转平方米', { value: 100, from: 'ft2', to: 'm2', category: 'area' }, 'NL_CN_A05_100ft2_to_m2')

console.log('--- Issue #25 NL area English ---')
assertParse('100 acre to m2', { value: 100, from: 'acre', to: 'm2', category: 'area' }, 'NL_EN_A01_100acre_to_m2')
assertParse('1 hectare to m2', { value: 1, from: 'hectare', to: 'm2', category: 'area' }, 'NL_EN_A02_1hectare_to_m2')
assertParse('1 km2 to m2', { value: 1, from: 'km2', to: 'm2', category: 'area' }, 'NL_EN_A03_1km2_to_m2')

console.log('--- Issue #25 NL time 中文 ---')
assertParse('2小时转分钟', { value: 2, from: 'h', to: 'min', category: 'time' }, 'NL_CN_Ti01_2h_to_min')
assertParse('1天转小时', { value: 1, from: 'd', to: 'h', category: 'time' }, 'NL_CN_Ti02_1d_to_h')
assertParse('1周转天', { value: 1, from: 'wk', to: 'd', category: 'time' }, 'NL_CN_Ti03_1wk_to_d')
assertParse('1月转天', { value: 1, from: 'mo', to: 'd', category: 'time' }, 'NL_CN_Ti04_1mo_to_d')
assertParse('1年转天', { value: 1, from: 'yr', to: 'd', category: 'time' }, 'NL_CN_Ti05_1yr_to_d')
assertParse('1000毫秒转秒', { value: 1000, from: 'ms', to: 's', category: 'time' }, 'NL_CN_Ti06_1000ms_to_s')

console.log('--- Issue #25 NL time English ---')
assertParse('2 hour to min', { value: 2, from: 'h', to: 'min', category: 'time' }, 'NL_EN_Ti01_2hour_to_min')
assertParse('1 day to hour', { value: 1, from: 'd', to: 'h', category: 'time' }, 'NL_EN_Ti02_1day_to_hour')
assertParse('1 year to day', { value: 1, from: 'yr', to: 'd', category: 'time' }, 'NL_EN_Ti03_1year_to_day')

console.log('--- Issue #25 NL speed 中文 ---')
assertParse('60英里每小时转千米每小时', { value: 60, from: 'mph', to: 'kmh', category: 'speed' }, 'NL_CN_S01_60mph_to_kmh')
assertParse('100千米每小时转米每秒', { value: 100, from: 'kmh', to: 'm_s', category: 'speed' }, 'NL_CN_S02_100kmh_to_mps')
assertParse('1节转千米每小时', { value: 1, from: 'knot', to: 'kmh', category: 'speed' }, 'NL_CN_S03_1knot_to_kmh')
assertParse('1马赫转米每秒', { value: 1, from: 'mach', to: 'm_s', category: 'speed' }, 'NL_CN_S04_1mach_to_mps')
assertParse('10米每秒转千米每小时', { value: 10, from: 'm_s', to: 'kmh', category: 'speed' }, 'NL_CN_S05_10mps_to_kmh')

console.log('--- Issue #25 NL speed English ---')
assertParse('60 mph to kmh', { value: 60, from: 'mph', to: 'kmh', category: 'speed' }, 'NL_EN_S01_60mph_to_kmh')
assertParse('1 knot to kmh', { value: 1, from: 'knot', to: 'kmh', category: 'speed' }, 'NL_EN_S02_1knot_to_kmh')
assertParse('1 mach to m/s', { value: 1, from: 'mach', to: 'm_s', category: 'speed' }, 'NL_EN_S03_1mach_to_mps')

console.log('--- Issue #25 NL cross-category rejection ---')
assertNull('100亩转小时', 'NL_XC_01_area_to_time')
assertNull('2小时转千米每小时', 'NL_XC_02_time_to_speed')
assertNull('60英里每小时转平方米', 'NL_XC_03_speed_to_area')

console.log('--- Issue #25 zero regression NL spot check (#18) ---')
assertParse('100厘米转英寸', { value: 100, from: 'cm', to: 'inch', category: 'length' }, 'NL_REG_01_100cm_to_inch')
assertParse('30摄氏度转华氏度', { value: 30, from: 'C', to: 'F', category: 'temperature' }, 'NL_REG_02_30C_to_F')
assertParse('5磅转千克', { value: 5, from: 'lb', to: 'kg', category: 'mass' }, 'NL_REG_03_5lb_to_kg')
assertParse('1加仑转升', { value: 1, from: 'gal', to: 'L', category: 'volume' }, 'NL_REG_04_1gal_to_L')

console.log(`\n=== NaturalLanguageParser #25 端口测试结果 ===`)
console.log(`pass: ${pass}, fail: ${fail}`)
if (fail > 0) {
  console.log('Failures:')
  for (const f of failures) console.log('  ' + f)
  process.exit(1)
}
console.log('ALL PASS')
