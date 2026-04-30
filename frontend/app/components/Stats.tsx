const stats = [
  { label: 'Restaurants', value: '10,000+' },
  { label: 'Happy Diners', value: '50,000+' },
  { label: 'Cities', value: '25+' },
  { label: 'Rating', value: '4.9/5' },
];

export function Stats() {
  return (
    <div className="py-16 bg-primary-600">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {stats.map((stat) => (
            <div key={stat.label}>
              <div className="text-4xl font-bold text-white">{stat.value}</div>
              <div className="mt-2 text-primary-100">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
