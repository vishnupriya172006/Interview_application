import os
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from app.core.config import settings

class NumberedCanvas(canvas.Canvas):
    """
    Canvas to draw headers, footers, and page numbers dynamically in a two-pass render.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4F46E5"))
        
        # Header
        self.drawString(54, 750, "INTERVIEWGUARD AI - INTEGRITY ASSESSMENT REPORT")
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        self.drawString(54, 45, "Confidential - Generated automatically by InterviewGuard AI.")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 45, page_text)
        self.restoreState()


def calculate_integrity(deepfake_logs, gaze_logs, phone_logs, liveness_logs):
    """
    Calculates weighted integrity metrics:
    - Base score = 100
    - Phone detection: -30 if any phone is detected persistently
    - Deepfake average score > 0.5: -50
    - Looking away > 20% of time: -15
    - Liveness anomalies (no blink detected or is_live False): -15
    Returns (score, risk_level, stats)
    """
    score = 100.0
    stats = {
        "avg_deepfake": 0.0,
        "max_deepfake": 0.0,
        "gaze_away_pct": 0.0,
        "phone_frames_pct": 0.0,
        "avg_liveness": 100.0,
        "phone_detected": False
    }
    
    # Process Deepfake
    if deepfake_logs:
        scores = [l.score for l in deepfake_logs]
        stats["avg_deepfake"] = float(np.mean(scores))
        stats["max_deepfake"] = float(np.max(scores))
        if stats["avg_deepfake"] > 0.4:
            score -= (stats["avg_deepfake"] * 50)
            
    # Process Gaze
    if gaze_logs:
        away_count = sum(1 for l in gaze_logs if l.looking_away)
        stats["gaze_away_pct"] = (away_count / len(gaze_logs)) * 100
        if stats["gaze_away_pct"] > 15:
            score -= min(stats["gaze_away_pct"] * 0.4, 20)
            
    # Process Phone
    if phone_logs:
        phone_count = sum(1 for l in phone_logs if l.phone_detected)
        stats["phone_frames_pct"] = (phone_count / len(phone_logs)) * 100
        if phone_count > 0:
            stats["phone_detected"] = True
            score -= min(phone_count * 10, 35)
            
    # Process Liveness
    if liveness_logs:
        live_count = sum(1 for l in liveness_logs if l.is_live)
        stats["avg_liveness"] = (live_count / len(liveness_logs)) * 100
        if stats["avg_liveness"] < 85:
            score -= (100 - stats["avg_liveness"]) * 0.5
            
    score = max(0.0, min(100.0, score))
    
    if score >= 85:
        risk_level = "Low Risk"
    elif score >= 60:
        risk_level = "Medium Risk"
    else:
        risk_level = "High Risk"
        
    return round(score, 1), risk_level, stats


def generate_pdf_report(interview, db_session) -> str:
    """
    Compiles database logs, runs calculations, and creates the report.
    Returns: PDF absolute file path.
    """
    from app.models.logs import DeepfakePrediction, EyeGazeLog, PhoneDetectionLog, LivenessLog, MonitoringEvent
    
    # Query database for all logs relating to this interview
    deepfake_logs = db_session.query(DeepfakePrediction).filter_by(interview_id=interview.id).all()
    gaze_logs = db_session.query(EyeGazeLog).filter_by(interview_id=interview.id).all()
    phone_logs = db_session.query(PhoneDetectionLog).filter_by(interview_id=interview.id).all()
    liveness_logs = db_session.query(LivenessLog).filter_by(interview_id=interview.id).all()
    events = db_session.query(MonitoringEvent).filter_by(interview_id=interview.id).order_by(MonitoringEvent.timestamp).all()
    
    # Run analytics
    score, risk, stats = calculate_integrity(deepfake_logs, gaze_logs, phone_logs, liveness_logs)
    
    # Update interview instance in database
    interview.integrity_score = score
    interview.risk_level = risk.split()[0].lower() # "low", "medium", "high"
    db_session.add(interview)
    db_session.commit()
    
    # Prepare PDF File Info
    filename = f"report_{interview.meeting_id}_{datetime.now().strftime('%Y%md_%H%M%S')}.pdf"
    pdf_path = os.path.join(settings.REPORTS_DIR, filename)
    
    # Document Template Setup (Margins leaves room for headers/footers)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor("#111827"),
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor("#4F46E5"),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        leading=14
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBodyCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # 1. Title Banner
    story.append(Paragraph("Interview Integrity Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y - %H:%M:%S')}", body_style))
    story.append(Spacer(1, 15))
    
    # 2. Metadata Grid
    meta_data = [
        [Paragraph("Candidate Name:", bold_body_style), Paragraph(interview.candidate_name, body_style),
         Paragraph("Meeting ID:", bold_body_style), Paragraph(interview.meeting_id, body_style)],
        [Paragraph("Candidate Email:", bold_body_style), Paragraph(interview.candidate_email, body_style),
         Paragraph("Interview Date:", bold_body_style), Paragraph(interview.scheduled_at.strftime('%Y-%m-%d %H:%M'), body_style)],
        [Paragraph("Recruiter Name:", bold_body_style), Paragraph(interview.recruiter.full_name, body_style),
         Paragraph("Duration:", bold_body_style), Paragraph(f"{interview.duration_minutes} min", body_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[1.5*inch, 2*inch, 1.2*inch, 2.3*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFB")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#D1D5DB")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # 3. Overall Score Callout Box
    score_color = colors.HexColor("#10B981") if risk == "Low Risk" else (colors.HexColor("#F59E0B") if risk == "Medium Risk" else colors.HexColor("#EF4444"))
    
    score_data = [
        [
            Paragraph("OVERALL INTEGRITY SCORE", ParagraphStyle('ScoreLabel', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#FFFFFF"), alignment=1)),
            Paragraph("RISK ASSESSMENT LEVEL", ParagraphStyle('RiskLabel', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#FFFFFF"), alignment=1))
        ],
        [
            Paragraph(f"<font size='36'><b>{score}/100</b></font>", ParagraphStyle('ScoreNum', fontName='Helvetica', textColor=colors.HexColor("#FFFFFF"), alignment=1)),
            Paragraph(f"<font size='24'><b>{risk.upper()}</b></font>", ParagraphStyle('RiskText', fontName='Helvetica', textColor=colors.HexColor("#FFFFFF"), alignment=1))
        ]
    ]
    score_table = Table(score_data, colWidths=[3.5*inch, 3.5*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), score_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 20))
    
    # 4. Multimodal Metrics Analysis
    story.append(Paragraph("Multimodal Subsystem Analysis", section_style))
    
    metrics_data = [
        [Paragraph("Subsystem Tracked", bold_body_style), Paragraph("Key Metric Evaluated", bold_body_style), Paragraph("Observed Level", bold_body_style), Paragraph("Status", bold_body_style)],
        [
            Paragraph("Deepfake Detection", body_style),
            Paragraph("Average Fake Prob. (Max)", body_style),
            Paragraph(f"{stats['avg_deepfake']*100:.1f}% ({stats['max_deepfake']*100:.1f}%)", body_style),
            Paragraph("FAILED" if stats['avg_deepfake'] > 0.4 else "VERIFIED", ParagraphStyle('SubStatus', fontName='Helvetica-Bold', textColor=colors.HexColor("#EF4444") if stats['avg_deepfake'] > 0.4 else colors.HexColor("#10B981")))
        ],
        [
            Paragraph("Eye Gaze Tracking", body_style),
            Paragraph("Time Looking Away", body_style),
            Paragraph(f"{stats['gaze_away_pct']:.1f}% of total duration", body_style),
            Paragraph("SUSPICIOUS" if stats['gaze_away_pct'] > 20 else "NORMAL", ParagraphStyle('SubStatus', fontName='Helvetica-Bold', textColor=colors.HexColor("#F59E0B") if stats['gaze_away_pct'] > 20 else colors.HexColor("#10B981")))
        ],
        [
            Paragraph("Phone Detection", body_style),
            Paragraph("Device Visibility", body_style),
            Paragraph("Phone detected during interview" if stats['phone_detected'] else "No phone visible", body_style),
            Paragraph("FAILED" if stats['phone_detected'] else "PASSED", ParagraphStyle('SubStatus', fontName='Helvetica-Bold', textColor=colors.HexColor("#EF4444") if stats['phone_detected'] else colors.HexColor("#10B981")))
        ],
        [
            Paragraph("Liveness Assessment", body_style),
            Paragraph("Successful Liveness Ratio", body_style),
            Paragraph(f"{stats['avg_liveness']:.1f}%", body_style),
            Paragraph("ANOMALY" if stats['avg_liveness'] < 85 else "PASSED", ParagraphStyle('SubStatus', fontName='Helvetica-Bold', textColor=colors.HexColor("#EF4444") if stats['avg_liveness'] < 85 else colors.HexColor("#10B981")))
        ],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[1.8*inch, 2.2*inch, 1.8*inch, 1.2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E5E7EB")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#D1D5DB")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # 5. Incident Log Timeline
    story.append(Paragraph("Security Alerts & Incident Logs", section_style))
    if len(events) == 0:
        story.append(Paragraph("No major integrity anomalies or suspicious movements detected during this session.", body_style))
    else:
        event_data = [[Paragraph("Timestamp", bold_body_style), Paragraph("Alert Category", bold_body_style), Paragraph("Severity", bold_body_style), Paragraph("Details / Context", bold_body_style)]]
        for e in events[:15]: # Show top 15 events
            sev_color = colors.HexColor("#EF4444") if e.severity == "high" else (colors.HexColor("#F59E0B") if e.severity == "medium" else colors.HexColor("#6B7280"))
            event_data.append([
                Paragraph(e.timestamp.strftime('%H:%M:%S'), body_style),
                Paragraph(e.event_type.replace('_', ' ').title(), body_style),
                Paragraph(e.severity.upper(), ParagraphStyle('SevCol', fontName='Helvetica-Bold', textColor=sev_color)),
                Paragraph(e.details or "N/A", body_style)
            ])
            
        event_table = Table(event_data, colWidths=[1.0*inch, 1.8*inch, 1.0*inch, 3.2*inch])
        event_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F3F4F6")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#D1D5DB")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(event_table)
        
    story.append(Spacer(1, 20))
    
    # 6. Recommendations / Conclusion
    story.append(KeepTogether([
        Paragraph("Recommendations & Conclusion", section_style),
        Paragraph(
            "<b>Low Risk Status:</b> The integrity check confirms standard candidate responses. Normal eye gaze and blinking patterns were recorded with no spoofing attempts detected. The candidate is recommended for hiring consideration.<br/>"
            if risk == "Low Risk" else
            ("<b>Medium Risk Status:</b> Suspicious gaze deviations or minor device activity was detected during portions of the interview. It is recommended to review the live recording of the flagging events before moving to next stages.<br/>"
             if risk == "Medium Risk" else
             "<b>High Risk Warning:</b> Significant deepfake anomalies, active smartphone usage, or failure to pass liveness challenge-responses was detected. The integrity score suggests active spoofing or cheating. Immediate disqualification or mandatory review is recommended."),
            body_style
        )
    ]))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Save Report record in DB
    report_record = Report(
        interview_id=interview.id,
        pdf_path=pdf_path,
        integrity_score=score,
        risk_level=interview.risk_level
    )
    db_session.add(report_record)
    db_session.commit()
    
    print(f"Generated PDF Report saved at: {pdf_path}")
    return pdf_path
