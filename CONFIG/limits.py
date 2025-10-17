# Limits Configuration

class LimitsConfig(object):
    #######################################################
    # Limits and restrictions
    #######################################################
    MAX_FILE_SIZE_GB = 8  # GiB
    # Download timeout in seconds (2 hours = 7200 seconds)
    DOWNLOAD_TIMEOUT = 7200 # in seconds
    MAX_SUB_QUALITY = 720 # 720p
    MAX_SUB_DURATION = 5400 # in seconds
    MAX_SUB_SIZE = 500 # in MB      
    MAX_PLAYLIST_COUNT = 50
    MAX_TIKTOK_COUNT = 500        
    # Max number of media files to download/send for /img
    MAX_IMG_FILES = 1000
    # Max single video duration in seconds for yt-dlp downloads (default 12 hours)
    MAX_VIDEO_DURATION = 43200
    #######################################################
    # Image download timeouts (in seconds)
    # Maximum wait time for one range (30 minutes) - for large videos
    # Increase this if you have very large video files that take longer to download
    MAX_IMG_RANGE_WAIT_TIME = 1800  # 30 minutes
    
    # Maximum total wait time (4 hours) - for very large collections
    # Increase this if you download very large Instagram accounts with thousands of posts
    MAX_IMG_TOTAL_WAIT_TIME = 14400  # 4 hours
    
    # Maximum inactivity time (5 minutes) - if no new files found
    # If no new files are found for this time, download stops (prevents infinite waiting)
    MAX_IMG_INACTIVITY_TIME = 300  # 5 minutes
    
    # Example configurations for different scenarios:
    # For fast internet and small files: MAX_IMG_RANGE_WAIT_TIME = 600 (10 min), MAX_IMG_TOTAL_WAIT_TIME = 3600 (1 hour)
    # For slow internet and large files: MAX_IMG_RANGE_WAIT_TIME = 3600 (1 hour), MAX_IMG_TOTAL_WAIT_TIME = 28800 (8 hours)
    # For very large accounts: MAX_IMG_TOTAL_WAIT_TIME = 43200 (12 hours)
    #######################################################
    # Group multipliers (applied in groups/channels) - except quality
    GROUP_MULTIPLIER = 2
    #######################################################
    NSFW_STAR_COST = 1
    ###############################################################################    
    ###############################################################################
    ## DO NOT CHANGE CONFIGURATION BELOW (IF YOU ARE NOT SURE WHAT YOU ARE DOING)##      
    ###############################################################################
    ###############################################################################    
    # Enterprise Scaling Configuration
    #######################################################
    
    # Main scaling limits (optimized for Oracle Cloud: 4 vCPU, 24 GB RAM, 4 Gbit/sec)
    MAX_USERS = 5000                     # Maximum concurrent users (increased for better resources)
    MAX_PROCESSES = 30                   # Number of processes (optimal for 4 vCPU)
    MAX_THREADS_PER_PROCESS = 150        # Threads per process (optimal for 24 GB RAM)
    MAX_GLOBAL_WORKERS = 4500            # Total number of threads (30 * 150)
    
    # Download limits
    MAX_DOWNLOADS_PER_USER = 1          # Downloads per user
    MAX_CONCURRENT_GLOBAL = 4500        # Total concurrent downloads
    
    # Priority pools (processes) - optimized for 4 vCPU
    VIP_PROCESSES = 3                    # VIP users (admins) - increased
    HIGH_PROCESSES = 6                   # HIGH priority (every 100th user) - increased
    NORMAL_PROCESSES = 15                # NORMAL priority (every 10th user) - increased
    LOW_PROCESSES = 6                    # LOW priority (others) - increased
    
    # Connection pools - optimized for 24 GB RAM and 4 Gbit/sec network
    FIREBASE_POOL_SIZE = 500             # Firebase connection pool size (increased for better network)
    TELEGRAM_POOL_SIZE = 500             # Telegram connection pool size (increased for better network)
    
    # Monitoring and scaling
    RESOURCE_CHECK_INTERVAL = 5         # Resource check interval (seconds)
    AUTO_SCALE_THRESHOLD = 80           # Auto-scaling threshold (%)
    
    # Queues
    QUEUE_SIZE = 50000                  # Queue size
    QUEUE_TIMEOUT = 300                 # Queue timeout (seconds)
    
    # Semaphores - optimized for 4 vCPU, 24 GB RAM
    GUARD_SEMAPHORE_LIMIT = 4500        # Semaphore limit in guard.py (increased for better performance)
    
    #######################################################
    # Predefined configurations for different loads
    #######################################################
    
    # Configuration for small loads (< 100 users)
    SMALL_SCALE_CONFIG = {
        'max_processes': 10,
        'max_threads_per_process': 10,
        'max_global_workers': 100,
        'max_concurrent_global': 100,
        'firebase_pool_size': 50,
        'telegram_pool_size': 50
    }
    
    # Configuration for medium loads (< 1000 users)
    MEDIUM_SCALE_CONFIG = {
        'max_processes': 50,
        'max_threads_per_process': 20,
        'max_global_workers': 1000,
        'max_concurrent_global': 1000,
        'firebase_pool_size': 200,
        'telegram_pool_size': 200
    }
    
    # Configuration for large loads (< 5000 users)
    LARGE_SCALE_CONFIG = {
        'max_processes': 100,
        'max_threads_per_process': 50,
        'max_global_workers': 5000,
        'max_concurrent_global': 5000,
        'firebase_pool_size': 500,
        'telegram_pool_size': 500
    }
    
    # Configuration for enterprise loads (10000+ users)
    ENTERPRISE_SCALE_CONFIG = {
        'max_processes': 200,
        'max_threads_per_process': 50,
        'max_global_workers': 10000,
        'max_concurrent_global': 10000,
        'firebase_pool_size': 1000,
        'telegram_pool_size': 1000
    }
    
    # Configuration for extreme loads (50000+ users)
    EXTREME_SCALE_CONFIG = {
        'max_processes': 500,
        'max_threads_per_process': 100,
        'max_global_workers': 50000,
        'max_concurrent_global': 50000,
        'firebase_pool_size': 2000,
        'telegram_pool_size': 2000
    }
    
    # Configuration for Oracle Cloud (4 vCPU, 24 GB RAM, 200 GB HDD, 4 Gbit/sec)
    ORACLE_CLOUD_CONFIG = {
        'max_processes': 30,
        'max_threads_per_process': 150,
        'max_global_workers': 4500,
        'max_concurrent_global': 4500,
        'firebase_pool_size': 500,
        'telegram_pool_size': 500
    }
    
    #######################################################
    # System requirements for different configurations
    #######################################################
    
    SYSTEM_REQUIREMENTS = {
        'small': {
            'cpu_cores': 2,
            'ram_gb': 4,
            'disk_gb': 50,
            'network_mbps': 50
        },
        'medium': {
            'cpu_cores': 4,
            'ram_gb': 8,
            'disk_gb': 200,
            'network_mbps': 200
        },
        'large': {
            'cpu_cores': 8,
            'ram_gb': 16,
            'disk_gb': 500,
            'network_mbps': 500
        },
        'enterprise': {
            'cpu_cores': 16,
            'ram_gb': 32,
            'disk_gb': 1000,
            'network_mbps': 1000
        },
        'extreme': {
            'cpu_cores': 32,
            'ram_gb': 64,
            'disk_gb': 2000,
            'network_mbps': 2000
        },
        'oracle_cloud': {
            'cpu_cores': 4,
            'ram_gb': 24,
            'disk_gb': 200,
            'network_mbps': 4000
        }
    }
    