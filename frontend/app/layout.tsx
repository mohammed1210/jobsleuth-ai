// Layout component for JobSleuth AI
import type { Metadata, Viewport } from 'next';
import './globals.css';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://jobsleuth-frontend.vercel.app';
const ABS = (p: string) => new URL(p, SITE_URL);

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'JobSleuth AI',
    template: '%s · JobSleuth AI',
  },
  description: 'AI‑powered job sourcing: analyse salary, role type and score jobs.',
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, 'max-snippet': -1, 'max-image-preview': 'large', 'max-video-preview': -1 },
  },
  alternates: {
    canonical: '/',
    languages: { 'en-GB': '/en-GB', en: '/' },
  },
  openGraph: {
    type: 'website',
    url: ABS('/'),
    title: 'JobSleuth AI',
    siteName: 'JobSleuth AI',
    description: 'AI‑powered job sourcing platform.',
    images: [ { url: ABS('/og/cover.png'), width: 1200, height: 630, alt: 'JobSleuth – AI job sourcing' } ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'JobSleuth AI',
    description: 'AI‑powered job sourcing platform.',
    images: [ABS('/og/cover.png')],
    creator: '@jobsleuth',
  },
  icons: {
    icon: [ { url: '/icons/favicon-32x32.png', sizes: '32x32', type: 'image/png' }, { url: '/icons/favicon-16x16.png', sizes: '16x16', type: 'image/png' } ],
    apple: [ { url: '/icons/apple-touch-icon.png', sizes: '180x180' } ],
    shortcut: ['/favicon.ico'],
  },
  manifest: ABS('/site.webmanifest').toString(),
  verification: { google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION || undefined },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#09090b' },
  ],
  width: 'device-width',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 bg-neutral-900 text-white px-3 py-2 rounded"
        >
          Skip to content
        </a>
        <main id="main" className="min-h-[calc(100dvh-var(--header-h,56px))] focus:outline-none">
          {children}
        </main>
      </body>
    </html>
  );
}