const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''
const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'
const demoFailureRate = Number(import.meta.env.VITE_DEMO_FAILURE_RATE || '0.5')

function demoReferenceId() {
  return `demo-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`
}

function createDemoQuote(payload) {
  const baseRates = { A: 0.015, B: 0.0225, C: 0.035, D: 0.05 }
  const termBonus = Math.min(Math.floor(payload.loanTermInMonths / 12) * 0.001, 0.01)
  const commissionRate = baseRates[payload.riskBand] + termBonus
  return new Promise((resolve, reject) => {
    window.setTimeout(() => {
      if (Math.random() < demoFailureRate) {
        const error = new Error('The quote service is temporarily unavailable. Please try again.')
        error.referenceId = demoReferenceId()
        reject(error)
        return
      }
      resolve({
        quoteId: `demo-${Date.now()}`,
        commissionRate: commissionRate.toFixed(4),
        totalCommission: (payload.loanAmount * commissionRate).toFixed(2),
        ...payload,
      })
    }, 450)
  })
}

export async function generateQuote(payload) {
  if (demoMode) return createDemoQuote(payload)

  const response = await fetch(`${apiBaseUrl}/api/quotes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg || JSON.stringify(item)).join(' ')
      : data.detail || 'Quote generation failed.'
    const error = new Error(detail)
    error.referenceId = response.headers.get('X-Correlation-ID')
      || detail.match(/Reference ID:\s*([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})/i)?.[1]
    throw error
  }

  return data
}
