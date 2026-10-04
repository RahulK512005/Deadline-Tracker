"""Generate sample academic document images for instant testing."""
import os
from PIL import Image, ImageDraw, ImageFont


def generate_sample_schedule(output_path: str = "samples/sample_academic_schedule.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 1200, 1500
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header styling
    draw.rectangle([(0, 0), (width, 140)], fill=(30, 58, 138))  # Dark Blue
    
    # Try standard fonts or default
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        sub_font = ImageFont.truetype("arial.ttf", 20)
        heading_font = ImageFont.truetype("arial.ttf", 24)
        body_font = ImageFont.truetype("arial.ttf", 18)
        bold_font = ImageFont.truetype("arialbd.ttf", 18)
    except IOError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        bold_font = ImageFont.load_default()

    draw.text((60, 35), "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", fill=(255, 255, 255), font=title_font)
    draw.text((60, 85), "SEMESTER VI - ACADEMIC DEADLINES & ASSESSMENT SCHEDULE (OCT - NOV 2026)", fill=(219, 234, 254), font=sub_font)

    # Notice Box
    draw.rounded_rectangle([(60, 180), (1140, 260)], radius=8, fill=(241, 245, 249), outline=(203, 213, 225), width=2)
    draw.text((80, 195), "IMPORTANT NOTICE FOR ALL STUDENTS:", fill=(15, 23, 42), font=bold_font)
    draw.text((80, 225), "Strict adherence to submission timelines is required. No extensions will be granted without prior approval.", fill=(71, 85, 105), font=body_font)

    # Schedule Table Header
    y = 300
    draw.rectangle([(60, y), (1140, y + 45)], fill=(226, 232, 240))
    draw.text((80, y + 12), "DATE", fill=(15, 23, 42), font=bold_font)
    draw.text((240, y + 12), "SUBJECT", fill=(15, 23, 42), font=bold_font)
    draw.text((380, y + 12), "TYPE", fill=(15, 23, 42), font=bold_font)
    draw.text((530, y + 12), "DETAILS & DELIVERABLE", fill=(15, 23, 42), font=bold_font)
    draw.text((980, y + 12), "TIME", fill=(15, 23, 42), font=bold_font)

    events = [
        ("03 Oct 2026", "Operating Systems", "Assignment", "Assignment 1: CPU Scheduling Algorithms Simulation", "23:59"),
        ("04 Oct 2026", "Computer Networks", "Quiz", "Online Quiz 2 - Data Link Layer & Subnetting", "14:00"),
        ("07 Oct 2026", "DBMS", "Lab", "Lab Record Submission - SQL Queries & Normalization", "17:00"),
        ("09 Oct 2026", "Software Engg", "Project", "Phase 1 Architecture & SRS Document Submission", "23:59"),
        ("15 Oct 2026", "AI & ML", "Exam", "Mid-Term Examination - Modules 1, 2 & 3", "10:00"),
        ("22 Oct 2026", "Cloud Computing", "Presentation", "Seminar Presentation on Microservices Deployment", "11:30"),
        ("28 Oct 2026", "Web Tech", "Submission", "Frontend & API Integration Project Repository Link", "23:59"),
        ("05 Nov 2026", "Operating Systems", "Exam", "Final Lab Practical & Viva Voce", "09:30"),
    ]

    row_y = y + 55
    for i, (edate, esubject, etype, edetails, etime) in enumerate(events):
        bg_color = (255, 255, 255) if i % 2 == 0 else (248, 250, 252)
        draw.rectangle([(60, row_y - 5), (1140, row_y + 45)], fill=bg_color)
        draw.line([(60, row_y + 45), (1140, row_y + 45)], fill=(226, 232, 240), width=1)

        draw.text((80, row_y + 10), edate, fill=(15, 23, 42), font=bold_font)
        draw.text((240, row_y + 10), esubject, fill=(15, 23, 42), font=body_font)
        draw.text((380, row_y + 10), etype, fill=(37, 99, 235), font=bold_font)
        draw.text((530, row_y + 10), edetails, fill=(51, 65, 85), font=body_font)
        draw.text((980, row_y + 10), etime, fill=(220, 38, 38), font=body_font)
        row_y += 55

    # Footer
    draw.line([(60, 1380), (1140, 1380)], fill=(203, 213, 225), width=2)
    draw.text((60, 1400), "Dean of Academic Affairs | CSE Department Office | Room 304", fill=(100, 116, 139), font=sub_font)
    draw.text((900, 1400), "Date of Issue: 01 Oct 2026", fill=(100, 116, 139), font=sub_font)

    img.save(output_path, "PNG")
    print(f"Sample schedule generated at {output_path}")


if __name__ == "__main__":
    generate_sample_schedule()
