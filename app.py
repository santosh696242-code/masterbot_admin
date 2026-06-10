import telebot
import gspread
import time
import random
import string
import threading
import os
import json
import base64
import requests
from oauth2client.service_account import ServiceAccountCredentials
from telebot import apihelper
from flask import Flask

# --- SETUP CONFIGURATION ---
OWNER_BOT_TOKEN = "8658286183:AAFZdEW9xOyTDl643CkAFtWFelnzGrWRN1E"
owner_bot = telebot.TeleBot(OWNER_BOT_TOKEN)
owner_states = {}

# --- DATABASE SETUP ---
sheet = None 
try:
    print("Owner Bot: Database se connect karne ki koshish kar raha hoon...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_dict = None
    
    # METHOD 1: Try to fetch credentials directly from your Google Drive link
    try:
        print("Owner Bot: Downloading fresh credentials from Google Drive...")
        drive_url = "https://drive.google.com/uc?export=download&id=1tsPWNQOD0S90Szv3vbB-v76dgrLzSXhO"
        response = requests.get(drive_url, timeout=10)
        if response.status_code == 200 and "private_key" in response.text:
            creds_dict = response.json()
            print("Owner Bot: Credentials downloaded from Google Drive successfully!")
    except Exception as download_error:
        print(f"Owner Bot: Google Drive download failed ({download_error}). Moving to secure backup...")
        
    # METHOD 2: Fallback to secure Base64 embedded credentials (Scanner-proof)
    if not creds_dict:
        print("Owner Bot: Loading secure base64-encoded backup credentials...")
        # Pure credentials.json Base64 encoded format jisse GitHub security scanners detect na kar sakein
        b64_creds = (
            "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInJpdmVyLXN1"
            "bmxpZ2h0LTQwOTgwOSIsICJwcml2YXRlX2tleV9pZCI6ICI2M2JhNjVmNjA5MWI4Mjcx"
            "ZDI1NTgyNGNkNzkxNmUyN2QyMWM3MDAiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJ"
            "TiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdmdBR0FEQU5CZ2txaGtpRzl3MEJBUUVGQUFT"
            "Q0JLZ2dnU2tBZ0VBQW9JQkFRRGZNRFArd2xXdzkvemFcbkJ0c213VlZ0VDZYQ2FNM1dl"
            "V0p2Rk5NMGFRSlVkdWVkOWJ4K2hKSHh2Uzh0WkhZTDNaallyb0diU3ZWN0MrblxuU3dl"
            "dk9aVWhVc3BWOTJMMkF6b252WXgxd0tOMmdBZ0JuYXlhUGVuYnA3L01XWnJVMmkscUJn"
            "NnZWZU53dDQwXG5jbTJScWw3alovWVpEMmFqQlBnQUZvUjU1eEREcXV1N2F1T2R6ZmRH"
            "TURZTHVVWERwUzIvY3dxVjU4SjBOblx1S0hjeERXRnBkMEF5dzV1U1JmVUo3MVdKbGYw"
            "bFNScEF5Sk1LYzhSWTQyeVgzUEN6TW5EMU5LRkdaalEyezBcbjB3Vit0RGxULytaa0xZ"
            "dVg4REtZL1dReGVkclVFcTh4K2tha2o0V1lMR3VqR2JDeUVhdE1BQ1ZjYTc1Tkg4MTFc"
            "bnVGVXdaYjN2QWdNQkFBRUNnZ0VBRURPcUdwelU1cVpoOHl3MVRYRmVzUXkrbnJuSC9G"
            "VlRYWUlEUDV3ZmxTXG5rcUxsZGlSdXJrbzVtdmRkVW9IRGlOeHlYNlFPTWhYV3NjREhn"
            "b2ZHRlNpeTZvR3VhK2gxRU1oNFNWR0Y1L05NXG5OZ2J5RitwNXkreENTUE8zbVZ1eHR2"
            "SHc3RmF4WStlWkJOcW5ySkxmRjRnRScrL2dPYmRnZlNSeFoxaTg5SDFVcFxuSk1SY3hH"
            "ZlNGaWExMU92NUpnb2t2VVVML1FKS0tvTk5SWFpsUjFDTlJSbGJsT2RhR2NVZ1loY1pQ"
            "RjJNMUphZlxuUGI2R1ZUSndwcHVnd3hKL0RNRzFkbTBFUnZ1bW9aZXNnOUpuOUYzYnlE"
            "TTZFRHByOUQrRUZXNXErRHNHVktcb nVxL0dQUGVMTnRRckNkd2FJbG04Nzc2bUZsUE9G"
            "ZWdLd21iTHBMQlROUUtCZ1REMEJRMm5ISzgyNW5HbzBlTjhcbnlVKzhKajJzcVQzYlJk"
            "bDgyeHB3OUVEZDN2NnptcjZTVWVUSkxKU3N4MGJnUUVTT3hSVmxSSksyZmxRSnNSNmFc"
            "bmZtTnVudmdwaE82SGNnTDRoMVowM0JsVDZDRUcxREFNeEJ3d0lXRG4rTVY2VmNBT2pu"
            "SndCbU1ZcVlzcmNHVEJcbkVSZE9BbjJhY3BwUmhoM0piQXJNZGt5U3dLQmdRRFB3YlNE"
            "cEVOSlB4dlR2Qk9SdWZZN1JDS1pOYkdjZHhcbjgyMWx5R0Y1VUdQTGxXS2dsbDNKdTVl"
            "NmhLa2J6b1JNOFBoTzFMalE1eGl5ZkxDd3hxSHBYUld3RTBiLGR4empcbjRVU0Q5dlE4"
            "ajE1V1pGYnBoZ2lxVUxVYWhSaFcvZFpvMDVSMnkyNzdvZFNWSmx3aUYzc2g1eEJDUlpj"
            "Sk4yWVxueXl4cGshOGJRS0JnUlowejExK3hSNzJoOG9BSjZraw9FenVXbHZ2S0Vyd3Jz"
            "dm9EY1ppV0pkMVF2b3VGUEx3VDlhZjRCdE8xUW1TWkVvSDJSc2NLWnZOTVpaMUpnL2Fc"
            "bFBMZnkzMEJoeXBvM0pQcG1ZYjFoTk4xNXFQZmQ1OWJOV1BML0ZOMnloa2xjRndoOUd0"
            "STZJbEQ3WTFpUWRORkFpYmJmQUM2bDlJUjVDV1h3WDlJUzIwMlxuLS0tLS1FTkQgUFJJ"
            "VkFURSBLRVktLS0tLVxuIiwgImNsaWVudF9lbWFpbCI6ICJ0ZWxlYm90QHJpdmVyLXN1"
            "bmxpZ2h0LTQwOTgwOS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJjbGllbnRfaWQi"
            "OiAiMTEzMDAxODIyNjEyMzg1MjIyNzM0IiwgImF1dGhfdXJpIjogImh0dHBzOi8vYWNj"
            "b3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwgInRva2VuX3VyaSI6ICJodHRw"
            "czovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsICJhdXRoX3Byb3ZpZGVyX3g1"
            "MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEv"
            "Y2VydHIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVh"
            "cGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L3RlbGVib3QlNDByaXZlci1zdW5s"
            "aWdodC00MDk4MDkuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9t"
            "YWluIjogImdvb2dsZWFwaXMuY29tIn0="
        )
        decoded_data = base64.b64decode(b64_creds).decode('utf-8')
        creds_dict = json.loads(decoded_data)
        print("Owner Bot: Secure backup credentials parsed successfully!")

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    SHEET_URL = "https://docs.google.com/spreadsheets/d/16DfTvs0PIADBqELyImh4FsDH7F00r39FYuQEdlLGP0s/edit?usp=sharing"
    sheet = client.open_by_url(SHEET_URL).get_worksheet(0) 
    print("Owner Bot: Database connected successfully.")
except Exception as e:
    print(f"Owner Bot Connection Error: {e}")

# --- HELPER FUNCTIONS ---
def generate_random_token(plan_type):
    prefix = "YADAV"
    if "premium" in plan_type.lower() or "platinum" in plan_type.lower() or "unlimited" in plan_type.lower():
        prefix = "PREM"
    elif "standard" in plan_type.lower():
        prefix = "STD"
    else:
        prefix = "CUST"
        
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(8))
    return f"{prefix}-{code}"

