import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Ladder Labs | Fleet Commander",
  description: "High-performance AI Trading Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} antialiased selection:bg-primary/30`}
      >
        <div className="relative min-h-screen">
          {/* Subtle Background Glows */}
          <div className="fixed top-0 left-0 w-full h-full overflow-hidden -z-10 bg-[#050505]">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/5 blur-[120px] rounded-full" />
          </div>

          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
