from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from django_backend.legacy import models as m

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def id_card(request):
    buf=BytesIO();pdf=canvas.Canvas(buf,pagesize=A4);w,h=A4;p=m.UserProfile.objects.filter(user_id=request.user.id).first()
    ms=m.InstitutionMembership.objects.filter(user_id=request.user.id,status="active");inst=m.Institution.objects.filter(pk=ms.first().institution_id).first() if ms.exists() else None
    pdf.setTitle("CampusHub Student ID Card");pdf.roundRect(40,h-300,w-80,180,10);pdf.setFont("Helvetica-Bold",18);pdf.drawString(60,h-155,"CAMPUSHUB");pdf.setFont("Helvetica-Bold",13);pdf.drawString(60,h-180,"STUDENT ID CARD");pdf.setFont("Helvetica",10)
    for y,label,value in [(205,"Name",getattr(p,"full_name","")),(222,"Student ID",getattr(p,"student_id","")),(239,"Program",getattr(p,"program","")),(256,"Department",getattr(p,"department","")),(273,"University",getattr(inst,"name","") if inst else "")]:pdf.drawString(60,h-y,f"{label}: {value or ''}")
    pdf.save();buf.seek(0);return FileResponse(buf,as_attachment=True,filename="campushub-student-id-card.pdf",content_type="application/pdf")

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transcript_pdf(request):
    buf=BytesIO();pdf=canvas.Canvas(buf,pagesize=A4);w,h=A4;p=m.UserProfile.objects.filter(user_id=request.user.id).first();pdf.setTitle("CampusHub Official Transcript")
    pdf.setFont("Helvetica-Bold",18);pdf.drawString(50,h-55,"CampusHub — Official Transcript");pdf.setFont("Helvetica",10);pdf.drawString(50,h-78,"Student: "+str(getattr(p,"full_name","")));pdf.drawString(50,h-94,"Student ID: "+str(getattr(p,"student_id","")));pdf.drawString(50,h-110,"Program: "+str(getattr(p,"program","")))
    rs=list(m.Result.objects.filter(student_id=request.user.id,published=True));y=h-145;pdf.setFont("Helvetica-Bold",10);pdf.drawString(50,y,"Course");pdf.drawString(300,y,"Grade");pdf.drawString(380,y,"Point");pdf.drawString(450,y,"Credits");y-=18;pdf.setFont("Helvetica",9);credits=points=0
    for r in rs:
        c=m.Course.objects.filter(pk=r.course_id).first();pdf.drawString(50,y,((c.code+" — "+c.title) if c else str(r.course_id))[:42]);pdf.drawString(300,y,r.grade);pdf.drawString(380,y,f"{r.grade_point:.2f}");pdf.drawString(450,y,f"{r.credits:.1f}");credits+=r.credits;points+=r.credits*r.grade_point;y-=15
        if y<55:pdf.showPage();y=h-55
    pdf.setFont("Helvetica-Bold",11);pdf.drawString(50,y-10,f"CGPA: {(points/credits if credits else 0):.2f}   Total Credits: {credits:.1f}");pdf.save();buf.seek(0);return FileResponse(buf,as_attachment=True,filename="campushub-transcript.pdf",content_type="application/pdf")
