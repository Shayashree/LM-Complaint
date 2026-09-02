import type { Inspection, Rule, Violation, User, AuditLog } from '../types';

export const mockRules: Rule[] = [
  {
    id: "LM-RULE-001",
    title: "Rule 6(1)(a) - Name of Commodity",
    description: "Every package shall bear the common or generic name of the commodity contained in the package.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "OCR matches standard commodity dictionaries. Must not be generic without descriptors if specialized.",
    effectiveDate: "2011-04-01",
    version: "2011-V1.2",
    status: "Active",
    category: "Mandatory"
  },
  {
    id: "LM-RULE-002",
    title: "Rule 6(1)(b) - Manufacturer/Packer Identity",
    description: "Name and complete address of the manufacturer, or packer, or importer (in case of imported packages) must be declared.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Must contain PIN code, street name, district/state, and country if imported. Must contain words like 'Mfg by', 'Packed by', or 'Mkt by'.",
    effectiveDate: "2011-04-01",
    version: "2011-V1.2",
    status: "Active",
    category: "Manufacturer"
  },
  {
    id: "LM-RULE-003",
    title: "Rule 6(1)(c) - Net Quantity",
    description: "The net quantity, in terms of standard unit of weight, measure or number, contained in the package shall be declared.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Units must match metric standards (g, kg, ml, l, m, N, units). Font size must comply with Schedule II based on pack size.",
    effectiveDate: "2011-04-01",
    version: "2011-V1.2",
    status: "Active",
    category: "Net Quantity"
  },
  {
    id: "LM-RULE-004",
    title: "Rule 6(1)(d) - Packaging Date",
    description: "The month and year in which the commodity is manufactured or pre-packed or imported shall be clearly indicated.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Must be in MM/YYYY, Mon/YYYY, or DD/MM/YYYY format. Best before or expiry dates are optional but do not replace packaging date.",
    effectiveDate: "2011-04-01",
    version: "2011-V1.2",
    status: "Active",
    category: "Mandatory"
  },
  {
    id: "LM-RULE-005",
    title: "Rule 6(1)(e) - Maximum Retail Price (MRP)",
    description: "The retail sale price of the package, inclusive of all taxes, must be clearly declared as: 'MRP ₹xx.xx (incl. of all taxes)'.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Must include the text 'MRP' and 'inclusive of all taxes' or similar. Price must use ₹ symbol. Font height must meet minimum requirements.",
    effectiveDate: "2011-04-01",
    version: "2022-V2.0",
    status: "Active",
    category: "MRP"
  },
  {
    id: "LM-RULE-006",
    title: "Rule 6(1)(da) - Consumer Care Details",
    description: "Every package shall contain the name, address, telephone number, and email address of the person or office that can be contacted in case of complaints.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Must contain: 1. Phone number, 2. Email ID, 3. Address, 4. Designation (e.g. 'Consumer Care Manager').",
    effectiveDate: "2011-04-01",
    version: "2011-V1.2",
    status: "Active",
    category: "Consumer Care"
  },
  {
    id: "LM-RULE-007",
    title: "Rule 13 - Font Size and Legibility",
    description: "All mandatory declarations on packages must be legible, prominent, and of a minimum height under Rule 13 in relation to the area of the principal display panel.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Minimum font height: 1.0mm (net qty <= 50g/ml), 2.0mm (50g-200g), 4.0mm (200g-1kg), 6.0mm (> 1kg). Background contrast ratio >= 4.5:1.",
    effectiveDate: "2011-04-01",
    version: "2011-V1.2",
    status: "Active",
    category: "Packaging"
  },
  {
    id: "LM-RULE-008",
    title: "Rule 6(1)(f) - Country of Origin",
    description: "Every package must declare the country of origin if the commodity is manufactured or packed outside India.",
    applicability: "Imported Packages",
    validationParameters: "Must contain text like 'Country of Origin: [Country]' or 'Product of [Country]'. Country name must match ISO standard dictionary.",
    effectiveDate: "2011-04-01",
    version: "2011-V1.2",
    status: "Active",
    category: "Mandatory"
  },
  {
    id: "LM-RULE-009",
    title: "Rule 6(1)(g) - Unit Sale Price",
    description: "Declaration of the unit sale price is mandatory (e.g. price per g, ml, kg, or litre) on all pre-packaged retail commodities.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Must display price per base metric unit (e.g. ₹0.25 per gram, ₹140.00 per kg). Font size must meet PDP visual contrast parameters.",
    effectiveDate: "2022-04-01",
    version: "2022-V2.0",
    status: "Active",
    category: "MRP"
  },
  {
    id: "LM-RULE-010",
    title: "Sec 18(1) - Legal Metrology Act, 2009",
    description: "No person shall manufacture, pack, import, sell, distribute, deliver, or possess for sale any pre-packaged commodity unless it conforms to prescribed declarations.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "Mandates general compliance layout and registration of packers/importers under Rule 27 of PC Rules.",
    effectiveDate: "2011-03-01",
    version: "Act-2009",
    status: "Active",
    category: "Mandatory"
  },
  {
    id: "LM-RULE-011",
    title: "Sec 36(1) - Legal Metrology Act, 2009",
    description: "Establishes a statutory penalty for selling, distributing, delivering, or transferring any pre-packaged commodity that does not conform to declarations.",
    applicability: "All Pre-packaged Commodities",
    validationParameters: "First offense penalty: Fine up to ₹25,000. Second offense: Fine up to ₹50,000. Subsequent: Fine up to ₹1 Lakh or imprisonment.",
    effectiveDate: "2011-03-01",
    version: "Act-2009",
    status: "Active",
    category: "Mandatory"
  }
];

