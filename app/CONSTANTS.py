data_source_redirect="redirect_table"
data_source_upstream="upstream_table"
data_source_redis="redis cache"
upstreamCheckLogTable="upstream_check_log_table"
KEY_DATA_TYPE="type"
DATA_TYPE_DYNAMIC="dynamic"
DATA_TYPE_STATIC="static"
DATA_TYPE_USER_DYNAMIC="user-dynamic"
import subprocess
import re

def get_semver():
    try:
        # Get latest tag, commit count since tag, and short hash
        desc = subprocess.check_output(['git', 'describe', '--tags', '--long', '--match', 'v*'], encoding='utf-8').strip()
        # Example: v3.0.0-5-gabcdef
        m = re.match(r'v?(\d+\.\d+\.\d+)-(\d+)-g([0-9a-f]+)', desc)
        if m:
            base, commits, githash = m.groups()
            # Always use 3.0.0 as base
            base = '3.0.0'
            if int(commits) == 0:
                return base
            else:
                return f"{base}+{commits}.g{githash}"
        # If not matching, fallback to tag or commit count
        commit_count = int(subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], encoding='utf-8').strip())
        githash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], encoding='utf-8').strip()
        return f"3.0.0+{commit_count}.g{githash}"
    except Exception:
        return "3.0.0"

__version__ = get_semver()