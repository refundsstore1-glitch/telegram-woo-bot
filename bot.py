import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WC_URL = os.environ.get("WC_URL")
WC_KEY = os.environ.get("WC_KEY")
WC_SECRET = os.environ.get("WC_SECRET")

def get_orders_by_name(name):
r = requests.get(
WC_URL,
auth=(WC_KEY, WC_SECRET),
params={"search": name, "per_page": 10}
)
if r.status_code != 200:
return []
return r.json()

def extract_tracking(order):
meta = order.get("meta_data", [])
for item in meta:
if item["key"] == "_wc_shipment_tracking_items":
data = item["value"]
if isinstance(data, list) and data:
return data[0].get("tracking_number")
return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()

# If user replies with order number
if text.isdigit():
orders = context.user_data.get("orders", [])
for o in orders:
if str(o["id"]) == text:
tracking = extract_tracking(o)
if tracking:
await update.message.reply_text(f"📦 Order #{o['id']}\nTracking: {tracking}")
else:
await update.message.reply_text("Tracking not yet added.")
return

# Treat input as name
orders = get_orders_by_name(text)

if len(orders) == 0:
await update.message.reply_text("❌ No orders found under that name.")
return

if len(orders) == 1:
tracking = extract_tracking(orders[0])
if tracking:
await update.message.reply_text(f"📦 Order #{orders[0]['id']}\nTracking: {tracking}")
else:
await update.message.reply_text("Tracking not yet added.")
return

# Multiple orders found
context.user_data["orders"] = orders
msg = "📦 Multiple orders found:\n\n"
for o in orders:
msg += f"• Order #{o['id']} – {o['date_created'][:10]}\n"
msg += "\nReply with the order number."
await update.message.reply_text(msg)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot running...")
app.run_polling()