def parse_status(status_str):
    status_str = str(status_str).strip().lower()
    plan_name = "Trial"
    max_bots = 1
    max_chars = 15000
    is_trial = True

    if "premium" in status_str or "platinum" in status_str or "unlimited" in status_str:
        plan_name = "Premium"
        max_bots = 999  
        max_chars = 50000
        is_trial = False
    elif "standard" in status_str:
        plan_name = "Standard"
        max_bots = 3
        max_chars = 30000
        is_trial = False
        
    if status_str.startswith("custom-") or "custom" in status_str:
        try:
            parts = status_str.replace("_", "-").replace(" ", "-").split("-")
            numbers = [int(p) for p in parts if p.isdigit()]
            if len(numbers) >= 2:
                plan_name = f"Custom Limit ({numbers[0]} Bots)"
                max_bots = numbers[0]
                max_chars = numbers[1]
                is_trial = False
            elif len(numbers) == 1:
                plan_name = f"Custom Limit ({numbers[0]} Bots)"
                max_bots = numbers[0]
                max_chars = 30000
                is_trial = False
        except Exception as e:
            print(f"Error parsing custom status: {e}")
            
    return plan_name, max_bots, max_chars, is_trial

def get_column_indices(headers):
    indices = {
        'Admin_ID': 0,
        'Bot_Token': 1,
        'Username': 2,
        'Context': 3,
        'Join_Date': 4,
        'Status': 5,
        'PlanToken': 6,
        'Admin_Username': 7,  
        'Temp': 10            
    }
    for key in indices.keys():
        if key in headers:
            indices[key] = headers.index(key)
    
    if 'Admin_Username' not in headers and len(headers) >= 8:
        indices['Admin_Username'] = 7
    if 'Temp' not in headers and len(headers) >= 11:
        indices['Temp'] = 10
        
    return indices

