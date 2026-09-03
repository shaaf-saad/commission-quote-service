import { useMutation } from '@tanstack/react-query'
import { generateQuote } from './api/quotes'
import QuoteForm from './components/QuoteForm'
import QuoteResult from './components/QuoteResult'

export default function App() {
  const quoteMutation = useMutation({ mutationFn: generateQuote, retry: false })
  const isDemo = import.meta.env.VITE_DEMO_MODE === 'true'

  return (
    <main className="min-h-screen px-5 py-8 sm:px-8 lg:px-12">
      <div className="mx-auto max-w-6xl">
        <header className="mb-10 flex items-center justify-between border-b border-white/10 pb-6">
          <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-lg bg-amber-300 font-black text-slate-950">CQ</span><span className="text-sm font-semibold tracking-wide text-white">Lending Platform</span></div>
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Staff workspace</span>
        </header>
        <section className="grid gap-8 lg:grid-cols-[0.86fr_1.14fr] lg:items-stretch">
          <div className="py-4 lg:py-14"><p className="mb-5 text-sm font-bold uppercase tracking-[0.25em] text-amber-300">Commission quote</p><h1 className="max-w-xl text-5xl font-semibold leading-[1.04] tracking-tight text-white sm:text-6xl">A clearer view of every loan.</h1><p className="mt-6 max-w-lg text-lg leading-8 text-slate-400">Turn application details into a precise commission estimate, backed by the vendor calculation service.</p><div className="mt-10 flex gap-8 text-sm"><div><p className="font-semibold text-white">01</p><p className="mt-1 text-slate-500">Enter details</p></div><div><p className="font-semibold text-white">02</p><p className="mt-1 text-slate-500">Review quote</p></div></div></div>
          <div className="grid gap-5 rounded-2xl border border-white/10 bg-slate-900/80 p-6 shadow-2xl shadow-black/20 sm:p-8"><div className="flex items-center justify-between border-b border-white/10 pb-4 text-xs"><span className="font-semibold uppercase tracking-[0.16em] text-slate-500">{isDemo ? 'Pages demo mode' : 'Live BFF mode'}</span><span className={`rounded-full px-2.5 py-1 font-medium ${isDemo ? 'bg-sky-400/10 text-sky-300' : 'bg-emerald-400/10 text-emerald-300'}`}>{isDemo ? 'Interactive preview' : 'Connected'}</span></div><QuoteForm onSubmit={(payload) => quoteMutation.mutate(payload)} isPending={quoteMutation.isPending} /><div className="border-t border-white/10 pt-6"><QuoteResult quote={quoteMutation.data} error={quoteMutation.error} isPending={quoteMutation.isPending} /></div></div>
        </section>
        <section className="mt-20 border-t border-white/10 pt-10"><div className="grid gap-8 md:grid-cols-[0.7fr_1.3fr]"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-amber-300">How it works</p><h2 className="mt-3 text-3xl font-semibold text-white">A small system with a clear boundary.</h2></div><div className="grid gap-4 sm:grid-cols-3"><div className="info-block"><span className="info-number">01</span><h3>React UI</h3><p>Captures loan details and presents each request state with an accessible, responsive interface.</p></div><div className="info-block"><span className="info-number">02</span><h3>FastAPI BFF</h3><p>Validates requests, protects the vendor key, and translates vendor failures for the browser.</p></div><div className="info-block"><span className="info-number">03</span><h3>Mock vendor</h3><p>Calculates deterministic rates while simulating authentication and intermittent outages.</p></div></div></div></section>
      </div>
    </main>
  )
}
