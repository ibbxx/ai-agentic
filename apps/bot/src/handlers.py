"""
Telegram Bot Handlers - With Groq LLM and UI automation.
"""
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.db import crud
from core.parser import parse_message, Intent
from core.agent.planner import make_plan
from core.agent.formatter import format_reply
from core.agent.guardrails import is_high_risk, get_risk_description
from core.agent.tools import task_tool, scheduler_tool, approval_tool
from core.agent.tools import shell_tool, file_tool, app_tool, ui_tool, vision_tool, media_tool
from core.config import get_settings
from groq import Groq
import json
import logging
import os

logger = logging.getLogger(__name__)
settings = get_settings()

TOOL_REGISTRY = {
    "task_tool": task_tool,
    "scheduler_tool": scheduler_tool,
    "approval_tool": approval_tool,
    "shell_tool": shell_tool,
    "file_tool": file_tool,
    "app_tool": app_tool,
    "ui_tool": ui_tool,
    "vision_tool": vision_tool,
    "media_tool": media_tool,
}

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    try:
        telegram_user_id = str(update.effective_user.id)
        name = update.effective_user.first_name or f"User_{telegram_user_id[-4:]}"
        
        user = crud.get_or_create_user(telegram_user_id, name)
        
        await update.message.reply_text(
            f"👋 Hi {name}!\n\n"
            "I'm your AI assistant (powered by Groq). Commands:\n\n"
            "📋 *Tasks:* `add task`, `list tasks`, `done <id>`\n"
            "💻 *Apps:* `buka chrome`, `tutup spotify`\n"
            "🎵 *Media:* `putar lagu mcr`\n"
            "🖥️ *UI:* `screenshot`, `click 500 300`\n"
            "🤖 *AI:* Just ask anything in natural language!\n\n"
            "Try: `screenshot` atau `apa kabar?`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in start handler: {e}", exc_info=True)
        await update.message.reply_text(f"Error: {str(e)[:100]}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages."""
    try:
        telegram_user_id = str(update.effective_user.id)
        text = update.message.text.strip()
        
        if not text:
            return
        
        # Get or create user
        user = crud.get_or_create_user(telegram_user_id)
        user_id = user["id"]
        
        # Log message
        try:
            crud.log_message(user_id, text, "telegram")
        except:
            pass
        
        # Parse message
        parsed = parse_message(text)
        logger.info(f"Parsed intent: {parsed.intent}, params: {parsed.params}")
        
        # INTERCEPTOR: Force media_tool for music commands
        # This bypasses LLM unpredictability for simple media requests
        import re
        media_match = re.search(r"(?:putar|play|dengar|ganti lagu)\s+(.+)", text, re.IGNORECASE)
        if media_match:
            query = media_match.group(1).strip()
            # Clean up query (remove 'lagu', 'musik', etc if needed, but search usually handles it)
            logger.info(f"Interceptor caught media request: {query}")
            plan = {
                "steps": [
                    {"tool": "media_tool", "action": "play_music", "params": {"query": query}}
                ]
            }
        
        # If parser didn't understand, try Groq LLM
        elif parsed.intent == Intent.UNKNOWN and settings.GROQ_API_KEY:
            logger.info("Using Groq LLM fallback")
            llm_result = await get_groq_response(text)
            
            # Check if it's a tool command or just chat
            if llm_result.get("is_tool_command"):
                plan = llm_result
            else:
                # Just chat response
                await update.message.reply_text(llm_result.get("response", "🤔"))
                return
        else:
            plan = make_plan(parsed)
        
        # Execute plan
        result = await execute_plan_with_photos(plan, user_id, update)
        
        # Format reply
        verify = {"ok": not result.get("error")}
        reply = format_reply(parsed, result, verify)
        
        await update.message.reply_text(reply)
        
    except Exception as e:
        logger.error(f"Error in message handler: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ Error: {str(e)[:200]}")

async def get_groq_response(text: str) -> dict:
    """Use Groq LLM for understanding and chat."""
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": """Kamu adalah asisten AI yang ramah dan helpful, berbicara dalam Bahasa Indonesia.

Jika user meminta melakukan sesuatu di komputer (buka app, kirim file, screenshot, lihat layar), respond dengan JSON:
{"is_tool_command": true, "steps": [{"tool": "app_tool", "action": "open", "params": {"app": "Chrome"}}]}

Tools yang tersedia:
- app_tool: open, close (params: app, url)
- ui_tool: screenshot, click, type, scroll, hotkey (params: x, y, text, direction, keys)
- shell_tool: run (params: command)
- task_tool: create, list, close (params: title, task_id)
- file_tool: read, list, send, find_latest (params: path)
- vision_tool: analyze, find_element, describe (params: question, element)
- media_tool: play_music (params: query) - WAJIB digunakan untuk Youtube/Spotify.

PENTING:
- **JANGAN** gunakan `app_tool` untuk membuka `youtube.com/results`! Itu hanya membuka halaman search, tidak memutar lagu.
- **SELALU** gunakan `media_tool` action `play_music` jika user ingin mendengar/memutar sesuatu. Tool ini akan otomatis mencari dan MEMUTAR video.

Contoh BENAR (Putar MCR):
- "putar lagu mcr" -> 
  {"steps": [
    {"tool": "media_tool", "action": "play_music", "params": {"query": "mcr"}}
  ]}

Contoh SALAH (Jangan lakukan ini):
- {"tool": "app_tool", "action": "open", "params": {"url": "youtube.com/results..."}}  <- SALAH!

Jika user request aneh/kompleks, baru gunakan ui_tool. Tapi untuk musik, wajib media_tool.

Jika user hanya ngobrol/tanya, respond dengan JSON:
{"is_tool_command": false, "response": "jawaban kamu disini"}

SELALU respond dalam format JSON."""},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        logger.info(f"Groq response: {content}")
        
        # Try to parse as JSON
        try:
            return json.loads(content)
        except:
            # If not JSON, treat as chat response
            return {"is_tool_command": False, "response": content}
        
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return {"is_tool_command": False, "response": f"Maaf, ada error: {str(e)[:100]}"}

async def execute_plan_with_photos(plan: dict, user_id: int, update: Update, bypass_risk: bool = False) -> dict:
    """Execute plan and send photos if needed."""
    results = []
    
    steps = plan.get("steps", [])
    
    if not steps:
        return {
            "success": False,
            "error": "no_steps",
            "fallback": plan.get("fallback")
        }
    
    # 1. RISK CHECK AGGREGATION
    if not bypass_risk:
        risky_steps = []
        for step in steps:
            tool_name = step.get("tool")
            action = step.get("action")
            if is_high_risk(tool_name, action):
                risky_steps.append(step)
        
        if risky_steps:
            # Create ONE approval request for ALL steps
            step_names = [f"{s.get('tool')}.{s.get('action')}" for s in steps]
            desc = f"Run {len(steps)} steps: {', '.join(step_names[:3])}" + ("..." if len(step_names)>3 else "")
            
            approval = crud.create_approval_request(user_id, desc, {"steps": steps})
            
            # Send APPROVAL BUTTONS
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve:{approval['id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject:{approval['id']}")
                ]
            ]
            
            # Format detailed message
            details = "\n".join([f"• `{s.get('tool')}`: {s.get('action')} params: `{str(s.get('params'))[:40]}`" for s in steps])
            
            await update.message.reply_text(
                f"🛡️ **APPROVAL REQUEST**\n\n{desc}\n\nPlan Details:\n{details}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return {
                "success": True,
                "needs_approval": True,
                "pending_approvals": [{"approval_id": approval["id"], "description": desc}]
            }

    # 2. EXECUTE STEPS (Approved / Safe)
    for step in steps:
        tool_name = step.get("tool")
        action = step.get("action")
        params = step.get("params", {})
        
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            results.append({"error": f"Tool '{tool_name}' not found"})
            continue
        
        try:
            # Execute
            result = tool.execute(action, params, user_id, None)
            results.append({"tool": tool_name, "result": result})
            
            # RECURSIVE EXECUTION for Approval Tool
            if result.get("success") and result.get("approved_payload"):
                payload = result.get("approved_payload")
                sub_steps = payload.get("steps") or [payload]
                await execute_plan_with_photos({"steps": sub_steps}, user_id, update, bypass_risk=True)

            # Send photo/file
            if result.get("send_photo") and result.get("path"):
                await send_photo(update, result["path"])
            if result.get("send_file") and result.get("path"):
                await send_document(update, result["path"])
                
        except Exception as e:
            logger.error(f"Tool error: {e}")
            results.append({"error": str(e)})
            break
    
    return {
        "success": not any("error" in r for r in results),
        "results": results,
        "pending_approvals": [],
        "needs_approval": False
    }

async def send_photo(update: Update, photo_path: str):
    """Send a photo to the user."""
    try:
        if os.path.exists(photo_path):
            # Check if it's an image
            ext = os.path.splitext(photo_path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                with open(photo_path, "rb") as photo:
                    await update.message.reply_photo(photo=photo, caption=f"📸 {os.path.basename(photo_path)}")
                logger.info(f"Sent photo: {photo_path}")
            else:
                # Send as document for non-image files
                await send_document(update, photo_path)
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")

async def send_document(update: Update, file_path: str):
    """Send any file to the user."""
    try:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            size_mb = size / (1024 * 1024)
            
            with open(file_path, "rb") as doc:
                await update.message.reply_document(
                    document=doc, 
                    filename=os.path.basename(file_path),
                    caption=f"📁 {os.path.basename(file_path)} ({size_mb:.1f} MB)"
                )
            logger.info(f"Sent document: {file_path}")
    except Exception as e:
        logger.error(f"Failed to send document: {e}")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries (buttons)."""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        if ":" not in data:
            return
            
        action, value = data.split(":", 1)
        user_id = int(query.from_user.id)
        
        if action == "approve":
            approval_id = int(value)
            
            # Execute approval (Update DB only)
            result = approval_tool.execute("approve", {"approval_id": approval_id}, user_id, None)
            
            if result.get("success"):
                await query.message.edit_reply_markup(reply_markup=None) # Remove buttons
                await query.message.reply_text(f"✅ Approved! Executing plan...")
                
                # Execute payload
                payload = result.get("approved_payload", {})
                # Support legacy single step format by wrapping in list
                steps = payload.get("steps") 
                if not steps:
                     # Old format: payload IS the step
                     steps = [payload]
                
                # Run plan (bypass risk check because it is approved)
                # We construct a plan dict
                await execute_plan_with_photos({"steps": steps}, user_id, update, bypass_risk=True)
            else:
                 await query.message.reply_text(f"⚠️ Failed: {result.get('error')}")
                 
        elif action == "reject":
            approval_id = int(value)
            crud.update_approval_status(approval_id, "rejected")
            await query.message.edit_text(f"❌ Request #{approval_id} rejected.")

    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        await query.message.reply_text(f"Error: {e}")

def setup_handlers(app: Application):
    """Setup all handlers."""
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
