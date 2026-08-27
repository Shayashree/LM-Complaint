import React from 'react';

interface ProductImageSVGProps {
  productId: string;
  highlightedBox?: string | null;
  showAllBoxes?: boolean;
  zoom?: number;
  rotation?: number;
  panX?: number;
  panY?: number;
}

export const ProductImageSVG: React.FC<ProductImageSVGProps> = ({
  productId,
  highlightedBox,
  showAllBoxes = false,
  zoom = 1,
  rotation = 0,
  panX = 0,
  panY = 0
}) => {
  // Define bounding boxes in percentages [x, y, w, h]
  const boxes: Record<string, Record<string, { rect: [number, number, number, number]; label: string; color: string }>> = {
    "LM-2026-00121": { // Parle-G
      "Product Name": { rect: [10, 35, 80, 15], label: "NAME", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Net Quantity": { rect: [10, 60, 35, 10], label: "NET QTY", color: "border-green-500 bg-green-500/10 text-green-700" },
      "MRP": { rect: [50, 60, 42, 10], label: "MRP", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Manufacturer Name/Address": { rect: [8, 73, 84, 11], label: "MFG DETAILS", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Consumer Care Phone/Email": { rect: [8, 86, 84, 11], label: "CONSUMER CARE", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Date of Packaging": { rect: [42, 51, 24, 7], label: "MFD DATE", color: "border-green-500 bg-green-500/10 text-green-700" }
    },
    "LM-2026-00122": { // Surf Excel
      "Product Name": { rect: [8, 12, 84, 16], label: "NAME", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Net Quantity": { rect: [10, 80, 38, 10], label: "NET QTY", color: "border-green-500 bg-green-500/10 text-green-700" },
      "MRP": { rect: [50, 80, 42, 10], label: "MRP (VIOLATION)", color: "border-red-500 bg-red-500/10 text-red-700" },
      "Manufacturer Name/Address": { rect: [8, 62, 84, 12], label: "MFG DETAILS", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Consumer Care Phone/Email": { rect: [8, 48, 84, 10], label: "CONSUMER CARE (MISSING)", color: "border-red-500 border-dashed bg-red-500/5 text-red-700" },
      "Date of Packaging": { rect: [12, 32, 28, 8], label: "MFD DATE", color: "border-green-500 bg-green-500/10 text-green-700" }
    },
    "LM-2026-00123": { // Haldiram's
      "Product Name": { rect: [15, 18, 70, 14], label: "NAME", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Net Quantity": { rect: [10, 75, 35, 10], label: "NET QTY", color: "border-green-500 bg-green-500/10 text-green-700" },
      "MRP": { rect: [48, 75, 44, 10], label: "MRP", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Manufacturer Name/Address": { rect: [8, 86, 84, 10], label: "MFG DETAILS", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Consumer Care Phone/Email": { rect: [10, 48, 80, 10], label: "CONSUMER CARE", color: "border-green-500 bg-green-500/10 text-green-700" },
      "Date of Packaging": { rect: [42, 34, 30, 8], label: "MFD DATE (WARNING)", color: "border-amber-500 bg-amber-500/10 text-amber-700" }
    }
  };

  const activeBoxes = boxes[productId] || {};

  const renderSVGContent = () => {
    switch (productId) {
      case "LM-2026-00121": // Parle-G
        return (
          <svg viewBox="0 0 400 500" className="w-full h-full select-none" xmlns="http://www.w3.org/2000/svg">
            {/* Background wrapper */}
            <rect width="400" height="500" rx="8" fill="#fef9c3" stroke="#ca8a04" strokeWidth="6" />
            
            {/* Tricolor corner indicator to denote Indian compliance check */}
            <path d="M 0 0 L 60 0 L 0 60 Z" fill="#f58220" />
            <path d="M 0 20 L 40 0" stroke="#ffffff" strokeWidth="4" />
            <path d="M 0 40 L 20 0" stroke="#059669" strokeWidth="4" />

            {/* Parle-G stripes pattern */}
            <g opacity="0.15">
              <line x1="0" y1="100" x2="400" y2="100" stroke="#ca8a04" strokeWidth="8" />
              <line x1="0" y1="120" x2="400" y2="120" stroke="#ca8a04" strokeWidth="8" />
              <line x1="0" y1="140" x2="400" y2="140" stroke="#ca8a04" strokeWidth="8" />
              <line x1="0" y1="300" x2="400" y2="300" stroke="#ca8a04" strokeWidth="8" />
              <line x1="0" y1="320" x2="400" y2="320" stroke="#ca8a04" strokeWidth="8" />
            </g>

            {/* Brand Logo & Name */}
            <rect x="80" y="40" width="240" height="70" rx="6" fill="#dc2626" stroke="#ffffff" strokeWidth="3" />
            <text x="200" y="80" fill="#ffffff" fontFamily="sans-serif" fontSize="34" fontWeight="bold" textAnchor="middle">PARLE-G</text>
            <text x="200" y="100" fill="#fef08a" fontFamily="sans-serif" fontSize="12" fontWeight="bold" textAnchor="middle">GLUCO BISCUITS</text>

            {/* Biscuit Illustration */}
            <circle cx="200" cy="220" r="60" fill="#b45309" stroke="#78350f" strokeWidth="4" />
            <circle cx="200" cy="220" r="50" fill="#d97706" stroke="#b45309" strokeWidth="2" strokeDasharray="6,4" />
            <text x="200" y="225" fill="#fef9c3" fontFamily="sans-serif" fontSize="14" fontWeight="bold" textAnchor="middle">PARLE</text>

            {/* Packaging date stamp */}
            <rect x="170" y="255" width="90" height="25" rx="3" fill="#ffffff" stroke="#000000" strokeWidth="1" />
            <text x="215" y="271" fill="#000000" fontFamily="monospace" fontSize="11" fontWeight="bold" textAnchor="middle">MFD 06/2026</text>

            {/* Net Quantity */}
            <rect x="40" y="300" width="140" height="50" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="50" y="320" fill="#64748b" fontFamily="sans-serif" fontSize="10">NET QUANTITY:</text>
            <text x="50" y="340" fill="#0f172a" fontFamily="sans-serif" fontSize="18" fontWeight="bold">800 g</text>

            {/* MRP */}
            <rect x="200" y="300" width="160" height="50" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="210" y="318" fill="#64748b" fontFamily="sans-serif" fontSize="10">MAX. RETAIL PRICE:</text>
            <text x="210" y="338" fill="#0f172a" fontFamily="sans-serif" fontSize="13" fontWeight="bold">₹50.00 (incl. of all taxes)</text>

            {/* Manufacturer Details */}
            <rect x="32" y="365" width="336" height="55" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="42" y="380" fill="#64748b" fontFamily="sans-serif" fontSize="9">MANUFACTURED BY:</text>
            <text x="42" y="395" fill="#0f172a" fontFamily="sans-serif" fontSize="10" fontWeight="bold">Parle Products Pvt. Ltd.</text>
            <text x="42" y="410" fill="#334155" fontFamily="sans-serif" fontSize="9">Vile Parle East, Mumbai, Maharashtra - 400057</text>

            {/* Consumer Care */}
            <rect x="32" y="430" width="336" height="55" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="42" y="443" fill="#64748b" fontFamily="sans-serif" fontSize="9">FOR FEEDBACK / COMPLAINTS CONTACT:</text>
            <text x="42" y="456" fill="#0f172a" fontFamily="sans-serif" fontSize="9" fontWeight="bold">Consumer Care Executive, Mumbai Office</text>
            <text x="42" y="474" fill="#1e3a8a" fontFamily="sans-serif" fontSize="9">Ph: 1800-22-7753 | email: customercare@parle.biz</text>
          </svg>
        );

      case "LM-2026-00122": // Surf Excel
        return (
          <svg viewBox="0 0 400 500" className="w-full h-full select-none" xmlns="http://www.w3.org/2000/svg">
            {/* Background wrapper */}
            <rect width="400" height="500" rx="8" fill="#1e40af" stroke="#1d4ed8" strokeWidth="6" />

            {/* Saffron & Green Side Trim */}
            <rect x="388" y="0" width="12" height="500" fill="#059669" />
            <rect x="0" y="488" width="400" height="12" fill="#f58220" />

            {/* Big burst graphics */}
            <path d="M 200 130 L 240 70 L 280 120 L 340 80 L 310 150 L 370 180 L 300 210 L 320 280 L 250 230 L 230 300 L 190 220 L 130 260 L 160 190 L 100 160 L 160 130 Z" fill="#f58220" opacity="0.9" />
            <path d="M 200 130 L 225 85 L 255 120 L 300 90 L 280 140 L 330 165 L 275 185 L 290 240 L 235 200 L 220 255 L 190 195 L 145 225 L 170 170 L 120 145 L 170 125 Z" fill="#facc15" />

            {/* Product Name */}
            <text x="200" y="80" fill="#ffffff" fontFamily="sans-serif" fontSize="38" fontWeight="black" textAnchor="middle" filter="drop-shadow(2px 4px 4px rgba(0,0,0,0.5))">Surf Excel</text>
            <text x="200" y="105" fill="#4ade80" fontFamily="sans-serif" fontSize="16" fontWeight="bold" textAnchor="middle" letterSpacing="2">EASY WASH</text>

            {/* Detergent flow graphic */}
            <ellipse cx="200" cy="210" rx="55" ry="12" fill="#ffffff" opacity="0.3" />
            <text x="200" y="214" fill="#ffffff" fontFamily="sans-serif" fontSize="11" fontWeight="bold" textAnchor="middle">TOUGH STAIN REMOVAL</text>

            {/* Date of Packaging */}
            <rect x="40" y="150" width="130" height="38" rx="4" fill="#ffffff" stroke="#1d4ed8" strokeWidth="2" />
            <text x="50" y="164" fill="#64748b" fontFamily="sans-serif" fontSize="8">PACKAGING DATE:</text>
            <text x="50" y="180" fill="#0f172a" fontFamily="sans-serif" fontSize="12" fontWeight="bold">MFD 05/2026</text>

            {/* Net Quantity */}
            <rect x="40" y="400" width="140" height="50" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="50" y="418" fill="#64748b" fontFamily="sans-serif" fontSize="9">NET QTY:</text>
            <text x="50" y="440" fill="#0f172a" fontFamily="sans-serif" fontSize="18" fontWeight="bold">1 kg</text>

            {/* MRP (Non-compliant: missing 'inclusive of all taxes') */}
            <rect x="200" y="400" width="160" height="50" rx="4" fill="#ffffff" stroke="#ef4444" strokeWidth="2" />
            <text x="210" y="418" fill="#ef4444" fontFamily="sans-serif" fontSize="8" fontWeight="bold">MRP (VIOLATION):</text>
            <text x="210" y="440" fill="#0f172a" fontFamily="sans-serif" fontSize="16" fontWeight="bold">₹ 140.00</text>

            {/* Manufacturer Details */}
            <rect x="32" y="310" width="336" height="60" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="42" y="325" fill="#64748b" fontFamily="sans-serif" fontSize="9">MANUFACTURED BY:</text>
            <text x="42" y="340" fill="#0f172a" fontFamily="sans-serif" fontSize="10" fontWeight="bold">Hindustan Unilever Limited (HUL)</text>
            <text x="42" y="356" fill="#334155" fontFamily="sans-serif" fontSize="9">Unilever House, Chakala, Andheri (E), Mumbai - 400099</text>

            {/* Consumer Care Section - Violation (Left Blank / Missing) */}
            <rect x="32" y="240" width="336" height="50" rx="4" fill="#fee2e2" stroke="#ef4444" strokeWidth="2" strokeDasharray="4,4" />
            <text x="200" y="270" fill="#dc2626" fontFamily="sans-serif" fontSize="11" fontWeight="bold" textAnchor="middle">MISSING MANDATORY CONSUMER CARE PANEL</text>
          </svg>
        );

      case "LM-2026-00123": // Haldiram's Bhujia
        return (
          <svg viewBox="0 0 400 500" className="w-full h-full select-none" xmlns="http://www.w3.org/2000/svg">
            {/* Background wrapper */}
            <rect width="400" height="500" rx="8" fill="#ea580c" stroke="#c2410c" strokeWidth="6" />

            {/* Gold border strip */}
            <rect x="15" y="15" width="370" height="470" fill="none" stroke="#fbbf24" strokeWidth="3" opacity="0.6" />

            {/* Brand Header */}
            <rect x="100" y="30" width="200" height="50" rx="6" fill="#ffffff" stroke="#b91c1c" strokeWidth="3" />
            <text x="200" y="65" fill="#b91c1c" fontFamily="serif" fontSize="26" fontWeight="bold" textAnchor="middle">Haldiram's</text>

            {/* Sub-logo */}
            <text x="200" y="110" fill="#fbbf24" fontFamily="sans-serif" fontSize="24" fontWeight="black" textAnchor="middle" letterSpacing="1">BHUJIA SEV</text>
            <text x="200" y="128" fill="#ffffff" fontFamily="sans-serif" fontSize="10" fontWeight="bold" textAnchor="middle">SPICY DEEP FRIED CHICKPEAS FLOUR STICKS</text>

            {/* Packaging date stamp (Poor Quality simulation - overlapping a graphic or seal) */}
            <g>
              <ellipse cx="280" cy="185" rx="45" ry="25" fill="#fcd34d" opacity="0.8" />
              {/* Blur simulation using opacity & shadow */}
              <text x="280" y="185" fill="#000000" opacity="0.3" fontFamily="monospace" fontSize="10" fontWeight="bold" textAnchor="middle">MFD 07/2026</text>
              <text x="281" y="186" fill="#000000" opacity="0.4" fontFamily="monospace" fontSize="10" fontWeight="bold" textAnchor="middle">MFD 07/2026</text>
              <text x="279" y="184" fill="#0b0f19" fontFamily="monospace" fontSize="10" fontWeight="bold" textAnchor="middle">MFD 07/2026</text>
              <text x="280" y="200" fill="#991b1b" fontFamily="sans-serif" fontSize="8" fontWeight="bold" textAnchor="middle">QUALITY SEAL</text>
            </g>

            {/* Bowl of Bhujia representation */}
            <path d="M 120 260 C 120 320 280 320 280 260 Z" fill="#b45309" stroke="#78350f" strokeWidth="4" />
            <ellipse cx="200" cy="260" rx="80" ry="15" fill="#fbbf24" />
            <circle cx="160" cy="258" r="4" fill="#d97706" />
            <circle cx="190" cy="262" r="5" fill="#b45309" />
            <circle cx="220" cy="257" r="4" fill="#d97706" />
            <circle cx="240" cy="261" r="5" fill="#b45309" />

            {/* Consumer Care */}
            <rect x="40" y="325" width="320" height="40" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="50" y="338" fill="#64748b" fontFamily="sans-serif" fontSize="8">CONSUMER CARE DETAILS:</text>
            <text x="50" y="352" fill="#0f172a" fontFamily="sans-serif" fontSize="8" fontWeight="bold">Haldiram Foods Nagpur. Ph: 0712-2681122 | email: support@haldirams.com</text>

            {/* Net Quantity */}
            <rect x="40" y="375" width="140" height="45" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="50" y="390" fill="#64748b" fontFamily="sans-serif" fontSize="9">NET QTY:</text>
            <text x="50" y="410" fill="#0f172a" fontFamily="sans-serif" fontSize="16" fontWeight="bold">400 g</text>

            {/* MRP */}
            <rect x="200" y="375" width="160" height="45" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="210" y="390" fill="#64748b" fontFamily="sans-serif" fontSize="9">MAX RETAIL PRICE:</text>
            <text x="210" y="410" fill="#0f172a" fontFamily="sans-serif" fontSize="12" fontWeight="bold">₹110.00 (incl. of all taxes)</text>

            {/* Manufacturer Details */}
            <rect x="32" y="430" width="336" height="45" rx="4" fill="#ffffff" stroke="#e2e8f0" strokeWidth="2" />
            <text x="42" y="443" fill="#64748b" fontFamily="sans-serif" fontSize="8">MANUFACTURER DETAILS:</text>
            <text x="42" y="456" fill="#0f172a" fontFamily="sans-serif" fontSize="9" fontWeight="bold">Haldiram Foods International Pvt. Ltd., Nagpur - 441104</text>
          </svg>
        );

      default:
        return (
          <div className="w-full h-full flex flex-col items-center justify-center bg-slate-200 border-2 border-slate-300 rounded text-slate-400">
            <span className="text-sm">No Image Available</span>
          </div>
        );
    }
  };

  return (
    <div className="relative overflow-hidden w-full h-full flex items-center justify-center bg-slate-900 rounded-lg shadow-inner" style={{ minHeight: '380px' }}>
      <div
        className="transition-transform duration-200 ease-out"
        style={{
          transform: `scale(${zoom}) rotate(${rotation}deg) translate(${panX}px, ${panY}px)`,
          width: '320px',
          height: '400px'
        }}
      >
        {renderSVGContent()}

        {/* Bounding Boxes overlay */}
        {Object.entries(activeBoxes).map(([key, value]) => {
          const isHighlighted = highlightedBox === key;
          if (!showAllBoxes && !isHighlighted) return null;
          
          const [x, y, w, h] = value.rect;
          return (
            <div
              key={key}
              className={`absolute border-2 rounded ${value.color} ${isHighlighted ? 'ring-4 ring-offset-1 ring-blue-500 scale-105 z-10' : 'z-0'} transition-all`}
              style={{
                left: `${x}%`,
                top: `${y}%`,
                width: `${w}%`,
                height: `${h}%`,
              }}
            >
              <div className={`absolute top-0 left-0 -translate-y-full px-1.5 py-0.5 rounded-t text-[8px] font-bold uppercase tracking-wider bg-slate-900 text-white`}>
                {value.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
export default ProductImageSVG;
