'use client';

interface UpgradeButtonProps {
  priceId: string;
  children: React.ReactNode;
}

export default function UpgradeButton({ priceId, children }: UpgradeButtonProps) {
  const handleUpgrade = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/stripe/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ price_id: priceId }),
      });
      
      const data = await response.json();
      
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (error) {
      console.error('Failed to initiate checkout:', error);
    }
  };
  
  return (
    <button 
      onClick={handleUpgrade}
      className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded"
    >
      {children}
    </button>
  );
}
