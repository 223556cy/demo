// GraphPageLifecycle.source.mjs — 共享源码(被 GraphPageLifecycle.test.mjs 引用)
// Issue #37 — 模拟 GraphPage.aboutToAppear() 时序

'use strict'

export class MockPreferencesStore {
  constructor (initDelayMs = 5) {
    this._initialized = false
    this._initDelay = initDelayMs
  }

  async init () {
    await new Promise(resolve => setTimeout(resolve, this._initDelay))
    this._initialized = true
  }

  async getRadiansDefault () {
    if (!this._initialized) {
      throw new Error('prefs not initialized')
    }
    return false
  }

  async getTheme () {
    if (!this._initialized) {
      throw new Error('prefs not initialized')
    }
    return 0
  }
}

export class MockGraphViewModel {
  constructor () {
    this.expression = 'sin(x)'
    this.xMin = -2 * Math.PI
    this.xMax = 2 * Math.PI
    this.samples = 200
    this.isDegree = false
    this.computeCallLog = []
  }

  setRadianMode (isDeg) {
    this.isDegree = isDeg
  }

  compute (eventId) {
    this.computeCallLog.push({
      eventId,
      isDegreeAtCall: this.isDegree,
      timestamp: Date.now()
    })
  }

  evaluateAt (x) {
    if (this.isDegree) {
      return Math.sin(x * Math.PI / 180)
    } else {
      return Math.sin(x)
    }
  }
}

// Buggy 版本: setTimeout 中的 compute 先于 init().then() 中的 loadPrefs 触发
export class MockGraphPageBuggy {
  constructor (vm, prefs) {
    this.vm = vm
    this.prefs = prefs
    this._loadPrefsStartEventId = -1
    this._loadPrefsEndEventId = -1
    this._eventCounter = 0
  }

  aboutToAppear () {
    // 微任务链: init → loadPrefs
    this.prefs.init().then(() => {
      this._eventCounter++
      this._loadPrefsStartEventId = this._eventCounter
      return this.loadPrefs()
    }).then(() => {
      this._eventCounter++
      this._loadPrefsEndEventId = this._eventCounter
    })

    // 宏任务: compute (setTimeout 0)
    setTimeout(() => {
      this._eventCounter++
      this.vm.compute(this._eventCounter)
    }, 0)
  }

  async loadPrefs () {
    if (!this.prefs) return
    const radianMode = await this.prefs.getRadiansDefault()
    this.vm.setRadianMode(false)  // aid-workflow 20260708: Issue #37 Task 5.3 force radians
  }

  async waitAll (timeoutMs = 100) {
    await new Promise(resolve => setTimeout(resolve, timeoutMs))
  }
}

// Fixed 版本: compute 移入 init().then(loadPrefs().then(compute))
// + 强制 radian 模式 (Task 5.3 扩展修复,解决用户默认角度制导致直线问题)
export class MockGraphPageFixed {
  constructor (vm, prefs) {
    this.vm = vm
    this.prefs = prefs
    this._loadPrefsStartEventId = -1
    this._loadPrefsEndEventId = -1
    this._eventCounter = 0
  }

  aboutToAppear () {
    this.prefs.init()
      .then(() => {
        this._eventCounter++
        this._loadPrefsStartEventId = this._eventCounter
        return this.loadPrefs()
      })
      .then(() => {
        this._eventCounter++
        this._loadPrefsEndEventId = this._eventCounter
        this._eventCounter++
        this.vm.compute(this._eventCounter)
      })
      .catch(() => {
        this._eventCounter++
        this.vm.compute(this._eventCounter)
      })
  }

  async loadPrefs () {
    if (!this.prefs) return
    // Task 5.3 扩展修复: GraphPage 强制 radian 模式,跟随用户偏好导致 sin 直线
    this.vm.setRadianMode(false)
  }

  async waitAll (timeoutMs = 100) {
    await new Promise(resolve => setTimeout(resolve, timeoutMs))
  }
}