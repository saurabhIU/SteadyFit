"use client";

import { TryItYourself } from "@/components/landing/TryItYourself";
import { PlanPhonePreview } from "@/components/landing/PlanPhonePreview";

const DEMO_LOOM_URL =
  process.env.NEXT_PUBLIC_DEMO_LOOM_URL ??
  "https://youtu.be/2gTdga4oN6c";

export function LandingHero() {
  return (
    <section className="landing-hero content-width">
      <div className="landing-hero-grid">
        <div className="landing-hero-copy">
          <p className="landing-eyebrow">AI Coaching Team · For Busy People</p>
          <h1 className="landing-headline">
            A plan that bends when your week doesn&apos;t.
          </h1>
          <p className="landing-subhead">
            A team of AI agents — not one chatbot — that notice when life gets
            in the way and re-plan around it automatically.
          </p>

          <div className="landing-cta-row">
            <TryItYourself
              label="Try it yourself — no signup"
              hideHint
              className="items-stretch sm:items-start"
            />
            <a
              href={DEMO_LOOM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="landing-demo-link"
            >
              Watch the 2-minute demo
            </a>
          </div>

          <p className="landing-trust">
            No sign-up needed · Free to try · Built by one engineer in 6 weeks
          </p>
        </div>

        <div className="landing-hero-visual">
          <PlanPhonePreview />
        </div>
      </div>
    </section>
  );
}
