
import os
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client as TwilioClient
from supabase import create_client

def sb_service():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

def now_utc():
    return datetime.now(timezone.utc)

def send_email(to_email: str, subject: str, body: str):
    user=os.environ.get("GMAIL_USER"); app_pass=os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not app_pass: return
    msg=MIMEText(body,"plain","utf-8"); msg["Subject"]=subject; msg["From"]=user; msg["To"]=to_email
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(user,app_pass); smtp.sendmail(user,[to_email],msg.as_string())

def send_whatsapp(to_number: str, body: str):
    sid=os.environ.get("TWILIO_ACCOUNT_SID"); token=os.environ.get("TWILIO_AUTH_TOKEN"); from_=os.environ.get("TWILIO_WHATSAPP_FROM")
    if not (sid and token and from_ and to_number): return
    tw=TwilioClient(sid,token)
    if not to_number.startswith("whatsapp:"): to_number="whatsapp:"+to_number
    tw.messages.create(from_=from_,to=to_number,body=body)

def main():
    sb=sb_service(); n=now_utc().isoformat()
    rem=(sb.table("reminders").select("id,user_id,item_id,remind_at,channel").is_("sent_at","null").lte("remind_at",n).execute().data or [])
    if not rem: print("No reminders due."); return
    user_ids=sorted({r["user_id"] for r in rem}); item_ids=sorted({r["item_id"] for r in rem if r.get("item_id")})
    profiles=sb.table("profiles").select("id,email,email_notifications,whatsapp_notifications,whatsapp_number").in_("id",user_ids).execute().data or []
    prof_by={p["id"]:p for p in profiles}
    items=sb.table("items").select("id,title,notes,due_at,tag,priority,type").in_("id",item_ids).execute().data or []
    item_by={i["id"]:i for i in items}
    for r in rem:
        uid=r["user_id"]; p=prof_by.get(uid,{}); it=item_by.get(r.get("item_id"),{})
        title=it.get("title","Lembrete"); due=it.get("due_at","")
        body=("PulseAgenda
"+title+"
Prazo: "+due+"
Tag: "+str(it.get('tag','geral'))+"

"+str(it.get('notes') or ''))
        sb.table("inbox_notifications").insert({"user_id":uid,"title":"Lembrete: "+title,"body":body,"source":"reminder","item_id":r.get("item_id")}).execute()
        ch=r["channel"]
        try:
            if ch=="email" and p.get("email_notifications",True) and p.get("email"): send_email(p.get("email"), "PulseAgenda • "+title, body)
            if ch=="whatsapp" and p.get("whatsapp_notifications",False) and p.get("whatsapp_number"): send_whatsapp(p.get("whatsapp_number"), body)
            sb.table("reminders").update({"sent_at": now_utc().isoformat()}).eq("id", r["id"]).execute()
        except Exception as e:
            print("Failed to send reminder", r['id'], e)

if __name__=="__main__":
    main()
