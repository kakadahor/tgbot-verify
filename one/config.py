# SheerID 验证配置文件

# SheerID API 配置
PROGRAM_ID = '67c8c14f5f17a83b745e3f82'
SHEERID_BASE_URL = 'https://services.sheerid.com'
MY_SHEERID_URL = 'https://my.sheerid.com'

# 文件大小限制
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

# 学校配置 - Pennsylvania State University
SCHOOLS = {
    '2565': {
        'id': 2565,
        'idExtended': '2565',
        'name': 'Pennsylvania State University-Main Campus',
        'city': 'University Park',
        'state': 'PA',
        'country': 'US',
        'type': 'UNIVERSITY',
        'domain': 'psu.edu',
        'weight': 100
    }
}

# 默认学校
DEFAULT_SCHOOL_ID = '2565'

# URL 配置 - 全部统一到 services.sheerid.com
MY_SHEERID_URL = "https://services.sheerid.com"
SHEERID_BASE_URL = "https://services.sheerid.com"

# UTM 参数（营销追踪参数）
# 如果 URL 中没有这些参数，会自动添加
DEFAULT_UTM_PARAMS = {
    'utm_source': 'gemini',
    'utm_medium': 'paid_media',
    'utm_campaign': 'students_pmax_bts-slap'
}

# 代理配置
# 格式: 'http://user:pass@host:port' 或 None
PROXY = None

