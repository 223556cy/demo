// OpenCalc — 测试入口（hypium 风格）
// Issue #22 程序员模式 — 注册所有 test 套件
// Issue #26 函数图像 — 注册 PlotUtils + evaluateAt test 套件
// aid-workflow 20260617: Issue #27 分数/小数显示切换 — 注册 FractionUtil 套件
// Issue #28 记忆槽 — 注册 MemorySlots test 套件
// aid-workflow 20260618: Issue #29 键盘滑动 — 注册 KeyboardSwipe 套件

import expressionPercentTest from './ets/calculator/Expression.test.ets'
import unitConverterTest from './ets/common/UnitConverter.test.ets'
import naturalLanguageParserTest from './ets/common/NaturalLanguageParser.test.ets'
import baseConverterTest from './ets/calculator/BaseConverter.test.ets'
import plotUtilsTest from './ets/common/PlotUtils.test.ets'
import calculatorEvaluateAtTest from './ets/calculator/Calculator.test.ets'
import fractionUtilTest from './ets/common/FractionUtil.test.ets'
import memorySlotsTest from './ets/calculator/MemorySlots.test.ets'
import keyboardSwipeTest from './ets/keyboard/KeyboardSwipe.test.ets'

export default function testsuite() {
  expressionPercentTest()
  unitConverterTest()
  naturalLanguageParserTest()
  baseConverterTest()
  plotUtilsTest()
  calculatorEvaluateAtTest()
  fractionUtilTest()
  memorySlotsTest()
  keyboardSwipeTest()
}