export const mockInspections: Inspection[] = [
  {
    id: "LM-2026-00121",
    productName: "Parle-G Gluco Biscuits",
    brand: "Parle",
    category: "Food Products",
    manufacturer: "Parle Products Pvt. Ltd.",
    manufacturerAddress: "Vile Parle East, Mumbai, Maharashtra - 400057",
    inspector: "Rajesh Kumar",
    date: "2026-08-26",
    status: "Compliant",
    violationsCount: 0,
    netQuantity: "800 g",
    mrp: "₹50.00 (inclusive of all taxes)",
    consumerCareDetails: "Consumer Care Executive, Parle Products Pvt. Ltd., Mumbai. Ph: 1800-22-7753, Email: customercare@parle.biz",
    dateOfPackaging: "06/2026",
    imageQuality: "Excellent",
    ocrConfidence: 98,
    detectionConfidence: 97,
    overallConfidence: 97.5,
    declarations: [
      { declaration: "Product Name", detectedValue: "Parle-G Gluco Biscuits", required: true, status: "PASS", confidence: 99, ruleReference: "Rule 6(1)(a)", boundingBox: [10, 45, 80, 10] },
      { declaration: "Net Quantity", detectedValue: "800 g", required: true, status: "PASS", confidence: 98, ruleReference: "Rule 6(1)(c)", boundingBox: [15, 65, 30, 8] },
      { declaration: "MRP", detectedValue: "MRP ₹50.00 (incl. of all taxes)", required: true, status: "PASS", confidence: 97, ruleReference: "Rule 6(1)(e)", boundingBox: [55, 65, 40, 8] },
      { declaration: "Manufacturer Name/Address", detectedValue: "Parle Products Pvt. Ltd., Vile Parle East, Mumbai, MH - 400057", required: true, status: "PASS", confidence: 96, ruleReference: "Rule 6(1)(b)", boundingBox: [10, 78, 80, 8] },
      { declaration: "Consumer Care Phone/Email", detectedValue: "Ph: 1800-22-7753, Email: customercare@parle.biz", required: true, status: "PASS", confidence: 98, ruleReference: "Rule 6(1)(da)", boundingBox: [10, 88, 80, 8] },
      { declaration: "Date of Packaging", detectedValue: "MFD 06/2026", required: true, status: "PASS", confidence: 99, ruleReference: "Rule 6(1)(d)", boundingBox: [45, 58, 20, 5] }
    ],
    officerRemarks: "All mandatory declarations verified on packaging. Font size is compliant with Rule 13 requirements for net weight package size.",
    verificationStatus: "Verified",
    verifiedBy: "Rajesh Kumar",
    verifiedDate: "2026-08-26"
  },
  {
    id: "LM-2026-00122",
    productName: "Product Scan",
    brand: "General Commodity",
    category: "Household Chemicals",
    manufacturer: "Packaged Commodities India Ltd.",
    manufacturerAddress: "Industrial Area, Phase II, New Delhi - 110020",
    inspector: "Rajesh Kumar",
    date: "2026-08-25",
    status: "Non-Compliant",
    violationsCount: 2,
    netQuantity: "1 kg",
    mrp: "₹140.00",
    consumerCareDetails: "Not Detected",
    dateOfPackaging: "05/2026",
    imageQuality: "Good",
    ocrConfidence: 94,
    detectionConfidence: 92,
    overallConfidence: 93,
    declarations: [
      { declaration: "Product Name", detectedValue: "Product Scan", required: true, status: "PASS", confidence: 98, ruleReference: "Rule 6(1)(a)", boundingBox: [10, 15, 80, 12] },
      { declaration: "Net Quantity", detectedValue: "Net Qty: 1 kg", required: true, status: "PASS", confidence: 97, ruleReference: "Rule 6(1)(c)", boundingBox: [15, 82, 30, 6] },
      { declaration: "MRP", detectedValue: "MRP ₹140.00", required: true, status: "WARNING", confidence: 95, ruleReference: "Rule 6(1)(e)", boundingBox: [50, 82, 40, 6] }, // missing (incl. of all taxes)
      { declaration: "Manufacturer Name/Address", detectedValue: "Hindustan Unilever Limited, Mumbai - 400099", required: true, status: "PASS", confidence: 96, ruleReference: "Rule 6(1)(b)", boundingBox: [10, 65, 80, 8] },
      { declaration: "Consumer Care Phone/Email", detectedValue: "Not Detected on Package", required: true, status: "FAIL", confidence: 91, ruleReference: "Rule 6(1)(da)", boundingBox: [10, 75, 80, 6] }, // Violation 1
      { declaration: "Date of Packaging", detectedValue: "05/2026", required: true, status: "PASS", confidence: 93, ruleReference: "Rule 6(1)(d)", boundingBox: [15, 55, 30, 5] }
    ],
    officerRemarks: "The package lacks consumer care contact information (Rule 6(1)(da)). The MRP block is also missing the mandatory phrase 'inclusive of all taxes' or 'incl. of all taxes'.",
    verificationStatus: "Verified",
    verifiedBy: "Rajesh Kumar",
    verifiedDate: "2026-08-25"
  },
  {
    id: "LM-2026-00123",
    productName: "Haldiram's Bhujia Sev",
    brand: "Haldiram",
    category: "Food Products",
    manufacturer: "Haldiram Foods International Pvt. Ltd.",
    manufacturerAddress: "20 Km Stone, Bhandara Road, Nagpur, Maharashtra - 441104",
    inspector: "Priya Sharma",
    date: "2026-08-26",
    status: "Manual Review",
    violationsCount: 1,
    netQuantity: "400 g",
    mrp: "₹110.00 (inclusive of all taxes)",
    consumerCareDetails: "Quality Manager, Haldiram Foods, Nagpur. Tel: 0712-2681122, email: support@haldirams.com",
    dateOfPackaging: "07/2026",
    imageQuality: "Poor",
    ocrConfidence: 85,
    detectionConfidence: 89,
    overallConfidence: 87,
    declarations: [
      { declaration: "Product Name", detectedValue: "Bhujia Sev", required: true, status: "PASS", confidence: 95, ruleReference: "Rule 6(1)(a)", boundingBox: [20, 20, 60, 10] },
      { declaration: "Net Quantity", detectedValue: "400 g", required: true, status: "PASS", confidence: 91, ruleReference: "Rule 6(1)(c)", boundingBox: [15, 78, 25, 5] },
      { declaration: "MRP", detectedValue: "MRP ₹110.00 (incl. of all taxes)", required: true, status: "PASS", confidence: 89, ruleReference: "Rule 6(1)(e)", boundingBox: [45, 78, 45, 5] },
      { declaration: "Manufacturer Name/Address", detectedValue: "Haldiram Foods International Pvt. Ltd., Nagpur - 441104", required: true, status: "PASS", confidence: 82, ruleReference: "Rule 6(1)(b)", boundingBox: [10, 85, 80, 5] },
      { declaration: "Consumer Care Phone/Email", detectedValue: "support@haldirams.com", required: true, status: "PASS", confidence: 87, ruleReference: "Rule 6(1)(da)", boundingBox: [10, 92, 80, 5] },
      { declaration: "Date of Packaging", detectedValue: "MFD 07/2026 (Low OCR confidence)", required: true, status: "WARNING", confidence: 68, ruleReference: "Rule 6(1)(d)", boundingBox: [45, 60, 20, 4] } // low confidence, warning
    ],
    officerRemarks: "The packaging date text is highly blurred. AI flagged OCR confidence below threshold (68%). Inspector needs to visually confirm date and check if physical print conforms to Rule 13 legibility standards.",
    verificationStatus: "Pending",
    verifiedBy: "",
    verifiedDate: ""
  },
  {
    id: "LM-2026-00124",
    productName: "Aashirvaad Shudh Chakki Atta",
    brand: "ITC",
    category: "Food Products",
    manufacturer: "ITC Limited",
    manufacturerAddress: "37, J.L. Nehru Road, Kolkata, West Bengal - 700071",
    inspector: "Priya Sharma",
    date: "2026-08-26",
    status: "Manual Review",
    violationsCount: 1,
    netQuantity: "5 kg",
    mrp: "₹260.00 (inclusive of all taxes)",
    consumerCareDetails: "ITC Care Manager, P.O. Box 540, Kolkata. Tel: 1800-425-4444, email: itccares@itc.in",
    dateOfPackaging: "06/2026",
    imageQuality: "Good",
    ocrConfidence: 96,
    detectionConfidence: 94,
    overallConfidence: 95,
    declarations: [
      { declaration: "Product Name", detectedValue: "Aashirvaad Shudh Chakki Atta", required: true, status: "PASS", confidence: 99, ruleReference: "Rule 6(1)(a)", boundingBox: [15, 10, 70, 15] },
      { declaration: "Net Quantity", detectedValue: "5 kg", required: true, status: "PASS", confidence: 97, ruleReference: "Rule 6(1)(c)", boundingBox: [10, 85, 30, 8] },
      { declaration: "MRP", detectedValue: "₹260.00", required: true, status: "WARNING", confidence: 95, ruleReference: "Rule 6(1)(e)", boundingBox: [60, 85, 30, 8] },
      { declaration: "Manufacturer Name/Address", detectedValue: "ITC Limited, 37, J.L. Nehru Road, Kolkata - 700071", required: true, status: "PASS", confidence: 93, ruleReference: "Rule 6(1)(b)", boundingBox: [10, 68, 80, 8] },
      { declaration: "Consumer Care Phone/Email", detectedValue: "itccares@itc.in, Tel: 1800-425-4444", required: true, status: "PASS", confidence: 96, ruleReference: "Rule 6(1)(da)", boundingBox: [10, 78, 80, 6] },
      { declaration: "Date of Packaging", detectedValue: "Not clearly detected", required: true, status: "FAIL", confidence: 91, ruleReference: "Rule 6(1)(d)", boundingBox: [15, 60, 30, 5] }
    ],
    officerRemarks: "Date of packaging is hidden in the bottom seam crimp, causing detection failure. Inspector must manually examine the crimp seal to verify whether date stamp exists and is legible.",
    verificationStatus: "Pending",
    verifiedBy: "",
    verifiedDate: ""
  },
  {
    id: "LM-2026-00125",
    productName: "Amul Pasteurised Butter",
    brand: "Amul",
    category: "Dairy Products",
    manufacturer: "Gujarat Cooperative Milk Marketing Federation (GCMMF)",
    manufacturerAddress: "Amul Dairy Road, Anand, Gujarat - 388001",
    inspector: "Rajesh Kumar",
    date: "2026-08-24",
    status: "Non-Compliant",
    violationsCount: 2,
    netQuantity: "500 g",
    mrp: "₹275.00 (incl. of all taxes)",
    consumerCareDetails: "Amul Customer Care, GCMMF Ltd., Anand. Toll Free: 1800-258-3333, Email: customercare@amul.coop",
    dateOfPackaging: "07/2026",
    imageQuality: "Good",
    ocrConfidence: 95,
    detectionConfidence: 94,
    overallConfidence: 94.5,
    declarations: [
      { declaration: "Product Name", detectedValue: "Amul Pasteurised Butter", required: true, status: "PASS", confidence: 98, ruleReference: "Rule 6(1)(a)", boundingBox: [20, 20, 60, 10] },
      { declaration: "Net Quantity", detectedValue: "500g", required: true, status: "PASS", confidence: 96, ruleReference: "Rule 6(1)(c)", boundingBox: [15, 75, 20, 6] },
      { declaration: "MRP", detectedValue: "MRP ₹275 (Incl of all taxes)", required: true, status: "PASS", confidence: 97, ruleReference: "Rule 6(1)(e)", boundingBox: [45, 75, 45, 6] },
      { declaration: "Manufacturer Name/Address", detectedValue: "GCMMF Anand 388001", required: true, status: "PASS", confidence: 94, ruleReference: "Rule 6(1)(b)", boundingBox: [10, 83, 80, 5] },
      { declaration: "Consumer Care Phone/Email", detectedValue: "customercare@amul.coop", required: true, status: "PASS", confidence: 95, ruleReference: "Rule 6(1)(da)", boundingBox: [10, 90, 80, 5] },
      { declaration: "Date of Packaging", detectedValue: "Not detected", required: true, status: "FAIL", confidence: 90, ruleReference: "Rule 6(1)(d)", boundingBox: [40, 55, 20, 5] }
    ],
    officerRemarks: "Date of packing completely absent from outer carton shell, representing a major violation of Rule 6(1)(d). Legal notice issued to manufacturer.",
    verificationStatus: "Verified",
    verifiedBy: "Rajesh Kumar",
    verifiedDate: "2026-08-24"
  }
];

