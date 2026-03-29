"""
MJ Remote AI - File Download Verification Tools
Function tools for checking if all files are downloaded
"""

import asyncio
import os
from livekit.agents import function_tool
from Tools.file_download_verifier import file_verifier
import logging

@function_tool()
async def register_download_task(files: str, source: str = "web") -> str:
    """
    Register a file download task for verification
    
    Examples:
    - "register_download_task 'file1.pdf, file2.jpg, report.docx'"
    - "register_download_task 'image.png, video.mp4' 'youtube'"
    
    Args:
        files: Comma-separated list of expected files
        source: Source of download (web, youtube, drive, etc.)
        
    Returns:
        str: Task registration status
    """
    try:
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        # Parse files list
        file_list = [f.strip() for f in files.split(',') if f.strip()]
        
        logging.info(f"Registering download task: {len(file_list)} files from {source}")
        
        result = file_verifier.register_download_task(task_id, file_list, source)
        
        if "✅" in result:
            return f"{result}\n🆔 Task ID: {task_id}\n📋 Files: {', '.join(file_list)}\n🔍 MJ will verify these files automatically!"
        else:
            return result
            
    except Exception as e:
        logging.error(f"Register download task error: {e}")
        return f"❌ Error registering download task: {str(e)}"

@function_tool()
async def verify_file_downloads(task_id: str) -> str:
    """
    Verify if all files in a download task are completed
    
    Examples:
    - "verify_file_downloads 'abc123'"
    - "verify_file_downloads 'task456'"
    
    Args:
        task_id: ID of the download task to verify
        
    Returns:
        str: Verification results with file status
    """
    try:
        logging.info(f"Verifying download task: {task_id}")
        
        result = await file_verifier.verify_downloads(task_id)
        
        if result['success']:
            total = result['total_files']
            completed = result['completed_files']
            missing = result['missing_files']
            failed = result['failed_files']
            success_rate = result['success_rate']
            
            response = f"📊 File Download Verification Results:\n\n"
            response += f"🆔 Task ID: {task_id}\n"
            response += f"📁 Total Files: {total}\n"
            response += f"✅ Completed: {completed}/{total} ({success_rate:.1f}%)\n"
            response += f"❌ Missing: {len(missing)}\n"
            response += f"⚠️ Failed: {len(failed)}\n\n"
            
            if result['is_complete']:
                response += "🎉 ALL FILES SUCCESSFULLY DOWNLOADED!\n\n"
                response += "✅ Verification: PASSED\n"
                response += "📞 Ready to call you (if auto-call enabled)"
            else:
                response += "⏳ DOWNLOAD INCOMPLETE\n\n"
                
                if missing:
                    response += "📋 Missing Files:\n"
                    for i, file in enumerate(missing, 1):
                        response += f"  {i}. {file['name']}\n"
                
                if failed:
                    response += "\n⚠️ Failed Files:\n"
                    for i, file in enumerate(failed, 1):
                        response += f"  {i}. {file['name']} - {file['error']}\n"
            
            return response
        else:
            return f"❌ Verification failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logging.error(f"Verify file downloads error: {e}")
        return f"❌ Error verifying downloads: {str(e)}"

@function_tool()
async def check_download_status(task_id: str) -> str:
    """
    Check current status of a download verification task
    
    Examples:
    - "check_download_status 'abc123'"
    - "check_download_status 'task456'"
    
    Args:
        task_id: ID of the download task
        
    Returns:
        str: Current task status and file list
    """
    try:
        logging.info(f"Checking download status: {task_id}")
        
        result = file_verifier.get_download_status(task_id)
        
        if result['success']:
            task = result
            response = f"📁 Download Task Status:\n\n"
            response += f"🆔 Task ID: {task_id}\n"
            response += f"📊 Status: {task['status']}\n"
            response += f"📂 Source: {task['source']}\n"
            response += f"📋 Total Files: {task['total_files']}\n"
            response += f"📝 File List:\n"
            
            for i, file in enumerate(task['files'], 1):
                response += f"  {i}. {file}\n"
            
            return response
        else:
            return f"❌ Status check failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logging.error(f"Check download status error: {e}")
        return f"❌ Error checking status: {str(e)}"

@function_tool()
async def list_download_tasks() -> str:
    """
    List all active download verification tasks
    
    Returns:
        str: List of all active download tasks
    """
    try:
        logging.info("Listing download tasks")
        
        tasks = file_verifier.list_active_tasks()
        
        if not tasks:
            return "📂 No active download tasks found.\n💡 Use register_download_task to start tracking files."
        
        response = f"📂 Active Download Tasks:\n\n"
        
        for i, task in enumerate(tasks, 1):
            response += f"{i}. Task ID: {task['task_id']}\n"
            response += f"   📊 Status: {task['status']}\n"
            response += f"   📁 Files: {task['total_files']}\n"
            response += f"   📂 Source: {task['source']}\n\n"
        
        return response
        
    except Exception as e:
        logging.error(f"List download tasks error: {e}")
        return f"❌ Error listing tasks: {str(e)}"

@function_tool()
async def quick_file_check(file_pattern: str) -> str:
    """
    Quick check if specific files exist in common download locations
    
    Examples:
    - "quick_file_check '*.pdf'"
    - "quick_file_check 'report.docx'"
    - "quick_file_check 'image.*'"
    
    Args:
        file_pattern: File name or pattern to search for
        
    Returns:
        str: Search results with file locations
    """
    try:
        import glob
        import re
        
        logging.info(f"Quick file check: {file_pattern}")
        
        # Get search paths
        search_paths = file_verifier._get_search_paths()
        
        found_files = []
        
        for path in search_paths:
            try:
                search_pattern = os.path.join(path, file_pattern)
                matches = glob.glob(search_pattern)
                
                for match in matches:
                    if os.path.isfile(match):
                        found_files.append({
                            'name': os.path.basename(match),
                            'path': match,
                            'size': os.path.getsize(match),
                            'modified': os.path.getmtime(match)
                        })
            except Exception as e:
                logging.warning(f"Search error in {path}: {e}")
        
        if not found_files:
            return f"🔍 No files found matching: {file_pattern}\n📂 Searched: {len(search_paths)} locations"
        
        response = f"🔍 File Search Results for '{file_pattern}':\n\n"
        
        for i, file in enumerate(found_files, 1):
            size_mb = file['size'] / (1024 * 1024)
            response += f"{i}. 📄 {file['name']}\n"
            response += f"   📂 Path: {file['path']}\n"
            response += f"   📏 Size: {size_mb:.2f} MB\n"
            response += f"   📅 Modified: {file['modified']}\n\n"
        
        response += f"📊 Total Found: {len(found_files)} files"
        return response
        
    except Exception as e:
        logging.error(f"Quick file check error: {e}")
        return f"❌ Error searching files: {str(e)}"
