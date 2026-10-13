import { router } from '@kit.ArkUI'

@Entry
@Component
struct Index {
  aboutToAppear(): void {
    router.replaceUrl({ url: 'pages/CalculatorPage' })
  }

  build() {
    Column() {
      Text('OpenCalc')
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
        .fontColor('#FFFFFF')
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
    .backgroundColor('#1a1a2e')
  }
}