export const mockViolations: Violation[] = [
  {
    id: "VIO-2026-0001",
    productName: "Product Scan",
    brand: "General Commodity",
    violationType: "Missing Consumer Care Details",
    severity: "High",
    detectedDate: "2026-08-25",
    status: "Open",
    assignedOfficer: "Rajesh Kumar"
  },
  {
    id: "VIO-2026-0002",
    productName: "Amul Pasteurised Butter",
    brand: "Amul",
    violationType: "Missing Date of Packaging",
    severity: "High",
    detectedDate: "2026-08-24",
    status: "Open",
    assignedOfficer: "Rajesh Kumar"
  },
  {
    id: "VIO-2026-0003",
    productName: "Haldiram's Bhujia Sev",
    brand: "Haldiram",
    violationType: "Readability / Font size",
    severity: "Medium",
    detectedDate: "2026-08-26",
    status: "Under Review",
    assignedOfficer: "Priya Sharma"
  },
  {
    id: "VIO-2026-0004",
    productName: "Aashirvaad Shudh Chakki Atta",
    brand: "ITC",
    violationType: "Missing Packaging Date",
    severity: "High",
    detectedDate: "2026-08-26",
    status: "Under Review",
    assignedOfficer: "Priya Sharma"
  }
];

export const mockUsers: User[] = [
  {
    name: "Rajesh Kumar",
    employeeId: "LMI-88902",
    department: "Enforcement - Delhi Zone I",
    role: "Legal Metrology Inspector",
    status: "Active",
    lastLogin: "2026-08-26 10:15"
  },
  {
    name: "Priya Sharma",
    employeeId: "LMI-88915",
    department: "Enforcement - Delhi Zone I",
    role: "Legal Metrology Inspector",
    status: "Active",
    lastLogin: "2026-08-26 11:22"
  },
  {
    name: "A. K. Shastri",
    employeeId: "LMS-77102",
    department: "Directorate of Legal Metrology",
    role: "Senior Officer / Supervisor",
    status: "Active",
    lastLogin: "2026-08-26 09:30"
  },
  {
    name: "Manoj Dwivedi",
    employeeId: "LMA-44390",
    department: "Rules & Policy Section",
    role: "Rule Administrator",
    status: "Active",
    lastLogin: "2026-08-25 15:40"
  },
  {
    name: "Neha Goel",
    employeeId: "LMD-12903",
    department: "Data Operations",
    role: "Data Analyst",
    status: "Active",
    lastLogin: "2026-08-26 13:05"
  },
  {
    name: "Sanjay Swamy",
    employeeId: "LMA-99021",
    department: "Internal Audit Division",
    role: "Auditor",
    status: "Active",
    lastLogin: "2026-08-24 11:55"
  }
];

