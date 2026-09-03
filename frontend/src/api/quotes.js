const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''
const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'

function createDemoQuote(payload) {
  const baseRates = { A: 0.015, B: 0.0225, C: 0.035, D: 0.05 }
  const termBonus = Math.min(Math.floor(payload.loanTermInMonths / 12) * 0.001, 0.01)
  const commissionRate = baseRates[payload.riskBand] + termBonus
  return new Promise((resolve) => {
    window.setTimeout(() => resolve({
      quoteId: `demo-${Date.now()}`,
      commissionRate: commissionRate.toFixed(4),
      totalCommission: (payload.loanAmount * commissionRate).toFixed(2),
      ...payload,
    }), 450)
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
    throw new Error(detail)
  }

  return data
}
