import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';
import { Providers } from './providers';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'DineSmart - AI-Powered Restaurant Recommendations',
  description: 'Discover your perfect dining experience with AI-powered restaurant recommendations personalized just for you.',
  keywords: ['restaurant', 'recommendation', 'AI', 'dining', 'food', 'personalized'],
  authors: [{ name: 'DineSmart Team' }],
  openGraph: {
    title: 'DineSmart - AI-Powered Restaurant Recommendations',
    description: 'Discover your perfect dining experience with AI-powered restaurant recommendations personalized just for you.',
    type: 'website',
    locale: 'en_US',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-grow">
              {children}
            </main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}
