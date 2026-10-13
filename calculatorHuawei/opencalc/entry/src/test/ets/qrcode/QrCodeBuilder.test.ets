// OpenCalc — QrCodeBuilder 单元测试（hypium 风格）
// Issue #13 一键分享二维码

import { describe, it, expect } from '@ohos/hypium'
import { QrCodeBuilder, buildSharePayload, MAX_PAYLOAD_LENGTH, PAYLOAD_PREFIX, RESULT_PREFIX, TRUNCATED_FLAG } from '../../../main/ets/qrcode/QrCodeBuilder'

export default function qrCodeBuilderTest() {
  describe('QrCodeBuilder_buildSharePayload_basic', () => {

    it('TC01_should_encode_basic_plus_as_percent_2B', 0, () => {
      // 1+2 = 3 → + 编码为 %2B
      const got = buildSharePayload('1+2', '3')
      expect(got).assertEqual('opencalc://calc?expr=1%2B2&res=3')
    })

    it('TC02_should_encode_pi_utf8_CF80_and_slash', 1, () => {
      // sin(π/2) → π 编码为 UTF-8 %CF%80，/ 编码为 %2F
      // ( 和 ) 在 encodeURIComponent 中是 unreserved 字符，不编码
      const got = buildSharePayload('sin(π/2)', '1')
      expect(got.indexOf('%CF%80') !== -1).assertTrue()
      expect(got.indexOf('%2F') !== -1).assertTrue()   // /
      expect(got.indexOf('sin(') !== -1).assertTrue()  // ( NOT encoded
      expect(got.indexOf(')') !== -1).assertTrue()     // ) NOT encoded
    })

    it('TC03_should_handle_empty_strings_gracefully', 2, () => {
      // 空字符串不抛异常，返回合法 payload
      const got = buildSharePayload('', '')
      expect(got).assertEqual('opencalc://calc?expr=&res=')
    })

    it('TC04_should_encode_space_as_percent_20', 3, () => {
      // 1 + 2 → 空格编码为 %20
      const got = buildSharePayload('1 + 2', '3')
      expect(got.indexOf('%20') !== -1).assertTrue()
    })

    it('TC05_should_encode_slash_as_percent_2F', 4, () => {
      // 1/2 → / 编码为 %2F
      const got = buildSharePayload('1/2', '0.5')
      expect(got.indexOf('%2F') !== -1).assertTrue()
    })

    it('TC06_should_truncate_long_expression_with_truncated_flag', 5, () => {
      // expr 250 字符 + res 3 字符 → 总 > 200 → 截断 expr + 追加 &truncated=1
      const longExpr: string = 'a'.repeat(250)
      const got = buildSharePayload(longExpr, '123')
      expect(got.length <= MAX_PAYLOAD_LENGTH).assertTrue()
      expect(got.indexOf(TRUNCATED_FLAG) !== -1).assertTrue()
    })

    it('TC07_should_truncate_when_result_alone_is_too_long', 7, () => {
      // expr 短，但 res 超过 200 → 截断整个 payload
      const longRes: string = 'b'.repeat(300)
      const got = buildSharePayload('1', longRes)
      expect(got.length <= MAX_PAYLOAD_LENGTH).assertTrue()
    })

    it('TC08_should_encode_caret_as_5E_but_NOT_minus', 8, () => {
      // 2^10 → ^ 编码为 %5E
      // -5 → - 不编码（unreserved）
      const got = buildSharePayload('2^10', '1024')
      expect(got.indexOf('2%5E10') !== -1).assertTrue()   // ^ encoded

      const gotNeg = buildSharePayload('-5', '-5')
      expect(gotNeg.indexOf('-5') !== -1).assertTrue()     // - NOT encoded
    })
  })

  describe('QrCodeBuilder_constants', () => {

    it('TC09_MAX_PAYLOAD_LENGTH_should_be_200', 9, () => {
      expect(MAX_PAYLOAD_LENGTH).assertEqual(200)
    })

    it('TC10_PAYLOAD_PREFIX_and_RESULT_PREFIX_should_be_correct', 10, () => {
      expect(PAYLOAD_PREFIX).assertEqual('opencalc://calc?expr=')
      expect(RESULT_PREFIX).assertEqual('&res=')
      expect(TRUNCATED_FLAG).assertEqual('&truncated=1')
    })

    it('TC11_QrCodeBuilder_namespace_should_expose_static_methods', 11, () => {
      // 命名空间风格导出（与 HistoryFilter 一致）
      expect(QrCodeBuilder.MAX_PAYLOAD_LENGTH).assertEqual(200)
      expect(QrCodeBuilder.buildSharePayload('1+2', '3')).assertEqual('opencalc://calc?expr=1%2B2&res=3')
    })
  })
}
