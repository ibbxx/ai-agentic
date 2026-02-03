"""
Telegram Bot Handlers - With Groq LLM and UI automation.
"""
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.db import crud
from core.parser import parse_message, Intent
from core.agent.planner import make_plan
from core.agent.formatter import format_reply
from core.agent.guardrails import is_high_risk, get_risk_description
from core.agent.tools import task_tool, scheduler_tool, approval_tool
from core.agent.tools import shell_tool, file_tool, app_tool, ui_tool
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
            "🖥️ *UI:* `screenshot`, `click 500 300`\n"
            "🌐 *Browser:* `buka youtube di chrome`\n"
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
        
        # If parser didn't understand, try Groq LLM
        if parsed.intent == Intent.UNKNOWN and settings.GROQ_API_KEY:
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

Jika user meminta melakukan sesuatu di komputer (buka app, screenshot, run command), respond dengan JSON:
{"is_tool_command": true, "steps": [{"tool": "app_tool", "action": "open", "params": {"app": "Chrome"}}]}

Tools yang tersedia:
- app_tool: open, close (params: app, url)
- ui_tool: screenshot, click, type, scroll (params: x, y, text, direction)
- shell_tool: run (params: command)
- task_tool: create, list, close (params: title, task_id)

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

async def execute_plan_with_photos(plan: dict, user_id: int, update: Update) -> dict:
    """Execute plan and send photos if needed."""
    results = []
    pending_approvals = []
    
    steps = plan.get("steps", [])
    
    if not steps:
        return {
            "success": False,
            "error": "no_steps",
            "fallback": plan.get("fallback")
        }
    
    for step in steps[:6]:
        tool_name = step.get("tool")
        action = step.get("action")
        params = step.get("params", {})
        
        # Check high risk
        if is_high_risk(tool_name, action):
            risk_desc = get_risk_description(tool_name, action)
            if tool_name == "app_tool":
                app = params.get("app", "")
                url = params.get("url", "")
                risk_desc += f": {app}"
                if url:
                    risk_desc += f" → {url}"
            
            approval = crud.create_approval_request(user_id, f"{tool_name}.{action}", {
                "tool": tool_name, "action": action, "params": params
            })
            pending_approvals.append({
                "approval_id": approval["id"],
                "description": risk_desc
            })
            continue
        
        # Execute tool
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            results.append({"error": f"Tool '{tool_name}' not found"})
            continue
        
        try:
            result = tool.execute(action, params, user_id, None)
            results.append({"tool": tool_name, "result": result})
            
            # Send photo if screenshot
            if result.get("send_photo") and result.get("path"):
                await send_photo(update, result["path"])
                
        except Exception as e:
            logger.error(f"Tool error: {e}")
            results.append({"error": str(e)})
    
    return {
        "success": len(pending_approvals) == 0 and not any("error" in r for r in results),
        "results": results,
        "pending_approvals": pending_approvals,
        "needs_approval": len(pending_approvals) > 0
    }

async def send_photo(update: Update, photo_path: str):
    """Send a photo to the user."""
    try:
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as photo:
                await update.message.reply_photo(photo=photo, caption="📸 Screenshot")
            logger.info(f"Sent photo: {photo_path}")
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")

def setup_handlers(app: Application):
    """Setup all handlers."""
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
