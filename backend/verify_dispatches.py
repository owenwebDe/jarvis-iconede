import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\602a906f-5401-4e23-b84d-b675d70dc29b\.system_generated\tasks\task-2601.log"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

matches = re.findall(r"Outgoing text message sent to (\d+@s\.whatsapp\.net):\s*(.*)", text)
print(f"==================================================")
print(f"  TOTAL VERIFIED LIVE WHATSAPP OUTREACH: {len(matches)} MESSAGES")
print(f"==================================================")
for i, (phone, msg) in enumerate(matches, 1):
    num = phone.split("@")[0]
    print(f"[{i:02d}] Recipient: +{num}")
    print(f"     Preview:   {msg[:90]}")
    print("--------------------------------------------------")
