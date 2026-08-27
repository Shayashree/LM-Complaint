export type ComplianceStatus = 'Compliant' | 'Non-Compliant' | 'Manual Review';
export type SeverityLevel = 'High' | 'Medium' | 'Low';
export type VerificationAction = 'Confirm Violation' | 'Mark Compliant' | 'Send for Manual Review';

export interface DeclarationCheck {
  declaration: string;
  detectedValue: string;
  required: boolean;
  status: 'PASS' | 'FAIL' | 'WARNING';
  confidence: number;
  ruleReference: string;
  boundingBox?: [number, number, number, number]; // [x, y, w, h] in percentages
}

export interface Inspection {
  id: string;
  productName: string;
  brand: string;
  category: string;
  manufacturer: string;
  manufacturerAddress: string;
  inspector: string;
  date: string;
  status: ComplianceStatus;
  violationsCount: number;
  netQuantity: string;
  mrp: string;
  consumerCareDetails: string;
  dateOfPackaging: string;
  imageQuality: 'Excellent' | 'Good' | 'Poor';
  ocrConfidence: number;
  detectionConfidence: number;
  overallConfidence: number;
  declarations: DeclarationCheck[];
  officerRemarks?: string;
  verificationStatus?: 'Pending' | 'Verified' | 'Escalated';
  verifiedBy?: string;
  verifiedDate?: string;
  imageEvidenceUrl?: string; // We will use SVG drawings or styled canvas placeholders
}

export interface Rule {
  id: string;
  title: string;
  description: string;
  applicability: string;
  validationParameters: string;
  effectiveDate: string;
  version: string;
  status: 'Active' | 'Inactive';
  category: 'Mandatory' | 'MRP' | 'Net Quantity' | 'Manufacturer' | 'Consumer Care' | 'Packaging';
}

export interface Violation {
  id: string;
  productName: string;
  brand: string;
  violationType: string;
  severity: SeverityLevel;
  detectedDate: string;
  status: 'Open' | 'Under Review' | 'Resolved';
  assignedOfficer: string;
}

export interface User {
  name: string;
  employeeId: string;
  department: string;
  role: string;
  status: 'Active' | 'Inactive';
  lastLogin: string;
}

export interface AuditLog {
  timestamp: string;
  user: string;
  action: string;
  recordId: string;
  ipAddress: string;
  status: 'Success' | 'Failed';
}
