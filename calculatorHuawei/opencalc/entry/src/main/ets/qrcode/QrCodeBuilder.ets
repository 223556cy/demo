// OpenCalc — QR 码分享内容生成器
// aid-workflow 20260615: Issue #13 一键分享二维码
// 纯函数模块，便于 100% 单元测试覆盖

/** QR payload 字符上限（保守值，规避 Kit 边界问题） */
export const MAX_PAYLOAD_LENGTH: number = 200

/** QR payload 前缀（自定义 URL scheme） */
export const PAYLOAD_PREFIX: string = 'opencalc://calc?expr='

/** 结果字段前缀 */
export const RESULT_PREFIX: string = '&res='

/** 截断标记 */
export const TRUNCATED_FLAG: string = '&truncated=1'

/**
 * aid-workflow 20260615: 生成 QR 码分享 payload
 * @param expression 用户输入的算式（如 "1+2"）
 * @param result 计算结果（如 "3"）
 * @returns URL 编码后的 payload（如 "opencalc://calc?expr=1%2B2&res=3"）
 *          超长则截断 expression 并追加 &truncated=1
 *          result 单独超长时截断整个 payload 至 200 字符
 */
export function buildSharePayload(expression: string, result: string): string {
  const safeExpr: string = (expression === undefined || expression === null) ? '' : expression
  const safeRes: string = (result === undefined || result === null) ? '' : result

  const encExpr: string = encodeURIComponent(safeExpr)
  const encRes: string = encodeURIComponent(safeRes)

  let payload: string = PAYLOAD_PREFIX + encExpr + RESULT_PREFIX + encRes

  if (payload.length <= MAX_PAYLOAD_LENGTH) return payload

  // 超长截断：优先截断 expr，保留 result 完整
  const fixedTail: string = RESULT_PREFIX + encRes + TRUNCATED_FLAG
  const maxExprLen: number = MAX_PAYLOAD_LENGTH - PAYLOAD_PREFIX.length - fixedTail.length
  if (maxExprLen > 0) {
    const truncatedExpr: string = encExpr.substring(0, maxExprLen)
    return PAYLOAD_PREFIX + truncatedExpr + fixedTail
  }

  // result 本身就超过上限（极罕见），直接截断整个 payload
  return payload.substring(0, MAX_PAYLOAD_LENGTH)
}

/** 命名空间风格导出（与项目内 HistoryFilter / NumberFormatter 一致） */
export class QrCodeBuilder {
  static readonly MAX_PAYLOAD_LENGTH = MAX_PAYLOAD_LENGTH
  static readonly PAYLOAD_PREFIX = PAYLOAD_PREFIX
  static readonly RESULT_PREFIX = RESULT_PREFIX
  static readonly TRUNCATED_FLAG = TRUNCATED_FLAG
  static buildSharePayload = buildSharePayload
}
