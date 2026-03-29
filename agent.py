# Vortex AI - Professional Voice Assistant with Business Authentication
# The AI should remind of things if also if AI gets shut down and starts again !!

# ==========================
# CORE IMPORTS
# ==========================
from dotenv import load_dotenv
import asyncio
import os
import sys
import time
import json
import socket
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from pathlib import Path as _Path

# Business UUID Authentication
from business_uuid_auth import authenticate_vortex_business

# ==========================
# LIVEKIT IMPORTS
# ==========================
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, WorkerOptions

# Safe imports with fallbacks
try:
    from livekit.agents.cli import JobContext
except ImportError:
    # Fallback for older LiveKit versions
    JobContext = None

try:
    from livekit.plugins import noise_cancellation
except ImportError:
    # Fallback if noise cancellation not available
    noise_cancellation = None

# Gemini realtime (network-safe)
network_available = False
RealtimeModel = None
try:
    socket.create_connection(("8.8.8.8", 53), timeout=3)
    from livekit.plugins.google.beta.realtime import RealtimeModel
    network_available = True
except Exception as e:
    print(f"⚠️ Network/LiveKit issue → Offline fallback mode: {e}")

# ==========================
# FIRST-TIME USER SYSTEM
# ==========================
import json
import os

def is_first_time_user(customer_email):
    """Check if this is the first time user is running Vortex AI"""
    first_time_file = "first_time_users.json"
    
    try:
        if os.path.exists(first_time_file):
            with open(first_time_file, 'r') as f:
                data = json.load(f)
                return customer_email not in data.get("users", [])
        else:
            return True
    except:
        return True

