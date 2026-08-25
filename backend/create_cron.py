import sqlite3
import os
import sys
import uuid
import time

sys.path.append(os.getcwd())
from core.database import get_db_session, CronJobModel

db = get_db_session()

job = CronJobModel(
    id=str(uuid.uuid4()),
    name='Morning WhatsApp Lead Outreach',
    schedule_cron='0 7 * * *',
    calendar_type='solar',
    one_shot=False,
    exec_mode='agent_turn',
    exec_agent='Outreach',
    exec_payload='Fetch the first 20 leads from the WhatsApp Pipeline using whatsapp_get_lead_pipeline where the stage is NEW. For each lead, use whatsapp_send_autonomous_message to send a calm, professional initial greeting. Example: "Hello [Business Name], good morning! Is this the official WhatsApp line for [Business Name]?" Do NOT mention websites or pricing yet.',
    status='active',
    approval_status='approved',
    created_at=time.time(),
    updated_at=time.time(),
    next_run_at=time.time() + 60 # Set to some future time so cron_server auto-calculates correctly on next sweep
)

db.add(job)
db.commit()
print('Cron job created successfully!')
