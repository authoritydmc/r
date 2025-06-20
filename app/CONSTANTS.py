data_source_redirect="redirect_table"
data_source_upstream="upstream_table"
data_source_redis="redis cache"
upstreamCheckLogTable="upstream_check_log_table"
KEY_DATA_TYPE="type"
DATA_TYPE_DYNAMIC="dynamic"
DATA_TYPE_STATIC="static"
import subprocess

def get_semver():
    major = 2
    try:
        commit_count = int(subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], encoding='utf-8').strip())
        minor = commit_count // 100
        patch = commit_count % 100
        return f"{major}.{minor}.{patch}"
    except Exception:
        return "2.0.0"

__version__ = get_semver()