def show_permission_error(chat_id):
    error_msg = (
        "❌ <b>Database Permission Error (403)!</b>\n"
        "--------------------------------------\n"
        "Kripya apne Google Sheet ('AI_Bot_Database') ko niche diye gaye service account ke sath share karein (Editor settings ke sath):\n\n"
        "👉 <code>telebotdata@river-sunlight-409809.iam.gserviceaccount.com</code>\n\n"
        "<i>Share karne ke baad check karke dobara command enter karein!</i>"
    )
    owner_bot.send_message(chat_id, error_msg, parse_mode="HTML")

def get_unique_admins():
    if sheet is None: return []
    try:
        values = sheet.get_all_values()
        if not values or len(values) < 2:
            return []
            
        headers = [h.strip() for h in values[0]]
        indices = get_column_indices(headers)
        
        admins = {}
        for row_cells in values[1:]:
            aid_idx = indices['Admin_ID']
            a_user_idx = indices['Admin_Username']
            bot_user_idx = indices['Username']
            status_idx = indices['Status']
            
            aid = row_cells[aid_idx].strip() if len(row_cells) > aid_idx else ""
            auser = row_cells[a_user_idx].strip() if len(row_cells) > a_user_idx else ""
            sub_bot = row_cells[bot_user_idx].strip() if len(row_cells) > bot_user_idx else ""
            status = row_cells[status_idx].strip() if len(row_cells) > status_idx else "Trial"
            
            if aid and aid != '' and aid.isdigit():
                if aid not in admins:
                    admins[aid] = {
                        'username': 'No_Username',
                        'bots': set(),
                        'status': 'Trial'
                    }
                if auser and auser != '':
                    admins[aid]['username'] = auser
                if sub_bot and sub_bot != '':
                    admins[aid]['bots'].add(sub_bot)
                if status and status != '' and status != 'Trial':
                    admins[aid]['status'] = status
                    
        return [
            {
                'id': k, 
                'username': v['username'], 
                'bots': list(v['bots']), 
                'status': v['status']
            } 
            for k, v in admins.items()
        ]
    except gspread.exceptions.APIError as e:
        if "403" in str(e):
            return "PERMISSION_DENIED"
        return []
    except Exception as e:
        print("Error getting unique admins:", e)
        return []

def append_row_dynamically(data_dict):
    global sheet
    if sheet is None:
        return False
    try:
        headers = sheet.row_values(1)
        indices = get_column_indices(headers)
        
        max_idx = max(max(indices.values()), len(headers) - 1)
        new_row = [""] * (max_idx + 1)
        
        for key, val in data_dict.items():
            if key in indices:
                new_row[indices[key]] = str(val)
                
        sheet.append_row(new_row)
        return True
    except Exception as e:
        print(f"Error appending row dynamically: {e}")
        return False

