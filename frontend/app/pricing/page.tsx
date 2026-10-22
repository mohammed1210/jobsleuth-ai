import HeaderClient from '@/components/HeaderClient';
import UpgradeButton from '@/components/UpgradeButton';

export const metadata = { title: 'Pricing • JobSleuth AI' };

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <HeaderClient />
      <main className="mx-auto max-w-6xl px-6 py-14">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h1 className="text-4xl font-bold text-gray-900">Simple, clear pricing</h1>
          <p className="mt-4 text-gray-600">Explore jobs and decide when to upgrade your application support. Paid plans renew monthly and can be cancelled.</p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <section className="card flex flex-col p-7">
            <h2 className="text-xl font-bold">Free</h2>
            <p className="mt-3 text-4xl font-bold">£0</p>
            <p className="mt-2 flex-1 text-gray-600">Get started with JobSleuth and explore the application journey.</p>
            <span className="mt-8 text-sm font-semibold text-gray-600">Free access</span>
          </section>
          <section className="card flex flex-col border-2 border-brand-500 p-7">
            <h2 className="text-xl font-bold">Career Plus</h2>
            <p className="mt-3 text-4xl font-bold">£4.99<span className="ml-1 text-base font-normal text-gray-600">/month</span></p>
            <p className="mt-2 flex-1 text-gray-600">An affordable next step for people applying regularly.</p>
            <div className="mt-8"><UpgradeButton plan="career_plus">Choose Career Plus</UpgradeButton></div>
          </section>
          <section className="card flex flex-col p-7">
            <h2 className="text-xl font-bold">Pro</h2>
            <p className="mt-3 text-4xl font-bold">£9.99<span className="ml-1 text-base font-normal text-gray-600">/month</span></p>
            <p className="mt-2 flex-1 text-gray-600">For active job seekers who want higher-tier application support.</p>
            <div className="mt-8"><UpgradeButton plan="pro">Choose Pro</UpgradeButton></div>
          </section>
        </div>
        <p className="mx-auto mt-8 max-w-3xl text-center text-sm text-gray-600">
          Subscription checkout remains subject to final activation and plan-access validation. Feature allowances will be displayed once they are enforced.
        </p>
      </main>
    </div>
  );
}
