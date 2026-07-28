import { LandingHero } from "@/components/landing/LandingHero";

export default function Home() {
  return (
    <main className="landing-page flex flex-1 flex-col pb-16 pt-6 sm:pb-20 sm:pt-10">
      <LandingHero />
    </main>
  );
}
