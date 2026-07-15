import type { Metadata } from "next";
import { Suspense } from "react";
import { IBM_Plex_Mono, Work_Sans } from "next/font/google";
import { Header } from "@/components/layout/Header";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ProfileProvider } from "@/lib/profile";
import { cn } from "@/lib/utils";
import "./globals.css";

const workSans = Work_Sans({
  subsets: ["latin"],
  variable: "--font-ui",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-data",
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "SteadyFit",
  description: "Your multi-agent AI Coaching Team fitness copilot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn("h-full", workSans.variable, plexMono.variable, "font-sans")}
    >
      <body className="flex min-h-dvh flex-col bg-navy text-navy-text">
        <TooltipProvider>
          <Suspense fallback={null}>
            <ProfileProvider>
              <Header />
              <div className="page-shell flex min-h-0 flex-1 flex-col">{children}</div>
            </ProfileProvider>
          </Suspense>
        </TooltipProvider>
      </body>
    </html>
  );
}