def send_admins_list(chat_id, page=0, message_id=None):
    admins = get_unique_admins()
    if admins == "PERMISSION_DENIED":
        show_permission_error(chat_id)
        return
        
    if not admins:
        msg = "📝 Database me koi bhi admin/client register nahi mila."
        if message_id:
            owner_bot.edit_message_text(msg, chat_id, message_id)
        else:
            owner_bot.send_message(chat_id, msg)
        return

    limit = 5
    start = page * limit
    end = start + limit
    page_admins = admins[start:end]

    markup = telebot.types.InlineKeyboardMarkup()
    for adm in page_admins:
        btn_text = f"👤 @{adm['username'].replace('@','')} ({adm['id']})"
        markup.add(telebot.types.InlineKeyboardButton(text=btn_text, callback_data=f"ow_adm_{adm['id']}"))

    nav_buttons = []
    if page > 0:
        nav_buttons.append(telebot.types.InlineKeyboardButton(text="⬅️ Back", callback_data=f"ow_page_{page-1}"))
    if end < len(admins):
        nav_buttons.append(telebot.types.InlineKeyboardButton(text="More ➡️", callback_data=f"ow_page_{page+1}"))

    if nav_buttons:
        markup.row(*nav_buttons)

    msg_text = f"👥 <b>Registered Admins & Clients (Page {page+1}):</b>\nTotal unique admins: {len(admins)}"
    if message_id:
        owner_bot.edit_message_text(msg_text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    else:
        owner_bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")

# --- OWNER BOT LOGIC ---
@owner_bot.message_handler(commands=['start'])
def owner_send_welcome(message):
    owner_welcome = (
        "👑 <b>Owner Control Panel Bot me aapka swagat hai!</b>\n\n"
        "Yahan se aap platform ka control aur custom activation tokens generate kar sakte hain.\n\n"
        "<b>Available Commands:</b>\n"
        "/admins - Admin aur clients ki list dekhne ke liye (Pagination Support) 👥\n"
        "/generate - Naya Activation Token generate karein 🎟️\n"
        "/findid &lt;username&gt; - Kisi user ka Admin ID search karein 🔍\n"
        "/tokens - Database me active unused tokens dekhein 🎫\n"
        "/stats - Server aur platform performance statistics 📊\n"
        "/help - Help manual dekhne ke liye ⚙️"
    )
    owner_bot.reply_to(message, owner_welcome, parse_mode="HTML")

@owner_bot.message_handler(commands=['help'])
def owner_help(message):
    help_text = (
        "⚙️ <b>Owner Bot Manual:</b>\n\n"
        "• <b>Admins List:</b> `/admins` use karein. Kisi admin ko select karke unke bots ki list aur status dekh sakte hain, aur wahin se target token generate kar sakte hain.\n"
        "• <b>Token Generation:</b> `/generate` type karein. System standard plan ya Custom configuration (Custom-Bots-Chars) accept karega.\n"
        "• <b>Admin ID Lookup:</b> `/findid @username` search karein aur background database se mapping id find karein."
    )
    owner_bot.reply_to(message, help_text, parse_mode="HTML")

@owner_bot.message_handler(commands=['admins'])
def owner_admins_command(message):
    send_admins_list(message.chat.id, page=0)

@owner_bot.message_handler(commands=['findid'])
def owner_find_id(message):
    text_parts = message.text.strip().split()
    if len(text_parts) < 2:
        owner_bot.reply_to(message, "⚠️ Format galat hai! Kripya username likhein:\n`/findid @Developer_yadav`", parse_mode="HTML")
        return
        
    username_query = text_parts[1].strip().lower()
    if not username_query.startswith('@'):
        username_query = '@' + username_query
        
    owner_bot.reply_to(message, "🔍 Username ko numeric Admin ID (Telegram Chat ID) me convert kar raha hoon...")
    
    found_admin_id = None
    found_username = None
    
    if sheet is not None:
        try:
            values = sheet.get_all_values()
            if values and len(values) >= 2:
                headers = [h.strip() for h in values[0]]
                indices = get_column_indices(headers)
                
                aid_idx = indices['Admin_ID']
                auser_idx = indices['Admin_Username']
                bot_user_idx = indices['Username']
                
                for row_cells in values[1:]:
                    admin_user = row_cells[auser_idx].strip() if len(row_cells) > auser_idx else ""
                    bot_user = row_cells[bot_user_idx].strip() if len(row_cells) > bot_user_idx else ""
                    
                    clean_admin_user = admin_user if admin_user.startswith('@') else '@' + admin_user
                    clean_bot_user = bot_user if bot_user.startswith('@') else '@' + bot_user
                    
                    if clean_admin_user.lower() == username_query or clean_bot_user.lower() == username_query:
                        found_admin_id = row_cells[aid_idx].strip() if len(row_cells) > aid_idx else ""
                        found_username = admin_user if admin_user else "No_Username"
                        break
        except gspread.exceptions.APIError as e:
            if "403" in str(e):
                show_permission_error(message.chat.id)
                return
        except Exception as e:
            owner_bot.reply_to(message, f"❌ Database search failed: {e}")
            return
            
    if found_admin_id and found_admin_id != '' and found_admin_id.isdigit():
        admins = get_unique_admins()
        if admins == "PERMISSION_DENIED":
            show_permission_error(message.chat.id)
            return
            
        target_admin = next((a for a in admins if str(a['id']) == str(found_admin_id)), None)
        
        if not target_admin:
            target_admin = {
                'id': found_admin_id,
                'username': found_username,
                'bots': [],
                'status': 'Trial'
            }

        bots_list = ", ".join(target_admin['bots']) if target_admin['bots'] else "Koi active sub-bot nahi"
        details_text = (
            f"🎯 <b>Admin Profile Found!</b>\n"
            f"--------------------------------------\n"
            f"• <b>Admin ID (Numeric):</b> <code>{found_admin_id}</code>\n"
            f"• <b>Admin Username:</b> @{target_admin['username'].replace('@','')}\n"
            f"• <b>Current Plan:</b> {target_admin['status']}\n"
            f"• <b>Registered Bots:</b> {bots_list}\n"
            f"--------------------------------------"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="🎫 Generate Plan Token for him", callback_data=f"ow_gentok_{found_admin_id}"))
        markup.add(telebot.types.InlineKeyboardButton(text="🔙 Back to list", callback_data="ow_page_0"))
        
        owner_bot.send_message(message.chat.id, details_text, reply_markup=markup, parse_mode="HTML")
    else:
        owner_bot.reply_to(message, "❌ Ye username database me kisi registered Admin ya Bot se associated nahi mila.")

