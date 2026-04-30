const steps = [
  {
    number: '01',
    title: 'Set Your Preferences',
    description: 'Enter your location, budget, cuisine preferences, and minimum rating requirements.',
  },
  {
    number: '02',
    title: 'AI Analysis',
    description: 'Our AI processes thousands of restaurants and matches them with your personal preferences.',
  },
  {
    number: '03',
    title: 'Get Recommendations',
    description: 'Receive personalized restaurant recommendations with detailed explanations and ratings.',
  },
  {
    number: '04',
    title: 'Provide Feedback',
    description: 'Rate and review restaurants to help our AI learn and improve future recommendations.',
  },
];

export function HowItWorks() {
  return (
    <div className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900">How It Works</h2>
          <p className="mt-4 text-lg text-gray-600">
            Get personalized restaurant recommendations in four simple steps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step) => (
            <div key={step.number} className="relative">
              <div className="text-6xl font-bold text-primary-200">{step.number}</div>
              <h3 className="mt-4 text-xl font-semibold text-gray-900">{step.title}</h3>
              <p className="mt-2 text-gray-600">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