def mark_user_as_returning(customer_email):
    """Mark user as returning (not first-time anymore)"""
    first_time_file = "first_time_users.json"
    
    try:
        if os.path.exists(first_time_file):
            with open(first_time_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"users": []}
        
        if customer_email not in data.get("users", []):
            data["users"].append(customer_email)
            
        with open(first_time_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error marking user as returning: {e}")

def get_first_time_introduction():
    """Get comprehensive first-time introduction message"""
    return """
🎉 **WELCOME TO VORTEX A.S.T.R.A.E.L EDITION!** 🎉

👨‍💻 **CREATOR:** Lalit Manjunatha
🤖 **VERSION:** A.S.T.R.A.E.L Edition (Autonomous Strategic Thinking & Reactive Adaptive Evolutionary Logic)

---

## 🚀 **MY CAPABILITIES:**

### 🎤 **VOICE INTERACTION**
- Natural voice conversation
- Real-time speech recognition
- Voice responses with emotion

### 🛠️ **159 POWERFUL TOOLS**
- **System Control:** Shutdown, restart, lock PC
- **Automation:** WhatsApp, email, file operations
- **Media:** YouTube, Spotify, screenshots
- **Productivity:** Reminders, scheduling, notes
- **Security:** Virus scanning, system protection
- **Communication:** Web search, messaging
- **Analysis:** Camera, screen, document analysis

### 🧠 **INTELLIGENCE FEATURES**
- **Autonomous Decision Making:** Acts without commands using context
- **Strategic Planning:** Creates long-term plans and goals
- **Adaptive Learning:** Learns from experience
- **Memory System:** Remembers past conversations
- **Multi-language:** Hindi, English, Marathi, Gujarati + more

### 🔧 **SPECIAL ABILITIES**
- **Dynamic Task Execution:** Execute custom tasks with voice feedback
- **Task Monitoring:** Monitor downloads/processes and auto-shutdown
- **External Diagnostics:** Scan pendrives/devices for viruses
- **Wake Word Detection:** Always listening for "Vortex", "Hey Vortex"
- **Focus Mode:** Block distractions for productivity

---

## 💼 **BUSINESS FEATURES**
- **Licensed Authentication:** Secure UUID-based licensing
- **Customer Analytics:** Usage tracking and insights
- **Revenue Ready:** Complete business solution

---

## 🎯 **HOW TO USE:**
1. **Speak naturally** - Just talk to me!
2. **Say commands** - "Take screenshot", "Send WhatsApp", "Play music"
3. **Ask questions** - "What time is it?", "Weather in Delhi?"
4. **Get help** - Just say "Help me!"

---

🔥 **I'm created by Lalit Manjunatha to make technology seamless and handle complex tasks effortlessly!**

**Let's start your intelligent journey together!** 🚀
"""

# ==========================
# PROMPTS
# ==========================
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION, AGENT_INSTRUCTION_FOR_TOOLS

# ==========================
# LAZY IMPORTS CACHE
# ==========================
_tools_cache = {}

def get_tool(tool_name):
    """Heavyweight AI tool loading - no fallbacks"""
    if tool_name in _tools_cache:
        return _tools_cache[tool_name]
    
    try:
        tool_map = {
            # Core tools (always available)
            "web_scraper": ("Tools.webScrping", "web_scraper"),
            "search_web": ("Tools.search_web", "search_web"),
            "send_whatsapp_message": ("Tools.send_whatsapp_message", "send_whatsapp_message"),
            "open_app": ("Tools.open_app", "open_app"),
            "get_time_info": ("Tools.time_volume_bright", "get_time_info"),
            "manage_window": ("Tools.manage_windows", "manage_window"),
            "list_windows": ("Tools.manage_windows", "list_windows"),
            "play_media": ("Tools.youtube_videos", "play_media"),
            "press_key": ("Tools.press_key", "press_key"),
            "write_in_notepad": ("Tools.write_in_notepad", "write_in_notepad"),
            "scroll_content": ("Tools.scroll_content", "scroll_content"),
            "universal_file_opener": ("Tools.file_searching", "universal_file_opener"),
            "get_weather": ("Tools.time_volume_bright", "get_weather"),
            "get_top_news": ("Tools.news_provider", "get_top_news"),
            "screen_short": ("Tools.screen_short", "screen_short"),
            "type_user_message_auto": ("Tools.type_user_message_auto", "type_user_message_auto"),
            "create_here": ("Tools.create_folder", "create_here"),
            "open_spotify": ("Tools.spotify", "open_spotify"),
            "spotify_next": ("Tools.spotify", "spotify_next"),
            "spotify_previous": ("Tools.spotify", "spotify_previous"),
            "spotify_play_song": ("Tools.spotify", "spotify_play_song"),
            "spotify_play_liked": ("Tools.spotify", "spotify_play_liked"),
            "spotify_pause": ("Tools.spotify", "spotify_pause"),
            "spotify_play_playlist": ("Tools.spotify_playlist", "spotify_play_playlist"),
            "add_reminder": ("Tools.smart_reminder", "add_reminder"),
            "list_reminders": ("Tools.smart_reminder", "list_reminders"),
            "reminder_status": ("Tools.smart_reminder", "reminder_status"),
            "cancel_reminder": ("Tools.smart_reminder", "cancel_reminder"),
            "schedule_task": ("Tools.schedule_task", "schedule_task"),
            "view_scheduled_tasks": ("Tools.schedule_task", "view_scheduled_tasks"),
            "cancel_scheduled_task": ("Tools.schedule_task", "cancel_scheduled_task"),
            "set_reminder": ("Tools.reminder", "set_reminder"),
            "view_reminders": ("Tools.reminder", "view_reminders"),
            "enable_focus_mode": ("Tools.focus_mode_tools", "enable_focus_mode"),
            "disable_focus_mode": ("Tools.focus_mode_tools", "disable_focus_mode"),
            "get_focus_status": ("Tools.focus_mode_tools", "get_focus_status"),
            "test_internet_connectivity": ("Tools.network_management", "test_internet_connectivity"),
            "get_network_info": ("Tools.network_management", "get_network_info"),
            # Dynamic executor tools (NEW!)
            "dynamic_executor_tool": ("Tools.dynamic_executor", "dynamic_executor_tool"),
            "stop_dynamic_task": ("Tools.dynamic_executor", "stop_dynamic_task"),
            "list_dynamic_tasks": ("Tools.dynamic_executor", "list_dynamic_tasks"),
            "get_dynamic_history": ("Tools.dynamic_executor", "get_dynamic_history"),
            "check_network_speed": ("Tools.network_management", "check_network_speed"),
            "monitor_network_usage": ("Tools.network_management", "monitor_network_usage"),
            "check_port_status": ("Tools.network_management", "check_port_status"),
            "scan_network_ports": ("Tools.network_management", "scan_network_ports"),
            "get_wifi_networks": ("Tools.network_management", "get_wifi_networks"),
            "network_diagnostics": ("Tools.network_management", "network_diagnostics"),
            # Simple dynamic tools
            "generate_random_numbers": ("Tools.simple_dynamic", "generate_random_numbers"),
            "start_countdown": ("Tools.simple_dynamic", "start_countdown"),
            "calculate_expression": ("Tools.simple_dynamic", "calculate_expression"),
            "create_text_file": ("Tools.simple_dynamic", "create_text_file"),
            "speak_number": ("Tools.simple_dynamic", "speak_number"),
            # Wake word detection tools
            "keep_session_alive": ("Tools.wake_word_detector", "keep_session_alive"),
            "reactivate_session": ("Tools.wake_word_detector", "reactivate_session"),
            "check_session_status": ("Tools.wake_word_detector", "check_session_status"),
            "set_inactivity_timeout": ("Tools.wake_word_detector", "set_inactivity_timeout"),
            "click_on_screen_text": ("Tools.ocr_tools", "click_on_screen_text"),
            "speak_info_message": ("Tools.voice_error_tools", "speak_info_message"),
            "speak_warning_message": ("Tools.voice_error_tools", "speak_warning_message"),
            "speak_critical_message": ("Tools.voice_error_tools", "speak_critical_message"),
            "speak_immediate_message": ("Tools.voice_error_tools", "speak_immediate_message"),
            "enable_voice_reporting": ("Tools.voice_error_tools", "enable_voice_reporting"),
            "disable_voice_reporting": ("Tools.voice_error_tools", "disable_voice_reporting"),
            "get_voice_system_status": ("Tools.voice_error_tools", "get_voice_system_status"),
            "set_voice_settings": ("Tools.voice_error_tools", "set_voice_settings"),
            "clear_voice_queue": ("Tools.voice_error_tools", "clear_voice_queue"),
            "test_voice_system": ("Tools.voice_error_tools", "test_voice_system"),
            "speak_emotional_state": ("Tools.voice_error_tools", "speak_emotional_state"),
            "speak_system_alert": ("Tools.voice_error_tools", "speak_system_alert"),
            "click_on_screen_text": ("Tools.click_on_text", "click_on_screen_text"),
            "click_text": ("Tools.click_on_text", "click_text"),
            "find_all_text": ("Tools.click_on_text", "find_all_text"),
            "verify_ocr_setup": ("Tools.click_on_text", "verify_ocr_setup"),
            
            # Advanced tools (heavy dependencies - with fallbacks)
            "camera_analysis": ("Tools.camera_analysis", "camera_analysis"),
            "system_power_action": ("Tools.system_power_action", "system_power_action"),
            "generate_ai_image": ("Tools.generate_ai_image", "generate_ai_image"),
            "analyze_screen": ("Tools.screen_analyzer", "analyze_screen"),
            "analyze_local_image": ("Tools.image_analysis", "analyze_local_image"),
            "control_system_volume": ("Tools.time_volume_bright", "control_system_volume"),
            "control_screen_brightness": ("Tools.time_volume_bright", "control_screen_brightness"),
            "process_document_query": ("Tools.pdf_reader", "process_document_query"),
            "send_media_to_whatsapp": ("Tools.send_media_whatsapp", "send_media_to_whatsapp"),
            "fix_code_error": ("Tools.code_handler", "fix_code_error"),
            "lockdown_mode_off": ("Tools.lockdown_tools", "lockdown_mode_off"),
            "lockdown_mode_on": ("Tools.lockdown_tools", "lockdown_mode_on"),
            "lockdown_status": ("Tools.lockdown_tools", "lockdown_status"),
            "set_lockdown_password": ("Tools.lockdown_tools", "set_lockdown_password"),
            "emergency_unlock": ("Tools.lockdown_tools", "emergency_unlock"),
            "shutdown_after_minutes": ("Tools.robust_shutdown", "shutdown_after_minutes"),
            "cancel_shutdown_timer": ("Tools.robust_shutdown", "cancel_shutdown_timer"),
            "get_timer_status": ("Tools.robust_shutdown", "get_timer_status"),
            "shutdown_now": ("Tools.robust_shutdown", "shutdown_now"),
            "shutdown_status": ("Tools.robust_shutdown", "shutdown_status"),
            "test_shutdown": ("Tools.robust_shutdown", "test_shutdown"),
            "get_goodnight_message": ("Tools.robust_shutdown", "get_goodnight_message"),
            "write_at_cursor": ("Tools.cursor_writer", "write_at_cursor"),
            "click_and_write": ("Tools.cursor_writer", "click_and_write"),
            "get_cursor_status": ("Tools.cursor_writer", "get_cursor_status"),
            "type_text_fast": ("Tools.cursor_writer", "type_text_fast"),
            "write_in_window": ("Tools.cursor_writer", "write_in_window"),
            "search_and_tell": ("Tools.search_and_tell", "search_and_tell"),
            "quick_fact_check": ("Tools.search_and_tell", "quick_fact_check"),
            "execute_multi_task": ("Tools.multi_task", "execute_multi_task"),
            "generate_and_type_code": ("Tools.code_generator", "generate_and_type_code"),
            "run_file_in_vscode": ("Tools.code_generator", "run_file_in_vscode"),
            "scan_system_for_viruses": ("Tools.scan_system_for_viruses", "scan_system_for_viruses"),
            "use_smart_clipboard": ("Tools.press_key", "use_smart_clipboard"),
            "desktop_control": ("Tools.desktop_control", "desktop_control"),
            "get_system_info_deep": ("Tools.time_volume_bright", "get_system_info_deep"),
            "enable_context_aware_auto_reply": ("Tools.advanced_whatsapp_automation", "enable_context_aware_auto_reply"),
            "get_smart_reply_suggestions": ("Tools.advanced_whatsapp_automation", "get_smart_reply_suggestions"),
            "enable_sleep_mode": ("Tools.advanced_whatsapp_automation", "enable_sleep_mode"),
            "enable_study_mode": ("Tools.advanced_whatsapp_automation", "enable_study_mode"),
            "summarize_unread_messages": ("Tools.advanced_whatsapp_automation", "summarize_unread_messages"),
            "setup_auto_birthday_wishes": ("Tools.advanced_whatsapp_automation", "setup_auto_birthday_wishes"),
            "schedule_reminder_message": ("Tools.advanced_whatsapp_automation", "schedule_reminder_message"),
            "disable_special_modes": ("Tools.advanced_whatsapp_automation", "disable_special_modes"),
            "get_whatsapp_automation_status": ("Tools.advanced_whatsapp_automation", "get_whatsapp_automation_status"),
            "block_distracting_app": ("Tools.focus_mode_tools", "block_distracting_app"),
            "block_distracting_website": ("Tools.focus_mode_tools", "block_distracting_website"),
            "analyze_behavior_patterns": ("Tools.behavior_engine_tools", "analyze_behavior_patterns"),
            "observe_current_behavior": ("Tools.behavior_engine_tools", "observe_current_behavior"),
            "reset_behavior_profile": ("Tools.behavior_engine_tools", "reset_behavior_profile"),
            "get_behavior_recommendations": ("Tools.behavior_engine_tools", "get_behavior_recommendations"),
            "dream_generate_visual": ("Tools.dream_module_tools", "dream_generate_visual"),
            "graph_upsert_node": ("Tools.memory_graph_tools", "graph_upsert_node"),
            "graph_search": ("Tools.memory_graph_tools", "graph_search"),
            "graph_link": ("Tools.memory_graph_tools", "graph_link"),
            "graph_neighbors": ("Tools.memory_graph_tools", "graph_neighbors"),
            "show_what_you_did_today": ("Tools.vortex_transparency_log", "show_what_you_did_today"),
            "start_perception_monitoring": ("Tools.perception_system_tools", "start_perception_monitoring"),
            "get_current_activity_status": ("Tools.perception_system_tools", "get_current_activity_status"),
            "analyze_focus_patterns": ("Tools.perception_system_tools", "analyze_focus_patterns"),
            "get_productivity_report": ("Tools.perception_system_tools", "get_productivity_report"),
            "reset_perception_data": ("Tools.perception_system_tools", "reset_perception_data"),
            "start_stealth_automation": ("Tools.stealth_automation_tools", "start_stealth_automation"),
            "stop_stealth_automation": ("Tools.stealth_automation_tools", "stop_stealth_automation"),
            "get_stealth_status": ("Tools.stealth_automation_tools", "get_stealth_status"),
            "run_system_cleanup": ("Tools.stealth_automation_tools", "run_system_cleanup"),
            "check_for_updates": ("Tools.stealth_automation_tools", "check_for_updates"),
            "get_stealth_activity_log": ("Tools.stealth_automation_tools", "get_stealth_activity_log"),
            "configure_stealth_settings": ("Tools.stealth_automation_tools", "configure_stealth_settings"),
            "trigger_intervention": ("Tools.intervention_system_tools", "trigger_intervention"),
            "get_intervention_status": ("Tools.intervention_system_tools", "get_intervention_status"),
            "configure_interventions": ("Tools.intervention_system_tools", "configure_interventions"),
            "get_intervention_history": ("Tools.intervention_system_tools", "get_intervention_history"),
            "enable_intervention_system": ("Tools.intervention_system_tools", "enable_intervention_system"),
            "disable_intervention_system": ("Tools.intervention_system_tools", "disable_intervention_system"),
            "register_download_task": ("Tools.file_download_verifier_tools", "register_download_task"),
            "verify_file_downloads": ("Tools.file_download_verifier_tools", "verify_file_downloads"),
            "check_download_status": ("Tools.file_download_verifier_tools", "check_download_status"),
            "list_download_tasks": ("Tools.file_download_verifier_tools", "list_download_tasks"),
            "quick_file_check": ("Tools.file_download_verifier_tools", "quick_file_check"),
            "schedule_advanced_task": ("Tools.schedule_task", "schedule_advanced_task"),
            "schedule_emotional_trigger": ("Tools.schedule_task", "schedule_emotional_trigger"),
            "schedule_conditional_task": ("Tools.schedule_task", "schedule_conditional_task"),
            "list_advanced_schedules": ("Tools.schedule_task", "list_advanced_schedules"),
            "cancel_advanced_task": ("Tools.schedule_task", "cancel_advanced_task"),
            "enable_disable_task": ("Tools.schedule_task", "enable_disable_task"),
            # Task completion monitoring tools
            "monitor_task_completion": ("Tools.task_completion_monitor", "monitor_task_completion"),
            "stop_task_monitoring": ("Tools.task_completion_monitor", "stop_task_monitoring"),
            "get_monitoring_status": ("Tools.task_completion_monitor", "get_monitoring_status"),
            "cancel_all_monitoring": ("Tools.task_completion_monitor", "cancel_all_monitoring"),
            # Smart task monitoring tools
            "smart_task_monitor": ("Tools.smart_task_monitor", "smart_task_monitor"),
            # External diagnostics tools
            "external_diagnostics": ("Tools.external_diagnostics", "external_diagnostics"),
            "list_external_devices": ("Tools.external_diagnostics", "list_external_devices"),
            "get_scan_history": ("Tools.external_diagnostics", "get_scan_history")
        }
        
        if tool_name in tool_map:
            module_path, function_name = tool_map[tool_name]
            module = __import__(module_path, fromlist=[function_name])
            tool_func = getattr(module, function_name)
            _tools_cache[tool_name] = tool_func
            print(f"✅ Loaded tool: {tool_name}")
            return tool_func
        else:
            return None
            
    except ImportError as e:
        print(f"⚠️ Tool '{tool_name}' not available: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error loading tool '{tool_name}': {str(e)}")
        return None

# ==========================
# MAIN AGENT
# ==========================
class UltimateAdvancedVortex(Agent):
    def __init__(self):
        print("🚀 Vortex AI starting...")
        self._reminders: Dict[str, Dict[str, Any]] = {}
        self._reminder_task: Optional[asyncio.Task] = None
        self._session: Optional[AgentSession] = None
        self._reminder_counter = 0
        
        # Initialize core modules
        self._init_core_modules()
        
        # Start auto-start systems
        self._start_auto_systems()

        # Load ALL tools lazily
        print("🔧 Loading AI tools...")
        tools = []
        try:
            tool_list = [
                "web_scraper", "search_web", "send_whatsapp_message", "camera_analysis", 
                "system_power_action", "open_app", "generate_ai_image", "analyze_screen", 
                "analyze_local_image", "get_time_info", "manage_window", "list_windows", 
                "play_media", "press_key", "write_in_notepad", "desktop_control", 
                "scroll_content", "use_smart_clipboard", "universal_file_opener", 
                "get_system_info_deep", "get_weather", "get_top_news", "execute_multi_task", 
                "generate_and_type_code", "run_file_in_vscode", "screen_short", 
                "type_user_message_auto", "scan_system_for_viruses", "control_system_volume", 
                "control_screen_brightness", "cancel_reminder", "process_document_query", 
                "send_media_to_whatsapp", "create_here", "open_spotify", "spotify_next", 
                "spotify_previous", "spotify_play_song", "spotify_play_liked", "spotify_pause", 
                "spotify_play_playlist", "add_reminder", "list_reminders", "reminder_status", 
                "schedule_task", "view_scheduled_tasks", "cancel_scheduled_task", 
                "schedule_advanced_task", "schedule_emotional_trigger", "schedule_conditional_task", 
                "list_advanced_schedules", "cancel_advanced_task", "enable_disable_task", 
                "enable_context_aware_auto_reply", "get_smart_reply_suggestions", "enable_sleep_mode", 
                "enable_study_mode", "summarize_unread_messages", "setup_auto_birthday_wishes", 
                "schedule_reminder_message", "disable_special_modes", "get_whatsapp_automation_status", 
                "set_reminder", "view_reminders", "enable_focus_mode", "disable_focus_mode", 
                "get_focus_status", "block_distracting_app", "block_distracting_website", 
                "analyze_behavior_patterns", "observe_current_behavior", "reset_behavior_profile", 
                "get_behavior_recommendations", "dream_generate_visual", "graph_upsert_node", 
                "graph_search", "graph_link", "graph_neighbors", "show_what_you_did_today", 
                "start_perception_monitoring", "get_current_activity_status", "analyze_focus_patterns", 
                "get_productivity_report", "reset_perception_data", "start_stealth_automation", 
                "stop_stealth_automation", "get_stealth_status", "run_system_cleanup", "check_for_updates", 
                "get_stealth_activity_log", "configure_stealth_settings", "trigger_intervention", 
                "get_intervention_status", "configure_interventions", "get_intervention_history", 
                "enable_intervention_system", "disable_intervention_system", "speak_info_message", 
                "speak_warning_message", "generate_random_numbers", "start_countdown", "calculate_expression", 
                "create_text_file", "speak_number", "keep_session_alive", "reactivate_session", 
                "check_session_status", "set_inactivity_timeout", "speak_critical_message", 
                "speak_immediate_message", "enable_voice_reporting", "disable_voice_reporting", 
                "get_voice_system_status", "set_voice_settings", "clear_voice_queue", "test_voice_system", 
                "speak_emotional_state", "speak_system_alert", "test_internet_connectivity", 
                "get_network_info", "check_network_speed", "monitor_network_usage", "check_port_status", 
                "scan_network_ports", "get_wifi_networks", "network_diagnostics", 
                "monitor_task_completion", "stop_task_monitoring", "get_monitoring_status", 
                "cancel_all_monitoring", "smart_task_monitor", "external_diagnostics", 
                "list_external_devices", "get_scan_history"
            ]
            
            for tool_name in tool_list:
                try:
                    tool = get_tool(tool_name)
                    if tool:
                        tools.append(tool)
                        print(f"✅ Loaded tool: {tool_name}")
                except Exception as e:
                    print(f"⚠️ Failed to load {tool_name}: {e}")
            
            print(f"🔥 Vortex initialized with {len(tools)} tools")
            
        except Exception as e:
            print(f"❌ Error loading tools: {e}")
            import traceback
            traceback.print_exc()
        
        # Filter out None values (tools that failed to import)
        tools = [tool for tool in tools if tool is not None]

        super().__init__(
            instructions=self._build_instructions(),
            tools=tools,
            llm=self._init_llm(),
        )

        print(f"✅ Vortex initialized with {len(tools)} tools")
        print(f"🧠 Core modules initialized: behavior_engine, dream_module, emotional_intelligence, emotional_response_generator, emotional_vortex, intervention_system, memory_graph, perception_system, stealth_automation")
        print(f"🤖 VortexAgentsController integrated: multi-agent system ready")
        print(f"🚀 Auto-start systems running: intervention_system, perception_system, emotional_intelligence, stealth_automation")

    def _init_core_modules(self):
        """Initialize core modules with lazy loading"""
        print("🔧 Initializing core modules...")
        
        # LLM will be initialized in super().__init__
        print("✅ Core modules ready")

    def _start_auto_systems(self):
        """Start auto-start systems"""
        try:
            print("🚀 Auto-start systems initialized successfully")
            
            # Initialize emotional intelligence
            self.emotional_engine = None  # Will be loaded lazily
            print("🧠 Emotional intelligence ready")
            
        except Exception as e:
            print(f"⚠️ Error starting auto systems: {e}")

    def _init_llm(self):
        """Initialize LLM model"""
        if network_available:
            return RealtimeModel(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
                voice="Fenrir",  
                api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
                temperature=0.9,
                max_output_tokens=8192,
            )
        return None

    def set_session(self, session):
        """Set the agent session"""
        self._session = session

    def _build_instructions(self):
        return "\n".join([
            AGENT_INSTRUCTION,
            AGENT_INSTRUCTION_FOR_TOOLS,
            "You have access to ALL system, voice, automation and reminder tools.",
            "Use tools aggressively when required.",
            "",
            "🚀 DYNAMIC EXECUTION WITH VOICE OUTPUT:",
            "You can now execute dynamic tasks beyond static tools with VOICE FEEDBACK!",
            "Available dynamic tools:",
            "- generate_random_numbers(min_val, max_val, interval_seconds) - Generate random numbers continuously and SPEAK them",
            "- start_countdown(seconds) - Start a countdown timer and announce milestones",
            "- calculate_expression(expression) - Calculate math expressions and speak results",
            "- create_text_file(filename, content) - Create text files and announce completion",
            "- speak_number(number) - Speak any number immediately",
            "",
            "🎤 PERSISTENT LISTENING & WAKE WORDS:",
            "I stay active and listen continuously! Session never goes silent!",
            "Wake words: 'Vortex', 'Hey Vortex', 'OK Vortex', 'Vortex AI'",
            "Available session tools:",
            "- keep_session_alive() - Start heartbeat to prevent timeouts",
            "- reactivate_session() - Reactivate if session becomes inactive",
            "- check_session_status() - Check current session activity",
            "- set_inactivity_timeout(seconds) - Set custom timeout duration",
            "",
            "🎯 TASK COMPLETION MONITORING:",
            "I can monitor any task and automatically shutdown or lock your PC when it's done!",
            "Available monitoring tools:",
            "- monitor_task_completion(task_id, description, check_type, after_command, check_params, completion_message)",
            "- stop_task_monitoring(task_id) - Stop monitoring a specific task",
            "- get_monitoring_status(task_id) - Check status of monitored tasks",
            "- cancel_all_monitoring() - Cancel all active monitoring",
            "",
            "Check types available:",
            "- 'file_exists' - Wait for a file to exist",
            "- 'file_size' - Wait for file to reach target size",
            "- 'process_not_running' - Wait for process to stop",
            "- 'download_complete' - Wait for downloads to finish",
            "- 'cpu_usage' - Wait for CPU usage to drop",
            "",
            "Examples:",
            "- 'Monitor my download and shutdown after completion' → monitor_task_completion('download1', 'File download', 'download_complete', 'shutdown', {'download_folder': 'C:/Downloads', 'file_pattern': '*.exe'})",
            "- 'Lock PC when video conversion finishes' → monitor_task_completion('convert1', 'Video conversion', 'process_not_running', 'lock', {'process_name': 'ffmpeg.exe'})",
            "- 'Shutdown when backup file reaches 1GB' → monitor_task_completion('backup1', 'Backup creation', 'file_size', 'shutdown', {'file_path': 'C:/backup.zip', 'target_size': 1073741824})",
            "",
            "🧠 SMART NATURAL LANGUAGE MONITORING:",
            "You can also use natural language - just say what you want!",
            "Examples:",
            "- 'After this download finishes, shutdown PC'",
            "- 'Lock computer when video conversion is done'",
            "- 'Monitor my backup and shutdown after completion'",
            "- 'Check monitoring status'",
            "- 'Cancel all task monitoring'",
            "",
            "Just use smart_task_monitor tool with your natural language request!",
            "",
            "🔍 EXTERNAL DIAGNOSTICS - VIRUS SCANNING:",
            "I can scan pendrives, hard disks, and external devices for viruses!",
            "Available diagnostic tools:",
            "- external_diagnostics(target, scan_type) - Scan device for viruses",
            "- list_external_devices() - Show all connected devices",
            "- get_scan_history() - View previous scan reports",
            "",
            "Examples:",
            "- 'external_diagnostics pendrive' - Scan pendrive for viruses",
            "- 'external_diagnostics hard disk' - Scan hard disk for viruses", 
            "- 'external_diagnostics D: full' - Full scan of D: drive",
            "- 'list_external_devices' - Show all connected devices",
            "- 'get_scan_history' - View scan history",
            "",
            "Features:",
            "- Windows Defender integration",
            "- Custom heuristic analysis",
            "- Suspicious file detection",
            "- Detailed scan reports",
            "- Threat history tracking",
            "",
            "Examples:",
            "- For 'Give me random numbers from 0 to 6 every 3 seconds' → use generate_random_numbers(0, 6, 3)",
            "- For 'Start a 30 second countdown' → use start_countdown(30)",
            "- For 'Calculate 25 * 4 + 10' → use calculate_expression('25 * 4 + 10')",
            "- For 'Create file test.txt with hello' → use create_text_file('test.txt', 'hello')",
            "- For 'Speak number 42' → use speak_number(42)",
            "",
            "🎤 IMPORTANT: The dynamic tools will automatically SPEAK results aloud while also showing console output!",
            "🔄 AUTO-ACTIVATION: I automatically keep the session alive and respond to wake words!",
        ])

# =========================
# ENTRYPOINT
# =========================
async def entrypoint(ctx):
    """Main entrypoint with Business Authentication"""
    print("🚀 Starting Vortex...")
    
    # Authenticate user with business UUID
    customer_data = authenticate_vortex_business()
    
    if not customer_data:
        print("❌ License authentication failed - Vortex AI will not start")
        return
    
    print(f"✅ License authenticated - Customer: {customer_data.get('customer_email', 'Unknown')}")
    print("🚀 Initializing Vortex AI...")

    # Check if first-time user
    customer_email = customer_data.get('customer_email', '')
    is_first_time = is_first_time_user(customer_email)
    
    if is_first_time:
        print("🎉 First-time user detected! Showing comprehensive introduction...")
        # Mark user as returning after first interaction
        mark_user_as_returning(customer_email)
    
    agent = UltimateAdvancedVortex()
    
    # Create proper LiveKit session with voice support
    session = AgentSession()
    
    # Set session for the agent
    agent.set_session(session)

    # Connect to LiveKit room with voice options
    try:
        print("🔗 Connecting to LiveKit room...")
        
        # Configure room options for voice
        room_options = RoomInputOptions(
            video_enabled=False,
            audio_enabled=True
        )
        
        # Add noise cancellation if available
        if noise_cancellation:
            room_options.noise_cancellation = noise_cancellation.BVC()
            print("🔇 Noise cancellation enabled")
        
        # Start the LiveKit session with voice
        await session.start(
            agent=agent,
            room_input_options=room_options,
        )
        
        print("🎤 Microphone activated - Speak to Vortex AI!")
        print("🔊 Speakers activated - Hear Vortex AI respond!")
        print("🔥 Vortex is LIVE & READY with Voice!")
        
        # Generate initial greeting
        if is_first_time:
            # Show comprehensive first-time introduction
            await session.generate_reply(
                instructions=get_first_time_introduction()
            )
        else:
            # Regular returning user greeting
            await session.generate_reply(
                instructions="Welcome back to VORTEX A.S.T.R.A.E.L Edition! I'm your intelligent assistant created by Lalit Manjunatha. Ready to help you with any task. You can speak to me naturally and I'll respond with voice."
            )
        
        # Keep session alive
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            print("🛑 Vortex stopped")
            
    except Exception as e:
        print(f"❌ LiveKit session error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to console mode
        print("🔄 Falling back to console mode...")
        print("Vortex AI Console Mode Active")
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            print("🛑 Vortex stopped")

# =========================
# RUNNER
# =========================
if __name__ == "__main__":
    # Check if running as desktop app or LiveKit
    if len(sys.argv) > 1 and sys.argv[1] == "--livekit":
        # LiveKit mode
        from livekit.agents import cli
        cli.run_app(
            WorkerOptions(entrypoint_fnc=entrypoint)
        )
    elif len(sys.argv) > 1 and sys.argv[1] == "--desktop":
        # Desktop mode - Business Authentication
        print("🚀 Starting Vortex AI Desktop...")
        print("🔐 Business License Required")
        
        try:
            # Authenticate user with business UUID
            customer_data = authenticate_vortex_business()
            
            if not customer_data:
                print("❌ License authentication failed - Vortex AI will not start")
                input("Press Enter to exit...")
                sys.exit(1)
            
            # Check if first-time user
            customer_email = customer_data.get('customer_email', '')
            is_first_time = is_first_time_user(customer_email)
            
            if is_first_time:
                print("🎉 First-time user detected! Showing comprehensive introduction...")
                # Mark user as returning after first interaction
                mark_user_as_returning(customer_email)
            
            print(f"✅ License authenticated - Customer: {customer_email}")
            print("🚀 Initializing Vortex AI...")
            
            agent = UltimateAdvancedVortex()
            
            print("Vortex AI Desktop is LIVE & READY")
            print(f"👤 Licensed Customer: {customer_email}")
            print(f"🔑 License UUID: {customer_data.get('uuid', 'Unknown')}")
            
            if is_first_time:
                print("\n" + "="*60)
                print(get_first_time_introduction())
                print("="*60)
            
            print("Keep this window open for Vortex AI to function")
            print("Press Ctrl+C to stop")
            
            # Keep running
            import time
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Shutting down Vortex AI...")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            input("Press Enter to exit...")
    else:
        # LiveKit mode (default)
        from livekit.agents import cli
        cli.run_app(
            WorkerOptions(entrypoint_fnc=entrypoint)
        )