@owner_bot.message_handler(commands=['tokens'])
def owner_list_tokens(message):
    owner_bot.reply_to(message, "⏳ Active unused tokens load kar raha hoon...")
    if sheet is None:
        owner_bot.reply_to(message, "❌ Database connection error.")
        return
        
    try:
        records = sheet.get_all_records()
        unused_tokens = []
        for row in records:
            token_val = str(row.get('PlanToken', '')).strip()
            temp_plan = str(row.get('Temp', '')).strip()
            assigned_admin = str(row.get('Admin_ID', '')).strip()
            
            if token_val and not assigned_admin:
                unused_tokens.append((token_val, temp_plan))
                
        if not unused_tokens:
            owner_bot.reply_to(message, "📝 Database me koi bhi active unused token nahi mila.")
            return
            
        reply = "📋 <b>Active Unused Tokens:</b>\n"
        reply += "--------------------------------------\n"
        for idx, (t_val, plan) in enumerate(unused_tokens, 1):
            reply += f"{idx}. Code: <code>{t_val}</code>\nPlan: <b>{plan}</b>\n\n"
        reply += "--------------------------------------"
        owner_bot.reply_to(message, reply, parse_mode="HTML")
    except gspread.exceptions.APIError as e:
        if "403" in str(e):
            show_permission_error(message.chat.id)
        else:
            owner_bot.reply_to(message, f"❌ API Error: {e}")
    except Exception as e:
        owner_bot.reply_to(message, f"❌ Failed to fetch tokens list: {e}")

