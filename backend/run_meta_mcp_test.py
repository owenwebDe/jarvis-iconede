import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

from tools import meta_marketing_server

ad_account_id = "act_1373656688269264"
page_id = "675548788978391"

print("================================================================================")
print(f">>> RUNNING mcp_meta_ads_get_account_info FOR {ad_account_id}...")
print("================================================================================")

account_info = meta_marketing_server.meta_ads_get_ad_account(ad_account_id=ad_account_id)
print("\n[RAW JSON RESPONSE - meta_ads_get_ad_account]:")
print(json.dumps(account_info, indent=2))

print("\n================================================================================")
print(f">>> RUNNING mcp_meta_ads_get_campaigns FOR {ad_account_id}...")
print("================================================================================")

campaigns_info = meta_marketing_server.meta_ads_list_campaigns(ad_account_id=ad_account_id)
print("\n[RAW JSON RESPONSE - meta_ads_list_campaigns]:")
print(json.dumps(campaigns_info, indent=2))

print("\n================================================================================")
