// specs/changes/20260617-requirement-add-中等模糊/tests/UnitConverter.port.mjs
// aid-workflow 20260617: Issue #25 单位换算扩展 — Node 端口
// 1:1 端口:与 ArkTS UnitConverter.ets 一一对应
// 覆盖 area/time/speed 3 大类 + 跨类别拒绝 + 零回归 spot check

import { UnitConverter } from './UnitConverter.port.impl.mjs'

const EPS = 1e-6
let pass = 0
let fail = 0
const failures = []

function assertEq(actual, expected, name) {
  if (actual === expected) {
    pass++
  } else {
    fail++
    failures.push(`FAIL ${name}: expected ${expected}, got ${actual}`)
  }
}

function assertApprox(actual, expected, eps, name) {
  if (actual !== null && Math.abs(actual - expected) < eps) {
    pass++
  } else {
    fail++
    failures.push(`FAIL ${name}: expected ≈${expected} (±${eps}), got ${actual}`)
  }
}

function assertNull(actual, name) {
  if (actual === null) {
    pass++
  } else {
    fail++
    failures.push(`FAIL ${name}: expected null, got ${actual}`)
  }
}

console.log('--- Issue #25 UnitConverter area ---')
assertApprox(UnitConverter.convert(1, 'm2', 'cm2', 'area'), 10000, EPS, 'UC_A_01_1m2_to_cm2')
assertApprox(UnitConverter.convert(1, 'cm2', 'm2', 'area'), 0.0001, EPS, 'UC_A_02_1cm2_to_m2')
assertApprox(UnitConverter.convert(1, 'acre', 'm2', 'area'), 4046.8564224, 1e-4, 'UC_A_03_1acre_to_m2')
assertApprox(UnitConverter.convert(1, 'hectare', 'm2', 'area'), 10000, EPS, 'UC_A_04_1hectare_to_m2')
assertApprox(UnitConverter.convert(1, 'mu', 'm2', 'area'), 2000.0 / 3.0, 1e-3, 'UC_A_05_1mu_to_m2')
assertApprox(UnitConverter.convert(100, 'mu', 'm2', 'area'), 66666.66666666667, 1e-3, 'UC_A_06_100mu_to_m2')
assertApprox(UnitConverter.convert(1, 'km2', 'm2', 'area'), 1000000, EPS, 'UC_A_07_1km2_to_m2')
assertApprox(UnitConverter.convert(1, 'ft2', 'm2', 'area'), 0.09290304, 1e-4, 'UC_A_08_1ft2_to_m2')
assertApprox(UnitConverter.convert(1, 'm2', 'acre', 'area'), 1.0 / 4046.8564224, 1e-6, 'UC_A_09_1m2_to_acre')
assertApprox(UnitConverter.convert(1, 'hectare', 'acre', 'area'), 10000.0 / 4046.8564224, 1e-4, 'UC_A_10_1hectare_to_acre')

console.log('--- Issue #25 UnitConverter time ---')
assertApprox(UnitConverter.convert(1, 'min', 's', 'time'), 60, EPS, 'UC_Ti_01_1min_to_s')
assertApprox(UnitConverter.convert(1, 'h', 'min', 'time'), 60, EPS, 'UC_Ti_02_1h_to_min')
assertApprox(UnitConverter.convert(2, 'h', 'min', 'time'), 120, EPS, 'UC_Ti_03_2h_to_min')
assertApprox(UnitConverter.convert(1, 'd', 'h', 'time'), 24, EPS, 'UC_Ti_04_1d_to_h')
assertApprox(UnitConverter.convert(1, 'wk', 'd', 'time'), 7, EPS, 'UC_Ti_05_1wk_to_d')
assertApprox(UnitConverter.convert(1, 'mo', 'd', 'time'), 30, EPS, 'UC_Ti_06_1mo_to_d')
assertApprox(UnitConverter.convert(1, 'yr', 'd', 'time'), 365, EPS, 'UC_Ti_07_1yr_to_d')
assertApprox(UnitConverter.convert(1000, 'ms', 's', 'time'), 1, EPS, 'UC_Ti_08_1000ms_to_s')
assertApprox(UnitConverter.convert(1, 'h', 'ms', 'time'), 3600000, EPS, 'UC_Ti_09_1h_to_ms')
assertApprox(UnitConverter.convert(1, 'wk', 'h', 'time'), 168, EPS, 'UC_Ti_10_1wk_to_h')

