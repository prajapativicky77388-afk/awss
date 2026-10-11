import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AquaMesh — Autonomous Urban Hydro-Sentinel",
  description:
    "Edge-first, multi-agent AI system that unifies flood control, groundwater recharge optimization, and smart-tanker distribution into a single predictive loop. By Team Grey Coder.",
  keywords: [
    "AquaMesh",
    "urban water management",
    "flood prediction",
    "drought management",
    "smart city",
    "IoT",
    "AI agents",
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
