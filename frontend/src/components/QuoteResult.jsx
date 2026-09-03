const money = new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' })

export default function QuoteResult({ quote, error, isPending }) {
  if (isPending) {
    return <div className="flex min-h-80 flex-col items-center justify-center text-center"><div className="mb-5 h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-amber-300" /><p className="font-medium text-white">Calculating your quote</p><p className="mt-2 text-sm text-slate-400">Contacting the Commission Quote API...</p></div>
  }

  if (error) {
    return <div className="flex min-h-80 flex-col justify-center"><p className="text-xs font-bold uppercase tracking-[0.2em] text-rose-300">Request failed</p><h2 className="mt-3 text-2xl font-semibold text-white">The quote could not be generated</h2><p className="mt-3 leading-7 text-slate-400">{error.message}</p><p className="mt-6 text-sm text-slate-500">Check the vendor service and try again.</p></div>
  }

  if (!quote) {
    return <div className="flex min-h-80 flex-col justify-center"><p className="text-6xl font-semibold tracking-tight text-slate-700">01</p><h2 className="mt-4 text-2xl font-semibold text-white">Your quote appears here</h2><p className="mt-3 max-w-sm leading-7 text-slate-400">Rates and total commission will be shown after the vendor responds.</p></div>
  }

  return <div className="min-h-80"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">Quote ready</p><h2 className="mt-3 text-2xl font-semibold text-white">Commission estimate</h2></div><span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-300">Success</span></div><div className="mt-10 grid gap-6 sm:grid-cols-2"><div><p className="text-sm text-slate-400">Commission rate</p><p className="mt-2 text-3xl font-semibold text-amber-300">{(Number(quote.commissionRate) * 100).toFixed(2)}%</p></div><div><p className="text-sm text-slate-400">Total commission</p><p className="mt-2 text-3xl font-semibold text-white">{money.format(Number(quote.totalCommission))}</p></div></div><div className="mt-10 border-t border-white/10 pt-5 text-sm text-slate-500">Quote ID <span className="ml-2 break-all font-mono text-slate-300">{quote.quoteId}</span></div></div>
}
