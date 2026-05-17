Page({
  data: {
    display: '0',
    expression: '',
    currentInput: '0',
    previousInput: '',
    operator: null,
    shouldResetDisplay: false,
    hasResult: false
  },

  // 数字输入
  onNumber(e) {
    const num = e.currentTarget.dataset.num
    let { currentInput, shouldResetDisplay, hasResult } = this.data

    if (shouldResetDisplay || hasResult) {
      currentInput = num
      this.setData({
        currentInput,
        display: num,
        shouldResetDisplay: false,
        hasResult: false,
        expression: hasResult ? '' : this.data.expression
      })
      return
    }

    if (currentInput === '0') {
      currentInput = num
    } else {
      if (currentInput.replace('-', '').length >= 15) return
      currentInput += num
    }

    this.setData({ currentInput, display: currentInput })
  },

  // 小数点
  onDot() {
    let { currentInput, shouldResetDisplay, hasResult } = this.data

    if (shouldResetDisplay || hasResult) {
      this.setData({
        currentInput: '0.',
        display: '0.',
        shouldResetDisplay: false,
        hasResult: false
      })
      return
    }

    if (currentInput.includes('.')) return

    currentInput += '.'
    this.setData({ currentInput, display: currentInput })
  },

  // 运算符
  onOperator(e) {
    const op = e.currentTarget.dataset.op
    const { currentInput, previousInput, operator, hasResult } = this.data

    let prev = previousInput
    let result = currentInput

    // 连续按运算符时只更新运算符
    if (this.data.shouldResetDisplay && !hasResult) {
      this.setData({ operator: op, expression: `${prev} ${op}` })
      return
    }

    // 链式运算
    if (operator && previousInput && !hasResult) {
      result = String(this._calculate(parseFloat(previousInput), parseFloat(currentInput), operator))
      result = this._formatNumber(result)
    }

    this.setData({
      previousInput: result,
      operator: op,
      currentInput: result,
      display: result,
      shouldResetDisplay: true,
      hasResult: false,
      expression: `${result} ${op}`
    })
  },

  // 等号
  onEquals() {
    const { currentInput, previousInput, operator } = this.data
    if (!operator || !previousInput) return

    const a = parseFloat(previousInput)
    const b = parseFloat(currentInput)
    let result = this._calculate(a, b, operator)

    if (result === null) {
      this.setData({ display: '错误', expression: '', currentInput: '0', previousInput: '', operator: null, shouldResetDisplay: true, hasResult: false })
      return
    }

    const formatted = this._formatNumber(String(result))
    this.setData({
      display: formatted,
      expression: `${previousInput} ${operator} ${currentInput} =`,
      currentInput: formatted,
      previousInput: '',
      operator: null,
      shouldResetDisplay: true,
      hasResult: true
    })
  },

  // 清除
  onClear() {
    this.setData({
      display: '0',
      expression: '',
      currentInput: '0',
      previousInput: '',
      operator: null,
      shouldResetDisplay: false,
      hasResult: false
    })
  },

  // 正负切换
  onToggleSign() {
    let { currentInput } = this.data
    if (currentInput === '0') return

    if (currentInput.startsWith('-')) {
      currentInput = currentInput.slice(1)
    } else {
      currentInput = '-' + currentInput
    }
    this.setData({ currentInput, display: currentInput })
  },

  // 百分比
  onPercent() {
    const { currentInput } = this.data
    const val = parseFloat(currentInput) / 100
    const formatted = this._formatNumber(String(val))
    this.setData({ currentInput: formatted, display: formatted })
  },

  // 计算核心
  _calculate(a, b, op) {
    switch (op) {
      case '+': return a + b
      case '−': return a - b
      case '×': return a * b
      case '÷':
        if (b === 0) return null
        return a / b
      default: return b
    }
  },

  // 格式化数字（避免浮点精度问题，限制显示长度）
  _formatNumber(numStr) {
    const num = parseFloat(numStr)
    if (isNaN(num)) return '错误'

    // 整数且不超长直接返回
    if (Number.isInteger(num) && Math.abs(num) < 1e15) {
      return String(num)
    }

    // 超大或超小用科学计数法
    if (Math.abs(num) >= 1e15 || (Math.abs(num) < 1e-6 && num !== 0)) {
      return num.toExponential(6).replace(/\.?0+e/, 'e')
    }

    // 修正浮点精度
    const fixed = parseFloat(num.toPrecision(12))
    return String(fixed)
  }
})
