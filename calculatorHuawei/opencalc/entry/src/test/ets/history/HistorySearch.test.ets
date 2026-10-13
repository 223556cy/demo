// OpenCalc — HistorySearch 单元测试 (hypium 风格)
// Issue #24 历史搜索框
// TDD RED 阶段: 驱动 HistorySearch.ets 生成

import { describe, it, expect } from '@ohos/hypium'
import { HistoryItem } from '../../../main/ets/model/Models'
import { filterHistoryByQuery } from '../../../main/ets/history/HistorySearch'

// 工具: 构造 HistoryItem
function mkItem(id: number, expression: string, result: string, timestamp: number = 0): HistoryItem {
  return { id, expression, result, timestamp }
}

export default function historySearchTest() {

  describe('filterHistoryByQuery_basic', () => {

    // TC-01: 空 query → 返回原 items 引用
    it('AC_HS_06_empty_query_should_return_same_items', 0, () => {
      const items: HistoryItem[] = [
        mkItem(1, '1+1', '2'),
        mkItem(2, '2+2', '4')
      ]
      const result = filterHistoryByQuery(items, '')
      expect(result).assertEqual(items)
    })

    // TC-01b: 全空格 query → trim 后视为空, 透传
    it('AC_HS_06_whitespace_query_should_be_treated_as_empty', 1, () => {
      const items: HistoryItem[] = [
        mkItem(1, '1+1', '2')
      ]
      const result = filterHistoryByQuery(items, '   ')
      expect(result).assertEqual(items)
    })

    // TC-02: query="12" → 匹配 expression 或 result 含 "12"
    it('AC_HS_02_query_12_should_match_expression_or_result', 2, () => {
      const items: HistoryItem[] = [
        mkItem(1, '1+1', '2'),          // 不含 12
        mkItem(2, '12+0', '12'),         // expr 含 12, result 含 12
        mkItem(3, '6*2', '12'),          // result 含 12
        mkItem(4, '100-88', '12')        // result 含 12
      ]
      const result = filterHistoryByQuery(items, '12')
      expect(result.length).assertEqual(3)
      expect(result[0].id).assertEqual(2)
      expect(result[1].id).assertEqual(3)
      expect(result[2].id).assertEqual(4)
    })

    // TC-03: query="SIN" (大写) → 匹配 "sin" (大小写不敏感)
    it('AC_HS_03_case_insensitive_uppercase_query_matches_lowercase', 3, () => {
      const items: HistoryItem[] = [
        mkItem(1, 'sin(30)', '0.5'),
        mkItem(2, 'SIN(45)', '0.707'),
        mkItem(3, 'Sin(60)', '0.866'),
        mkItem(4, 'cos(30)', '0.866')   // 不含 sin
      ]
      const result = filterHistoryByQuery(items, 'SIN')
      expect(result.length).assertEqual(3)
      expect(result[0].id).assertEqual(1)
      expect(result[1].id).assertEqual(2)
      expect(result[2].id).assertEqual(3)
    })

    // TC-04: query="xyz" (无匹配) → 返回 []
    it('AC_HS_05_no_match_should_return_empty_array', 4, () => {
      const items: HistoryItem[] = [
        mkItem(1, '1+1', '2'),
        mkItem(2, '2+2', '4')
      ]
      const result = filterHistoryByQuery(items, 'xyz')
      expect(result.length).assertEqual(0)
    })
  })

  describe('filterHistoryByQuery_edge_cases', () => {

    // TC-05: 特殊字符 (π, e) → 正常匹配
    it('AC_HS_special_chars_pi_and_e_should_match', 0, () => {
      const items: HistoryItem[] = [
        mkItem(1, 'π*2', '6.28'),
        mkItem(2, 'e^2', '7.39'),
        mkItem(3, '1+1', '2')
      ]
      const resultPi = filterHistoryByQuery(items, 'π')
      expect(resultPi.length).assertEqual(1)
      expect(resultPi[0].id).assertEqual(1)

      const resultE = filterHistoryByQuery(items, 'e')
      expect(resultE.length).assertEqual(2)
    })

    // TC-06: result 含数字/逗号 → 正常匹配
    it('AC_HS_result_with_commas_should_match', 1, () => {
      const items: HistoryItem[] = [
        mkItem(1, '1000+1000', '2,000'),
        mkItem(2, '500+500', '1,000')
      ]
      const result = filterHistoryByQuery(items, '2,000')
      expect(result.length).assertEqual(1)
      expect(result[0].id).assertEqual(1)
    })

    // TC-07: null items → 返回 []
    it('AC_HS_null_items_should_return_empty_array', 2, () => {
      const result = filterHistoryByQuery(null, 'test')
      expect(result.length).assertEqual(0)
    })

    // TC-08: undefined items → 返回 []
    it('AC_HS_undefined_items_should_return_empty_array', 3, () => {
      const result = filterHistoryByQuery(undefined, 'test')
      expect(result.length).assertEqual(0)
    })

    // TC-09: 空数组 items → 返回 []
    it('AC_HS_empty_items_should_return_empty_array', 4, () => {
      const result = filterHistoryByQuery([], 'test')
      expect(result.length).assertEqual(0)
    })

    // TC-10: 子串匹配 (不要求整词匹配)
    it('AC_HS_substring_match_should_work', 5, () => {
      const items: HistoryItem[] = [
        mkItem(1, '123+456', '579'),
        mkItem(2, '7+8', '15')
      ]
      const result = filterHistoryByQuery(items, '23')
      expect(result.length).assertEqual(1)
      expect(result[0].id).assertEqual(1)
    })

    // TC-11: 不修改入参 items
    it('AC_HS_should_not_mutate_input_items', 6, () => {
      const items: HistoryItem[] = [
        mkItem(1, '1+1', '2'),
        mkItem(2, '2+2', '4')
      ]
      const originalLen: number = items.length
      filterHistoryByQuery(items, '1')
      expect(items.length).assertEqual(originalLen)
      expect(items[0].expression).assertEqual('1+1')
    })
  })
}