export const mockAuditLogs: AuditLog[] = [
  {
    timestamp: "2026-08-26 17:34:02",
    user: "Rajesh Kumar (LMI-88902)",
    action: "Completed Compliance Screening",
    recordId: "LM-2026-00121",
    ipAddress: "10.240.45.18",
    status: "Success"
  },
  {
    timestamp: "2026-08-26 17:30:15",
    user: "Rajesh Kumar (LMI-88902)",
    action: "Uploaded Product Packaging Images",
    recordId: "LM-2026-00121",
    ipAddress: "10.240.45.18",
    status: "Success"
  },
  {
    timestamp: "2026-08-26 16:15:44",
    user: "Priya Sharma (LMI-88915)",
    action: "Submitted Officer Verification Form",
    recordId: "LM-2026-00124",
    ipAddress: "10.240.45.22",
    status: "Success"
  },
  {
    timestamp: "2026-08-26 15:10:30",
    user: "A. K. Shastri (LMS-77102)",
    action: "Approved Rule Amendment",
    recordId: "LM-RULE-005",
    ipAddress: "10.240.12.5",
    status: "Success"
  },
  {
    timestamp: "2026-08-26 11:42:19",
    user: "Manoj Dwivedi (LMA-44390)",
    action: "Created Draft Rule Version",
    recordId: "LM-RULE-005",
    ipAddress: "10.240.18.99",
    status: "Success"
  },
  {
    timestamp: "2026-08-26 09:31:00",
    user: "System AI Engine",
    action: "Auto-Analysis Hook Completed",
    recordId: "LM-2026-00123",
    ipAddress: "localhost",
    status: "Success"
  }
];
