#!/usr/bin/env python3
"""
Resource monitoring script for tg-ytdlp-bot
Shows real-time resource usage
"""

import psutil
import time
import os
import sys

def get_bot_processes():
    """Get all bot-related processes"""
    bot_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'magic.py' in cmdline or 'python' in proc.info['name']:
                    bot_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return bot_processes

def get_system_stats():
    """Get system statistics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_percent': cpu_percent,
        'memory_total': memory.total,
        'memory_used': memory.used,
        'memory_percent': memory.percent,
        'disk_total': disk.total,
        'disk_used': disk.used,
        'disk_percent': (disk.used / disk.total) * 100
    }

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def monitor_resources():
    """Monitor bot resources in real-time"""
    print("🔍 tg-ytdlp-bot Resource Monitor")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("🔍 tg-ytdlp-bot Resource Monitor")
            print("=" * 50)
            print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # System stats
            stats = get_system_stats()
            print("🖥️  System Resources:")
            print(f"   CPU: {stats['cpu_percent']:.1f}%")
            print(f"   RAM: {format_bytes(stats['memory_used'])} / {format_bytes(stats['memory_total'])} ({stats['memory_percent']:.1f}%)")
            print(f"   Disk: {format_bytes(stats['disk_used'])} / {format_bytes(stats['disk_total'])} ({stats['disk_percent']:.1f}%)")
            print()
            
            # Bot processes
            bot_processes = get_bot_processes()
            print(f"🤖 Bot Processes: {len(bot_processes)}")
            
            if bot_processes:
                total_cpu = 0
                total_memory = 0
                
                for i, proc in enumerate(bot_processes):
                    try:
                        cpu = proc.cpu_percent()
                        memory = proc.memory_info()
                        total_cpu += cpu
                        total_memory += memory.rss
                        
                        print(f"   Process {i+1}: PID={proc.pid}, CPU={cpu:.1f}%, RAM={format_bytes(memory.rss)}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                print(f"   Total Bot CPU: {total_cpu:.1f}%")
                print(f"   Total Bot RAM: {format_bytes(total_memory)}")
            else:
                print("   No bot processes found")
            
            print()
            print("📊 Resource Limits (from CONFIG/limits.py):")
            print("   Max Users: 5000")
            print("   Max Processes: 30")
            print("   Max Threads: 4500")
            print("   Max Concurrent Downloads: 4500")
            print()
            print("💡 Note: Resources are allocated on-demand, not at startup")
            print("   - Processes created only when users request downloads")
            print("   - Threads created only when needed")
            print("   - Memory used only for active operations")
            print()
            print("Press Ctrl+C to stop monitoring...")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    monitor_resources()
