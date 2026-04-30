import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { HowItWorks } from './components/HowItWorks';
import { Stats } from './components/Stats';
import { CTASection } from './components/CTASection';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <Hero />
      <Features />
      <HowItWorks />
      <Stats />
      <CTASection />
    </div>
  );
}