console.log('--- Issue #25 UnitConverter speed ---')
assertApprox(UnitConverter.convert(60, 'mph', 'kmh', 'speed'), 96.56064, 1e-3, 'UC_S_01_60mph_to_kmh')
assertApprox(UnitConverter.convert(100, 'kmh', 'mph', 'speed'), 62.137273664, 1e-3, 'UC_S_02_100kmh_to_mph')
assertApprox(UnitConverter.convert(1, 'knot', 'kmh', 'speed'), 1.852, 1e-4, 'UC_S_03_1knot_to_kmh')
assertApprox(UnitConverter.convert(1, 'knot', 'm_s', 'speed'), 1852.0 / 3600.0, 1e-4, 'UC_S_04_1knot_to_mps')
assertApprox(UnitConverter.convert(1, 'mach', 'm_s', 'speed'), 340.29, 1e-3, 'UC_S_05_1mach_to_mps')
assertApprox(UnitConverter.convert(1, 'kmh', 'm_s', 'speed'), 1000.0 / 3600.0, 1e-4, 'UC_S_06_1kmh_to_mps')
assertApprox(UnitConverter.convert(1, 'm_s', 'kmh', 'speed'), 3.6, 1e-4, 'UC_S_07_1mps_to_kmh')
assertApprox(UnitConverter.convert(1, 'mph', 'm_s', 'speed'), 1609.344 / 3600.0, 1e-4, 'UC_S_08_1mph_to_mps')

console.log('--- Issue #25 cross-category rejection ---')
assertNull(UnitConverter.convert(1, 'mu', 'h', 'area'), 'UC_XC_01_area_to_time')
assertNull(UnitConverter.convert(1, 'h', 'kmh', 'time'), 'UC_XC_02_time_to_speed')
assertNull(UnitConverter.convert(1, 'kmh', 'mu', 'speed'), 'UC_XC_03_speed_to_area')
assertNull(UnitConverter.convert(1, 'mu', 'mph', 'area'), 'UC_XC_04_area_to_speed')
assertNull(UnitConverter.convert(1, 'cm', 'mu', 'length'), 'UC_XC_05_length_to_area')
assertNull(UnitConverter.convert(1, 'm2', 'xyz', 'area'), 'UC_XC_06_unknown_unit_area')
assertNull(UnitConverter.convert(1, 'm2', 'kg', 'area'), 'UC_XC_07_area_to_mass_via_area')

console.log('--- Issue #25 zero regression spot check (#18 4 大类) ---')
assertApprox(UnitConverter.convert(100, 'cm', 'inch', 'length'), 39.3700787, EPS, 'UC_REG_L_100cm_to_inch')
assertApprox(UnitConverter.convert(100, 'C', 'F', 'temperature'), 212, EPS, 'UC_REG_T_100C_to_F')
assertApprox(UnitConverter.convert(1, 'kg', 'lb', 'mass'), 2.2046226218, 1e-4, 'UC_REG_M_1kg_to_lb')
assertApprox(UnitConverter.convert(1, 'L', 'gal', 'volume'), 0.2641720524, 1e-4, 'UC_REG_V_1L_to_gal')

console.log(`\n=== UnitConverter #25 端口测试结果 ===`)
console.log(`pass: ${pass}, fail: ${fail}`)
if (fail > 0) {
  console.log('Failures:')
  for (const f of failures) console.log('  ' + f)
  process.exit(1)
}
console.log('ALL PASS')