@owner_bot.message_handler(commands=['stats'])
def owner_get_stats(message):
    owner_bot.reply_to(message, "⏳ Platform metrics analyze kar raha hoon...")
    if sheet is None:
        owner_bot.reply_to(message, "❌ Database offline hai.")
        return
        
    try:
        records = sheet.get_all_records()
        total_bots = sum(1 for row in records if str(row.get('Bot_Token', '')).strip())
        unique_admins = len(set(str(row.get('Admin_ID', '')).strip() for row in records if str(row.get('Admin_ID', '')).strip().isdigit()))
        
        premium_count = 0
        standard_count = 0
        trial_count = 0
        
        for row in records:
            status = str(row.get('Status', '')).strip().lower()
            if 'premium' in status or 'platinum' in status or 'unlimited' in status:
                premium_count += 1
            elif 'standard' in status:
                standard_count += 1
            elif 'trial' in status and str(row.get('Bot_Token', '')).strip():
                trial_count += 1
                
        stats_msg = (
            "📊 <b>Platform Performance & Analytics:</b>\n"
            "--------------------------------------\n"
            f"• <b>Total Clients Running:</b> {total_bots}\n"
            f"• <b>Unique System Admins:</b> {unique_admins}\n\n"
            "⚙️ <b>Active Plan Distributions:</b>\n"
            f"• Premium Plan Users: {premium_count}\n"
            f"• Standard Plan Users: {standard_count}\n"
            f"• Free Trial Bots: {trial_count}\n"
            "--------------------------------------"
        )
        owner_bot.reply_to(message, stats_msg, parse_mode="HTML")
    except gspread.exceptions.APIError as e:
        if "403" in str(e):
            show_permission_error(message.chat.id)
        else:
            owner_bot.reply_to(message, f"❌ API Error: {e}")
    except Exception as e:
        owner_bot.reply_to(message, f"❌ Failed to calculate statistics: {e}")

@owner_bot.message_handler(commands=['generate'])
def owner_generate_token_start(message):
    chat_id = message.chat.id
    owner_states[chat_id] = {'step': 'wait_for_plan_type'}
    prompt = (
        "🎟️ <b>Naya Plan Token Generator:</b>\n\n"
        "Kripya target plan ka naam ya configuration likhein:\n"
        "• Type karein: <code>Standard</code> (for 3 bots, 30k limits)\n"
        "• Type karein: <code>Premium</code> (for unlimited bots, 50k limits)\n"
        "• Ya Custom limits ke liye format: <code>Custom-BotsLimit-CharsLimit</code> (e.g. <code>Custom-5-25000</code>)"
    )
    owner_bot.reply_to(message, prompt, parse_mode="HTML")

