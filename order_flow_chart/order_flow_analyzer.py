#!/usr/bin/env python3
#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, deque#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, deque


class OrderFlowAnalyzer:
    def __init__(self):
        self#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, deque


class OrderFlowAnalyzer:
    def __init__(self):
        self.trades = []
        self.orders = []
        self.snapshots =#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, deque


class OrderFlowAnalyzer:
    def __init__(self):
        self.trades = []
        self.orders = []
        self.snapshots = []
        self.order_flow_data = []
        self.price_levels = set()#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, deque


class OrderFlowAnalyzer:
    def __init__(self):
        self.trades = []
        self.orders = []
        self.snapshots = []
        self.order_flow_data = []
        self.price_levels = set()
        self.time_window = 5  # 时间窗口（秒）
#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, deque


class OrderFlowAnalyzer:
    def __init__(self):
        self.trades = []
        self.orders = []
        self.snapshots = []
        self.order_flow_data = []
        self.price_levels = set()
        self.time_window = 5  # 时间窗口（秒）
    
    def load_csv(self, file_path):
        """加载CSV文件#!/usr/bin/env python3
"""
基于Level 2 CSV数据的订单流图表生成器

功能：
1. 解析Level 2 CSV数据（逐笔成交、逐笔委托、十档快照）
2. 计算订单流指标
3. 生成订单流图表数据
4. 提供Web界面展示
"""
import csv
import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, deque


class OrderFlowAnalyzer:
    def __init__(self):
        self.trades = []
        self.orders = []
        self.snapshots = []
        self.order_flow_data = []
        self.price_levels = set()
        self.time_window = 5  # 时间窗口（秒）
    
    def load_csv(self, file_path):
        """加载CSV文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError