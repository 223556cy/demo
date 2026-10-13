// OpenCalc — QrCodeBuilder Node 端口（用于本机无 hvigorw 环境跑测）
// aid-workflow 20260615: Issue #13 一键分享二维码
// 把 ArkTS 的 encodeURIComponent 用 Node 的同名全局函数替代；
// 完整逻辑等价，不依赖鸿蒙 Kit。
import {
  MAX_PAYLOAD_LENGTH,
  PAYLOAD_PREFIX,
  RESULT_PREFIX,
  TRUNCATED_FLAG,
  buildSharePayload,
  QrCodeBuilder
} from './QrCodeBuilder.port.mjs.source.mjs'

export {
  MAX_PAYLOAD_LENGTH,
  PAYLOAD_PREFIX,
  RESULT_PREFIX,
  TRUNCATED_FLAG,
  buildSharePayload,
  QrCodeBuilder
}
