import { useState } from 'react'

const initialValues = {
  loanAmount: '',
  loanTermInMonths: '',
  riskBand: '',
}

export default function QuoteForm({ onSubmit, isPending }) {
  const [values, setValues] = useState(initialValues)
  const [validationError, setValidationError] = useState('')

  function updateValue(event) {
    setValues((current) => ({ ...current, [event.target.name]: event.target.value }))
    setValidationError('')
  }

  function submit(event) {
    event.preventDefault()
    const payload = {
      loanAmount: Number(values.loanAmount),
      loanTermInMonths: Number(values.loanTermInMonths),
      riskBand: values.riskBand,
    }

    if (!Number.isFinite(payload.loanAmount) || payload.loanAmount <= 0 || payload.loanAmount > 10000000) {
      setValidationError('Enter a loan amount between 0.01 and 10,000,000.')
      return
    }
    if (!Number.isInteger(payload.loanTermInMonths) || payload.loanTermInMonths < 1 || payload.loanTermInMonths > 360) {
      setValidationError('Enter a whole-number term between 1 and 360 months.')
      return
    }
    if (!payload.riskBand) {
      setValidationError('Select a risk band to continue.')
      return
    }

    onSubmit(payload)
  }

  return (
    <form onSubmit={submit} className="space-y-6" noValidate>
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-amber-300">Loan profile</p>
        <h2 className="mt-2 text-2xl font-semibold text-white">Build a quote</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">Provide the application details and we will calculate your quote.</p>
      </div>

      <div className="space-y-5">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">Loan amount <span className="text-slate-500">AUD</span></span>
          <input name="loanAmount" value={values.loanAmount} onChange={updateValue} type="number" min="0.01" max="10000000" step="0.01" placeholder="250000.00" className="input" required />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">Loan term <span className="text-slate-500">months</span></span>
          <input name="loanTermInMonths" value={values.loanTermInMonths} onChange={updateValue} type="number" min="1" max="360" step="1" placeholder="360" className="input" required />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">Risk band</span>
          <select name="riskBand" value={values.riskBand} onChange={updateValue} className="input" required>
            <option value="">Select a band</option>
            <option value="A">A - lowest risk</option>
            <option value="B">B - moderate</option>
            <option value="C">C - elevated</option>
            <option value="D">D - highest risk</option>
          </select>
        </label>
      </div>

      {validationError && <p className="rounded-lg border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200" role="alert">{validationError}</p>}

      <button type="submit" disabled={isPending} className="button-primary">
        {isPending ? 'Requesting quote...' : 'Generate quote'}
        <span aria-hidden="true">-&gt;</span>
      </button>
    </form>
  )
}
