import Tesseract from 'tesseract.js';

export interface PackagingSideItem {
  side: 'Front Panel' | 'Back Panel (PDP)' | 'Left Side' | 'Right Side / Top';
  sideCode: 'front' | 'back' | 'side_left' | 'side_right';
  name: string;
  file?: File;
  previewUrl?: string;
  size?: string;
}

export interface ExtractedPanelResult {
  sideCode: string;
  sideName: string;
  rawText: string;
  words: { text: string; bbox: [number, number, number, number]; confidence: number }[];
}

export async function runRealMultiSideOcr(
  panels: PackagingSideItem[],
  onProgress?: (msg: string, pct: number) => void
): Promise<{
  allText: string;
  panelResults: ExtractedPanelResult[];
  extractedDeclarations: Record<string, any>;
}> {
  const panelResults: ExtractedPanelResult[] = [];
  let combinedText = '';
  const filenames = panels.map(p => p.name || '').filter(Boolean);

  for (let i = 0; i < panels.length; i++) {
    const p = panels[i];
    if (!p.file && !p.previewUrl) continue;

    if (onProgress) {
      onProgress(`Reading text on ${p.side} (${i + 1}/${panels.length})...`, Math.round(((i) / panels.length) * 60) + 10);
    }

    try {
      const source = p.file || p.previewUrl!;
      const result = await Tesseract.recognize(source, 'eng', {
        logger: (m: any) => {
          if (m && m.status === 'recognizing text') {
            const currentPct = Math.round(((i + (m.progress || 0)) / panels.length) * 60) + 10;
            if (onProgress) {
              onProgress(`Extracting optical glyphs on ${p.side}: ${Math.round((m.progress || 0) * 100)}%`, currentPct);
            }
          }
        }
      });

      const raw = result?.data?.text || '';
      combinedText += `\n--- [${p.side}] ---\n` + raw;

      const words: { text: string; bbox: [number, number, number, number]; confidence: number }[] = [];
      const imgW = (result?.data as any)?.imageWidth || 800;
      const imgH = (result?.data as any)?.imageHeight || 600;

      const anyData = result?.data as any;
      if (anyData?.words) {
        for (const w of anyData.words) {
          if (w.text && w.text.trim().length > 1 && w.bbox) {
            const xPct = Math.round((w.bbox.x0 / imgW) * 100);
            const yPct = Math.round((w.bbox.y0 / imgH) * 100);
            const wPct = Math.max(4, Math.round(((w.bbox.x1 - w.bbox.x0) / imgW) * 100));
            const hPct = Math.max(3, Math.round(((w.bbox.y1 - w.bbox.y0) / imgH) * 100));
            words.push({
              text: w.text.trim(),
              bbox: [xPct, yPct, wPct, hPct],
              confidence: Math.round(w.confidence || 85)
            });
          }
        }
      }

      panelResults.push({
        sideCode: p.sideCode,
        sideName: p.side,
        rawText: raw,
        words
      });
    } catch (err) {
      console.warn(`Tesseract OCR failed for ${p.side}:`, err);
    }
  }

  if (onProgress) {
    onProgress('Parsing statutory Legal Metrology declarations...', 80);
  }

  const extracted = parseLmpcDeclarationsFromText(combinedText, filenames);

  return {
    allText: combinedText,
    panelResults,
    extractedDeclarations: extracted
  };
}

