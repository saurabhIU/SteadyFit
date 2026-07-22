import { TryItYourself } from "@/components/landing/TryItYourself";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="flex max-w-lg flex-col items-center gap-3 text-center">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-navy-muted">
          SteadyFit
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-navy-text sm:text-4xl">
          Your AI coaching team
        </h1>
        <p className="text-sm leading-relaxed text-navy-muted sm:text-base">
          Adaptive training and nutrition for busy adults — start a guest
          session and meet the coach in under a minute.
        </p>
      </div>
      <TryItYourself />
    </main>
  );
}