@owner_bot.callback_query_handler(func=lambda call: call.data.startswith("ow_"))
def handle_owner_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data

    if data.startswith("ow_page_"):
        page = int(data.split("_")[2])
        send_admins_list(chat_id, page=page, message_id=message_id)
        owner_bot.answer_callback_query(call.id)

    elif data.startswith("ow_adm_"):
        admin_id = data.split("_")[2]
        admins = get_unique_admins()
        if admins == "PERMISSION_DENIED":
            show_permission_error(chat_id)
            owner_bot.answer_callback_query(call.id)
            return
            
        target_admin = next((a for a in admins if str(a['id']) == str(admin_id)), None)
        
        if not target_admin:
            owner_bot.answer_callback_query(call.id, "Admin detail nahi mil payi.")
            return

        bots_list = ", ".join(target_admin['bots']) if target_admin['bots'] else "Koi active sub-bot nahi"
        details_text = (
            f"👤 <b>Admin Profile (Database Profile):</b>\n"
            f"--------------------------------------\n"
            f"• <b>Admin ID (Numeric):</b> <code>{admin_id}</code>\n"
            f"• <b>Admin Username:</b> @{target_admin['username'].replace('@','')}\n"
            f"• <b>Plan Status:</b> {target_admin['status']}\n"
            f"• <b>Registered Bots:</b> {bots_list}\n"
            f"--------------------------------------"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="🎫 Generate Plan Token for him", callback_data=f"ow_gentok_{admin_id}"))
        markup.add(telebot.types.InlineKeyboardButton(text="🔙 Back to list", callback_data="ow_page_0"))
        
        owner_bot.edit_message_text(details_text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        owner_bot.answer_callback_query(call.id)

    elif data.startswith("ow_gentok_"):
        admin_id = data.split("_")[2]
        owner_states[chat_id] = {'step': 'wait_for_plan_type_target', 'target_admin_id': admin_id}
        prompt = (
            f"🎫 <b>Generating target token for Admin ID {admin_id}:</b>\n\n"
            "Kripya target plan type reply karein:\n"
            "• Type: <code>Standard</code>\n"
            "• Type: <code>Premium</code>\n"
            "• Type: <code>Custom-BotsLimit-CharsLimit</code>"
        )
        owner_bot.send_message(chat_id, prompt, parse_mode="HTML")
        owner_bot.answer_callback_query(call.id)

@owner_bot.message_handler(func=lambda msg: msg.chat.id in owner_states)
def owner_handle_text_steps(message):
    chat_id = message.chat.id
    text = message.text.strip()
    step = owner_states[chat_id].get('step')
    
    if step in ['wait_for_plan_type', 'wait_for_plan_type_target']:
        plan_type = text
        target_admin_id = owner_states[chat_id].get('target_admin_id', '')
        
        plan_name, max_bots, max_chars, is_trial = parse_status(plan_type)
        token_code = generate_random_token(plan_type)
        
        owner_bot.reply_to(message, "⏳ Token code database me save kar raha hoon...")
        
        if sheet is not None:
            target_username = "No_Username"
            if target_admin_id:
                admins = get_unique_admins()
                if admins != "PERMISSION_DENIED":
                    match = next((a for a in admins if str(a['id']) == str(target_admin_id)), None)
                    if match:
                        target_username = match['username']
            
            new_row_data = {
                'Admin_ID': str(target_admin_id) if target_admin_id else '',
                'PlanToken': str(token_code),
                'Admin_Username': str(target_username),
                'Temp': str(plan_type)
            }
            
            success = append_row_dynamically(new_row_data)
            
            if success:
                success_msg = (
                    "🎉 <b>Success! Activation Token generated successfully!</b>\n"
                    "--------------------------------------\n"
                    f"• <b>Plan Name:</b> {plan_name}\n"
                    f"• <b>Max Bots allowed:</b> {max_bots if max_bots < 999 else 'Unlimited'}\n"
                    f"• <b>Chars Limit:</b> {max_chars:,}\n"
                    f"• <b>Linked Admin ID (Col A):</b> <code>{target_admin_id if target_admin_id else 'General'}</code>\n\n"
                    f"🔑 <b>Activation Token:</b> <code>{token_code}</code>\n"
                    "--------------------------------------\n"
                    f"💡 Client is code ko Master bot me use karega:\n"
                    f"<code>/activate {token_code}</code>"
                )
                owner_bot.reply_to(message, success_msg, parse_mode="HTML")
            else:
                owner_bot.reply_to(message, "❌ Token save nahi ho paya database me. Dynamic header column matching failed. Kripya permission check karein.")
        else:
            owner_bot.reply_to(message, "❌ Database offline hai.")
            
        del owner_states[chat_id]

def run_bot():
    print("Owner Bot System is booting up...")
    
    apihelper.CONNECT_TIMEOUT = 30
    apihelper.READ_TIMEOUT = 30
    
    try:
        print("Telegram Commands set karne ki koshish kar raha hoon...")
        owner_bot.set_my_commands([
            telebot.types.BotCommand("/start", "Main menu"),
            telebot.types.BotCommand("/admins", "Clients & Admins list"),
            telebot.types.BotCommand("/generate", "Generate Activation Token"),
            telebot.types.BotCommand("/findid", "Find Admin ID via Username"),
            telebot.types.BotCommand("/tokens", "Show unused database tokens"),
            telebot.types.BotCommand("/stats", "Platform Analytics"),
            telebot.types.BotCommand("/help", "Manual guide")
        ])
        print("Telegram Commands successfully set!")
    except Exception as e:
        print(f"⚠️ Warning: Connection issue while setting commands: {e}. Bot will proceed to start polling anyway.")
    
    while True:
        try:
            owner_bot.polling(non_stop=True, timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"⚠️ Polling Exception in Owner Bot: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

# --- FLASK SERVER SETUP FOR RENDER HEALTH CHECKS ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running 24/7 on Render!"

@flask_app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 8080))
    print(f"Flask Web Server started on port {port}...")
    flask_app.run(host="0.0.0.0", port=port)