export function parseLmpcDeclarationsFromText(text: string, filenames: string[] = []): Record<string, any> {
  const clean = text.replace(/\r/g, ' ');
  const lines = clean.split('\n').map(l => l.trim()).filter(Boolean);

  // 1. Robust Multi-Line MRP Parsing
  let mrp = 'N/A';
  // Check A: "MRP", "M.R.P.", "MAX RETAIL PRICE" with optional newline/words and price
  const mrpDeepMatch = clean.match(/(?:M\.?\s*R\.?\s*P\.?|MAX(?:IMUM)?\s*RETAIL\s*PRICE|RETAIL\s*PRICE|MAX\s*PRICE)[\s\S]{0,35}?(?:Rs\.?|INR|₹)?\s*([0-9]{1,5}(?:\.[0-9]{1,2})?)/i);
  if (mrpDeepMatch && parseFloat(mrpDeepMatch[1]) > 0) {
    const val = mrpDeepMatch[1];
    const hasTaxes = /incl(?:usive)?\s*(?:of)?\s*(?:all)?\s*taxes/i.test(clean);
    mrp = `₹ ${val} ${hasTaxes ? '(incl. of all taxes)' : '(incl. of all taxes)'}`;
  } else {
    // Check B: Currency symbol directly before number (e.g. ₹45 or Rs. 120)
    const currMatch = clean.match(/(?:₹|Rs\.?|INR)\s*([0-9]{1,5}(?:\.[0-9]{1,2})?)/i);
    if (currMatch && parseFloat(currMatch[1]) > 0) {
      mrp = `₹ ${currMatch[1]} (incl. of all taxes)`;
    } else {
      // Check C: Price followed by /- (e.g. 50/- or 25/-)
      const slashMatch = clean.match(/\b([0-9]{1,4}(?:\.[0-9]{1,2})?)\s*\/\-/);
      if (slashMatch && parseFloat(slashMatch[1]) > 0) {
        mrp = `₹ ${slashMatch[1]} (incl. of all taxes)`;
      } else {
        // Check D: Any number followed by incl/taxes
        const taxMatch = clean.match(/([0-9]{1,4}(?:\.[0-9]{1,2})?)\s*(?:\(?[I|i]ncl|\(?[T|t]axes)/);
        if (taxMatch && parseFloat(taxMatch[1]) > 0) {
          mrp = `₹ ${taxMatch[1]} (incl. of all taxes)`;
        }
      }
    }
  }

  // 2. Robust Net Quantity Parsing
  let netQty = 'N/A';
  const qtyRegex = /(?:NET\s*(?:QTY|QUANTITY|WT\.?|WEIGHT|VOL(?:UME)?)?|CONTENTS?)\s*[:.\-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|gms|ml|l|ltr|litre|litres|n|units|pieces|pc|tablets|capsules|m|cm))\b/i;
  const qtyMatch = clean.match(qtyRegex);
  if (qtyMatch) {
    netQty = qtyMatch[1].trim();
  } else {
    const standaloneMatch = clean.match(/\b([0-9]+(?:\.[0-9]+)?\s*(?:kg|g|gm|ml|l|ltr))\b/i);
    if (standaloneMatch) {
      netQty = standaloneMatch[1].trim();
    }
  }

  // 3. Manufacturing / Packaging Date Parsing
  let mfgDate = 'N/A';
  const mfgRegex = /(?:MFD|MFG|PACKED|PKD|DATE\s*OF\s*(?:MFG|PACKING|PKD))\s*[:.\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{2,4}|[A-Za-z]{3,9}\s*[0-9]{2,4}|[0-9]{2,4}[\/\.\-][0-9]{1,2})/i;
  const mfgMatch = clean.match(mfgRegex);
  if (mfgMatch) {
    mfgDate = mfgMatch[1].trim();
  } else {
    const monthYear = clean.match(/\b(0[1-9]|1[0-2])[\/\.\-](202[0-9]|2[0-9])\b/);
    if (monthYear) {
      mfgDate = monthYear[0];
    }
  }

  // 4. Best Before / Expiry Date Parsing
  let bestBefore = 'N/A';
  const expRegex = /(?:BEST\s*BEFORE|EXP(?:IRY)?(?:\s*DATE)?|USE\s*BY)\s*[:.\-]?\s*([^\\n\r,;]{3,35})/i;
  const expMatch = clean.match(expRegex);
  if (expMatch) {
    bestBefore = expMatch[1].trim();
  }

  // 5. Consumer Care Helpline & Email Parsing
  let consumerCare = 'N/A';
  const phoneMatch = clean.match(/(?:1800[-\s]?[0-9]{2,4}[-\s]?[0-9]{3,4}|\+?91[-\s]?[6-9][0-9]{9}|[0-9]{3,4}[-\s]?[0-9]{6,8})/);
  const emailMatch = clean.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  if (phoneMatch || emailMatch) {
    const parts = [];
    if (phoneMatch) parts.push(`Helpline: ${phoneMatch[0]}`);
    if (emailMatch) parts.push(`Email: ${emailMatch[0]}`);
    consumerCare = parts.join(' | ');
  }

  // 6. Manufacturer & Packer Address
  let manufacturer = 'N/A';
  const mfgAddrRegex = /(?:MFD|MANUFACTURED|PACKED|MARKETED)\s*BY\s*[:.\-]?\s*([^\\n\r]+(?:\n[^\\n\r]+)?)/i;
  const mfgAddrMatch = clean.match(mfgAddrRegex);
  if (mfgAddrMatch) {
    manufacturer = mfgAddrMatch[1].replace(/\s+/g, ' ').trim().slice(0, 120);
  } else {
    const compLine = lines.find(l => /(?:Pvt\.?\s*Ltd\.?|Limited|Industries|Enterprises|Corporation)/i.test(l));
    if (compLine) {
      manufacturer = compLine.slice(0, 100);
    }
  }

  // 7. Robust Country of Origin Parsing
  let countryOfOrigin = 'India';
  const originRegex = /(?:COUNTRY\s*OF\s*ORIGIN|ORIGIN|MADE\s*IN|PRODUCT\s*OF|MFD\s*IN|MANUFACTURED\s*IN|PRODUCED\s*IN)\s*[:.\-]?\s*([A-Za-z\s]{3,20})/i;
  const originMatch = clean.match(originRegex);
  if (originMatch) {
    const rawOrigin = originMatch[1].trim();
    const firstWord = rawOrigin.split(/\s+/)[0];
    if (firstWord && firstWord.length >= 3) {
      countryOfOrigin = firstWord.charAt(0).toUpperCase() + firstWord.slice(1).toLowerCase();
    }
  } else if (/\b(India|Bharat|Maharashtra|Gujarat|Tamil\s*Nadu|Karnataka|Delhi|Haryana|Punjab|Uttar\s*Pradesh|Kerala|Telangana|Andhra|Rajasthan|West\s*Bengal|Mumbai|Bengaluru|Chennai|Kolkata|Hyderabad|FSSAI)\b/i.test(clean)) {
    countryOfOrigin = 'India';
  } else {
    const foreignMatch = clean.match(/\b(China|Vietnam|USA|United\s*States|Germany|Japan|Thailand|UK|United\s*Kingdom|France|Italy|Korea|Bangladesh|Sri\s*Lanka|Nepal|Taiwan|Malaysia|Indonesia)\b/i);
    if (foreignMatch) {
      countryOfOrigin = foreignMatch[0];
    } else {
      countryOfOrigin = 'India';
    }
  }

  // 8. Robust Product Name & Brand Identification
  let productName = 'Packaged Commodity Item';
  let brand = 'Product';

  const knownBrands: Record<string, string> = {
    'parle': 'Parle-G',
    'parle-g': 'Parle-G',
    'surf excel': 'Surf Excel',
    'surf': 'Surf Excel',
    'tata salt': 'Tata Salt',
    'tata': 'Tata',
    'amul': 'Amul',
    'maggi': 'Maggi',
    'haldiram': "Haldiram's",
    'dettol': 'Dettol',
    'colgate': 'Colgate',
    'aashirvaad': 'Aashirvaad',
    'fortune': 'Fortune',
    'britannia': 'Britannia',
    'good day': 'Good Day',
    'lays': "Lay's",
    "lay's": "Lay's",
    'kurkure': 'Kurkure',
    'bingo': 'Bingo',
    'clinic plus': 'Clinic Plus',
    'head & shoulders': 'Head & Shoulders',
    'head and shoulders': 'Head & Shoulders',
    'dove': 'Dove',
    'lux': 'Lux',
    'lifebuoy': 'Lifebuoy',
    'parachute': 'Parachute',
    'lizol': 'Lizol',
    'harpic': 'Harpic',
    'vim': 'Vim',
    'comfort': 'Comfort',
    'bournvita': 'Bournvita',
    'horlicks': 'Horlicks',
    'cadbury': 'Cadbury',
    'dairy milk': 'Cadbury Dairy Milk',
    'oreo': 'Oreo',
    'nestle': 'Nestle',
    'kitkat': 'KitKat',
    'everest': 'Everest',
    'mdh': 'MDH',
    'catch': 'Catch',
    'dabur': 'Dabur',
    'patanjali': 'Patanjali',
    'himalaya': 'Himalaya',
    'saffola': 'Saffola',
    'kissan': 'Kissan'
  };

  const combinedSearchText = (clean + ' ' + filenames.join(' ')).toLowerCase();

  for (const [key, brandTitle] of Object.entries(knownBrands)) {
    if (combinedSearchText.includes(key)) {
      brand = brandTitle;
      const lineWithBrand = lines.find(l => l.toLowerCase().includes(key));
      if (lineWithBrand && lineWithBrand.length >= 4 && lineWithBrand.length <= 50) {
        productName = lineWithBrand;
      } else {
        productName = `${brandTitle} Packaged Product`;
      }
      break;
    }
  }

  if (brand === 'Product') {
    const candidateLines = lines.filter(l => {
      const lower = l.toLowerCase();
      if (l.length < 3 || l.length > 50) return false;
      if (/(?:mrp|net|wt|qty|batch|mfd|mfg|exp|pkd|addr|care|ph|email|ltd|pvt|rule|fssai|lic|nutri|ingred|contain|store|cool|dry|place|keep|away|regd|trade|mark|barcode)/i.test(lower)) return false;
      if (/^[0-9\s.,:\-_/]+$/.test(l)) return false;
      return true;
    });

    if (candidateLines.length > 0) {
      productName = candidateLines[0];
      const words = productName.split(/\s+/).filter(w => w.length > 1);
      brand = words[0] || 'Brand';
    } else if (filenames.length > 0 && filenames[0]) {
      const cleanFn = filenames[0].replace(/\.[^/.]+$/, "").replace(/[_-]+/g, " ");
      if (cleanFn.length >= 3) {
        productName = cleanFn.charAt(0).toUpperCase() + cleanFn.slice(1);
        brand = cleanFn.split(' ')[0] || 'Brand';
      }
    }
  }

  // 9. Unit Sale Price
  let unitSalePrice = 'N/A';
  const uspRegex = /(?:USP|UNIT\s*SALE\s*PRICE)\s*[:.\-]?\s*(?:(?:Rs\.?|₹)\s*)?([0-9]+(?:\.[0-9]+)?\s*(?:per|\/)\s*(?:g|kg|ml|l|unit|n))/i;
  const uspMatch = clean.match(uspRegex);
  if (uspMatch) {
    unitSalePrice = `₹ ${uspMatch[1]}`;
  } else if (mrp !== 'N/A' && netQty !== 'N/A') {
    const numPrice = parseFloat(mrp.replace(/[^0-9.]/g, ''));
    const numQty = parseFloat(netQty.replace(/[^0-9.]/g, ''));
    const unit = netQty.replace(/[0-9.\s]/g, '').toLowerCase();
    if (!isNaN(numPrice) && !isNaN(numQty) && numQty > 0) {
      if (unit.includes('kg') || (unit.includes('g') && numQty >= 1000)) {
        const kgVal = unit.includes('kg') ? numQty : numQty / 1000;
        unitSalePrice = `₹ ${(numPrice / kgVal).toFixed(2)} / kg`;
      } else if (unit.includes('g')) {
        unitSalePrice = `₹ ${(numPrice / numQty).toFixed(2)} / g`;
      } else if (unit.includes('l') || (unit.includes('ml') && numQty >= 1000)) {
        const lVal = unit.includes('l') && !unit.includes('ml') ? numQty : numQty / 1000;
        unitSalePrice = `₹ ${(numPrice / lVal).toFixed(2)} / L`;
      } else if (unit.includes('ml')) {
        unitSalePrice = `₹ ${(numPrice / numQty).toFixed(2)} / ml`;
      } else {
        unitSalePrice = `₹ ${(numPrice / numQty).toFixed(2)} / unit`;
      }
    }
  }

  // 10. Veg/Non-Veg Symbol
  let vegSymbol = 'N/A';
  if (/non[-\s]?veg/i.test(clean) || /brown\s*dot/i.test(clean)) {
    vegSymbol = 'BROWN_NONVEG';
  } else if (/100%\s*veg|vegetarian|green\s*dot/i.test(clean)) {
    vegSymbol = 'GREEN_VEG';
  }

  return {
    product_name: productName,
    brand,
    manufacturer_name_address: manufacturer,
    net_quantity: netQty,
    mfg_date: mfgDate,
    mrp,
    unit_sale_price: unitSalePrice,
    consumer_care: consumerCare,
    best_before_or_expiry: bestBefore,
    country_of_origin: countryOfOrigin,
    veg_nonveg_symbol: vegSymbol
  };
}
