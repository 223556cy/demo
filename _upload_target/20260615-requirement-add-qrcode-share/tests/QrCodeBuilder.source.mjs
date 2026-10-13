// Node port of QrCodeBuilder.ets for offline testing
// Mirrors the ArkTS implementation byte-for-byte (except Node's encodeURIComponent)

export const MAX_PAYLOAD_LENGTH = 200
export const PAYLOAD_PREFIX = 'opencalc://calc?expr='
export const RESULT_PREFIX = '&res='
export const TRUNCATED_FLAG = '&truncated=1'

export function buildSharePayload(expression, result) {
  const safeExpr = (expression === undefined || expression === null) ? '' : expression
  const safeRes  = (result  === undefined || result  === null) ? '' : result

  const encExpr = encodeURIComponent(safeExpr)
  const encRes  = encodeURIComponent(safeRes)

  let payload = PAYLOAD_PREFIX + encExpr + RESULT_PREFIX + encRes

  if (payload.length <= MAX_PAYLOAD_LENGTH) return payload

  const fixedTail = RESULT_PREFIX + encRes + TRUNCATED_FLAG
  const maxExprLen = MAX_PAYLOAD_LENGTH - PAYLOAD_PREFIX.length - fixedTail.length
  if (maxExprLen > 0) {
    const truncatedExpr = encExpr.substring(0, maxExprLen)
    return PAYLOAD_PREFIX + truncatedExpr + fixedTail
  }

  return payload.substring(0, MAX_PAYLOAD_LENGTH)
}

export class QrCodeBuilder {
  static MAX_PAYLOAD_LENGTH = MAX_PAYLOAD_LENGTH
  static PAYLOAD_PREFIX = PAYLOAD_PREFIX
  static RESULT_PREFIX = RESULT_PREFIX
  static TRUNCATED_FLAG = TRUNCATED_FLAG
  static buildSharePayload = buildSharePayload
}
