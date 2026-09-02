import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.models import Inspection, Report, AuditLog

class ReportService:
    def generate_compliance_report(self, db, inspection_id: str, officer_id: int) -> str:
        """
        Generates an official PDF report using ReportLab.
        Returns the output path of the generated PDF.
        """
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found.")

        # Determine output folder and path
        os.makedirs("reports", exist_ok=True)
        pdf_filename = f"Report_{inspection_id}_{int(datetime.utcnow().timestamp())}.pdf"
        pdf_path = os.path.join("reports", pdf_filename).replace("\\", "/")

        # Document setup
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                                rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#0b2240"),
            alignment=1, # Centered
            spaceAfter=10
        )
        sub_style = ParagraphStyle(
            name="SubStyle",
            parent=styles["Normal"],
            fontSize=9,
            alignment=1,
            spaceAfter=20
        )
        h2_style = ParagraphStyle(
            name="H2Style",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#0b2240"),
            spaceBefore=12,
            spaceAfter=6
        )
        normal_style = styles["Normal"]
        disclaimer_style = ParagraphStyle(
            name="DisclaimerStyle",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#7f8c8d"),
            spaceBefore=15,
            alignment=1
        )

        # Header
        story.append(Paragraph("LM-ComplianceAuditor System", title_style))
        story.append(Paragraph("System-Generated Compliance Report — Prototype for SIH 2026", title_style))
        story.append(Paragraph("Automated Legal Metrology Packaging Inspection Report", sub_style))
        story.append(Paragraph(f"Inspection ID: {inspection_id} | Date: {inspection.date}", sub_style))
        story.append(Spacer(1, 10))

        # Section 1: Metadata
        story.append(Paragraph("1. PACKAGED COMMODITY METADATA & RULE 6 DECLARATIONS", h2_style))
        prod = inspection.product

        def get_decl(name, default="N/A"):
            d = next((x for x in inspection.declarations if x.field_name == name), None)
            return d.value if d and d.value else default

        prod_name = (prod.product_name if prod and prod.product_name else None) or get_decl("product_name")
        brand_val = (prod.brand if prod and prod.brand else None) or get_decl("brand")
        mfg_val = (prod.manufacturer if prod and prod.manufacturer else None) or get_decl("manufacturer")
        net_qty = (prod.net_quantity if prod and prod.net_quantity else None) or get_decl("net_quantity")
        mrp_val = (prod.mrp if prod and prod.mrp else None) or get_decl("mrp")
        mfg_date = (prod.manufacturing_date if prod and prod.manufacturing_date else None) or get_decl("manufacturing_date")
        consumer_care = (prod.consumer_care if prod and prod.consumer_care else None) or get_decl("consumer_care")
        unit_price = get_decl("unit_sale_price")
        country_origin = get_decl("country_of_origin")

        prod_data = [
            ["Declaration Parameter", "Detected / Declared Value"],
            ["Commodity Classification", Paragraph(f"<b>{inspection.commodity_category or 'GENERAL'}</b> (Category Rule Profile Applied)", normal_style)],
            ["Commodity / Generic Name", Paragraph(prod_name, normal_style)],
            ["Brand", Paragraph(brand_val, normal_style)],
            ["Manufacturer / Packer", Paragraph(mfg_val, normal_style)],
            ["Declared Net Quantity", Paragraph(net_qty, normal_style)],
            ["Maximum Retail Price (MRP)", Paragraph(mrp_val, normal_style)],
            ["Date of Mfg / Packing", Paragraph(mfg_date, normal_style)],
            ["Consumer Helpline Details", Paragraph(consumer_care, normal_style)],
            ["Unit Sale Price (USP)", Paragraph(unit_price, normal_style)],
            ["Country of Origin", Paragraph(country_origin, normal_style)],
            ["Principal Display Panel (PDP)", Paragraph(f"<b>{inspection.pdp_area_cm2 or 250.0} cm²</b> | Calibration: {inspection.calibration_method or 'AUTO_HEURISTIC'}", normal_style)],
            ["Certified Numeral Height", Paragraph(f"<b>{inspection.caliper_override_mm or inspection.calibrated_font_height_mm or 2.5} mm</b>" + (" (Vernier Caliper Certified)" if inspection.caliper_override_mm else " (Optical Bounding Box)"), normal_style)]
        ]
        t1 = Table(prod_data, colWidths=[160, 340])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor("#0b2240")),
            ('TEXTCOLOR', (0,0), (1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        story.append(t1)
        story.append(Spacer(1, 15))

        # Section 2: AI Compliance Checks
        story.append(Paragraph("2. STATUTORY SCREENING CHECKS & RULE COMPLIANCE", h2_style))
        checks_data = [["Rule Reference", "Field", "Status", "Measured / Req.", "Compliance Details"]]
        for check in inspection.compliance_checks:
            rule_title = check.rule.title if check.rule else "General"
            meas_str = f"{check.measured_font_height_mm} mm (Req: >={check.required_font_height_mm} mm)" if check.measured_font_height_mm else "N/A"
            checks_data.append([
                Paragraph(rule_title, normal_style),
                Paragraph(check.field or "N/A", normal_style),
                Paragraph(check.status, normal_style),
                Paragraph(meas_str, normal_style),
                Paragraph(check.message or "", normal_style)
            ])
        t2 = Table(checks_data, colWidths=[120, 65, 55, 100, 160])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0b2240")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3)
        ]))
        story.append(t2)
        story.append(Spacer(1, 15))

        # Section 3: Verification Remarks & Signatures
        story.append(Paragraph("3. OFFICER SIGN-OFF & VERDICT", h2_style))
        sig_data = [
            ["AI Status Result:", inspection.overall_status],
            ["Verification Decision:", inspection.verification_status],
            ["Remarks:", inspection.officer_remarks or "No remarks provided."],
            ["Verified By Officer ID:", str(inspection.verified_by_id or "Pending Signature")],
            ["Supervisor Status:", inspection.supervisor_status]
        ]
        t3 = Table(sig_data, colWidths=[150, 350])
        t3.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9)
        ]))
        story.append(t3)
        story.append(Spacer(1, 20))

        # Disclaimer (Official Mandate)
        disclaimer_text = (
            "IMPORTANT NOTICE: AI-generated results are screening assistance only. "
            "They do not replace official verification, legal determination, or formal court proceedings. "
            "The authorized human metrology officer holds final executive and legal decision-making authority."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build PDF
        doc.build(story)

        # Log PDF Generation to reports database table (update if exists)
        report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
        if report:
            report.storage_path = pdf_path
            report.created_at = datetime.utcnow()
        else:
            report = Report(
                inspection_id=inspection_id,
                generated_by_id=officer_id,
                storage_path=pdf_path,
                rule_version_used="1.0"
            )
            db.add(report)

        # Log system audit action
        audit = AuditLog(
            user_id=officer_id,
            user_identity=f"Officer ID {officer_id}",
            action="REPORT_GENERATED",
            entity_type="report",
            entity_id=inspection_id,
            timestamp=datetime.utcnow(),
            action_metadata={"pdf_filename": pdf_filename},
            ip_address="127.0.0.1"
        )
        db.add(audit)
        
        db.commit()
        return pdf_path

    def generate_analytics_report(self, db, officer_id: int) -> str:
        """
        Generates an aggregated compliance analytics report.
        """
        from app.models.models import Violation, Product
        inspections = db.query(Inspection).all()
        violations = db.query(Violation).all()
        products = db.query(Product).all()

        os.makedirs("reports", exist_ok=True)
        pdf_filename = f"Analytical_Report_{int(datetime.utcnow().timestamp())}.pdf"
        pdf_path = os.path.join("reports", pdf_filename).replace("\\", "/")

        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                                rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name="TitleStyle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#0b2240"), alignment=1, spaceAfter=5
        )
        sub_style = ParagraphStyle(
            name="SubStyle", parent=styles["Normal"], fontSize=9, alignment=1, spaceAfter=20
        )
        h2_style = ParagraphStyle(
            name="H2Style", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#0b2240"), spaceBefore=15, spaceAfter=8
        )

        story.append(Paragraph("LM-ComplianceAuditor Analytics Report", title_style))
        story.append(Paragraph(f"Compiled on {datetime.now().strftime('%d %B %Y %H:%M:%S')} | LM-ComplianceAuditor System (SIH 2026 Prototype)", sub_style))

        # KPI Summary table
        kpi_data = [
            ["Metric Parameter", "Count Value"],
            ["Total Inspections Processed", str(len(inspections))],
            ["Total Compliant Products", str(sum(1 for i in inspections if i.overall_status == 'COMPLIANT'))],
            ["Total Non-Compliances Logged", str(len(violations))],
            ["Registered Rules Database Size", str(db.query(Product).count())]
        ]
        t = Table(kpi_data, colWidths=[200, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0b2240")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f1f5f9")])
        ]))
        story.append(Paragraph("System Aggregated KPI Statistics", h2_style))
        story.append(t)
        story.append(Spacer(1, 15))

        # List of violations
        story.append(Paragraph("Recent Violation Log Brief", h2_style))
        viol_data = [["ID", "Product Name", "Breached Clause", "Severity", "Status"]]
        for v in violations[:10]:
            viol_data.append([
                str(v.id),
                v.inspection.product.product_name[:30] if v.inspection and v.inspection.product else "Generic Item",
                v.violation_type[:30],
                v.severity,
                v.status
            ])
        t2 = Table(viol_data, colWidths=[40, 150, 150, 60, 60])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#475569")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        story.append(t2)

        doc.build(story)
        
        # Log system audit action
        audit = AuditLog(
            user_id=officer_id,
            user_identity=f"Officer ID {officer_id}",
            action="ANALYTICAL_REPORT_GENERATED",
            entity_type="report",
            entity_id="ALL",
            timestamp=datetime.utcnow(),
            action_metadata={"pdf_filename": pdf_filename},
            ip_address="127.0.0.1"
        )
        db.add(audit)
        db.commit()
        
        return pdf_path

report_service = ReportService()
