"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边可达性：调用 maps_around_search，参数 location=126.714045,45.753871、radius=2000、keywords=咖啡厅，验证返回pois中包含poi_id=B0GD0B6E49。
2) 步行时间：对poi_id=B0GD0B6E49调用 maps_search_detail 获取其location；再调用 maps_walking_by_coordinates，参数 origin=126.714045,45.753871、destination=该POI的location；验证 total_duration_seconds <= 1200（20分钟）。
3) 营业到21:00之后：调用 maps_search_detail(B0GD0B6E49)，读取 biz_ext.open_time 或 biz_ext.opentime2；验证其当日关门时间晚于21:00（例如为09:30-21:30则满足）。
4) 500米内有公交站：用该POI的location调用 maps_around_search，参数 radius=500、keywords=公交站；验证 pois 列表非空（存在至少1个公交站POI）。
"""

import os
import sys
import re
from datetime import datetime

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_walking_by_coordinates,
)
from tools.amap_tools import maps_around_search


def parse_business_hours(opentime_str: str) -> tuple:
    """
    解析营业时间字符串，返回(开门时间, 关门时间)的元组
    
    支持格式：
    - "09:30-21:30" -> (9, 30, 21, 30)
    - "09:00-22:00" -> (9, 0, 22, 0)
    
    Args:
        opentime_str: 营业时间字符串，格式如"09:30-21:30"
    
    Returns:
        tuple: (开门小时, 开门分钟, 关门小时, 关门分钟)，如果解析失败返回None
    """
    if not opentime_str:
        return None
    
    # 匹配格式：HH:MM-HH:MM
    pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    match = re.match(pattern, opentime_str.strip())
    
    if match:
        open_hour = int(match.group(1))
        open_minute = int(match.group(2))
        close_hour = int(match.group(3))
        close_minute = int(match.group(4))
        return (open_hour, open_minute, close_hour, close_minute)
    
    return None


def check_business_hours_after_21(biz_ext: dict) -> bool:
    """
    检查营业时间是否到21:00之后
    
    Args:
        biz_ext: POI的biz_ext字典
    
    Returns:
        bool: True表示营业到21:00之后，False表示不符合要求或无法确定
    """
    if not biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    # 尝试读取open_time或opentime2
    opentime_str = None
    if biz_ext.get("open_time"):
        opentime_str = biz_ext.get("open_time")
        print(f"📅 找到open_time: {opentime_str}")
    elif biz_ext.get("opentime2"):
        opentime_str = biz_ext.get("opentime2")
        print(f"📅 找到opentime2: {opentime_str}")
    elif biz_ext.get("opentime"):
        opentime_str = biz_ext.get("opentime")
        print(f"📅 找到opentime: {opentime_str}")
    
    if not opentime_str:
        print(f"❌ 无法找到营业时间信息（open_time/opentime2/opentime）")
        return False
    
    # 解析营业时间
    hours = parse_business_hours(opentime_str)
    if not hours:
        print(f"❌ 无法解析营业时间格式: {opentime_str}")
        return False
    
    open_hour, open_minute, close_hour, close_minute = hours
    open_minutes = open_hour * 60 + open_minute
    close_minutes = close_hour * 60 + close_minute

    # 跨天：关门时间在次日凌晨（如 10:00-2:00），有效关门晚于当日任意时刻，满足“晚于21:00”
    if close_minutes <= open_minutes:
        print(f"✅ 营业时间跨天（{open_hour:02d}:{open_minute:02d}-{close_hour:02d}:{close_minute:02d}），关门在次日，晚于21:00")
        return True

    # 检查关门时间是否晚于21:00
    # 21:00 = 21小时0分钟
    if close_hour > 21:
        print(f"✅ 关门时间{close_hour:02d}:{close_minute:02d}晚于21:00")
        return True
    elif close_hour == 21 and close_minute > 0:
        print(f"✅ 关门时间{close_hour:02d}:{close_minute:02d}晚于21:00")
        return True
    elif close_hour == 21 and close_minute == 0:
        print(f"⚠️  关门时间正好21:00，需要确认是否包含21:00")
        # 根据需求，如果正好21:00，可能不满足"21:00之后"的要求
        # 但通常"营业到21:00"可能意味着21:00关门，这里严格判断为不满足
        print(f"❌ 关门时间{close_hour:02d}:{close_minute:02d}不晚于21:00")
        return False
    else:
        print(f"❌ 关门时间{close_hour:02d}:{close_minute:02d}早于21:00")
        return False


def verify_poi(
    poi_id: str,
    user_location: str = "126.714045,45.753871",
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    search_radius: int = 2000,  # 2km
    keywords: str = "咖啡厅",
    bus_stop_search_radius: int = 500,
    bus_stop_keywords: str = "公交站",
    min_close_hour: int = 21  # 最小关门时间（小时）
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 周边可达性：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 步行时间：调用 maps_search_detail 获取POI的location，再调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 1200。
    3) 营业到21:00之后：调用 maps_search_detail，读取 biz_ext.open_time 或 biz_ext.opentime2，验证其当日关门时间晚于21:00。
    4) 500米内有公交站：用该POI的location调用 maps_around_search，验证 pois 列表非空。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"126.714045,45.753871"
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"咖啡厅"
        bus_stop_search_radius: 公交站搜索半径（米），默认500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        min_close_hour: 最小关门时间（小时），默认21
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边可达性（附近2公里内）
    print(f"【步骤1】验证周边可达性（{search_radius}米范围内）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False
    
    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break
    
    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # 步骤2: 获取目标POI坐标和详情
    print(f"\n【步骤2】获取POI详情并验证步行时间")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location} ({poi_detail.name})")
    
    # 验证步行时间
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False
    
    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    
    # 步骤3: 验证营业时间到21:00之后
    print(f"\n【步骤3】验证营业时间到{min_close_hour}:00之后")
    print("-" * 80)
    if not check_business_hours_after_21(poi_detail.biz_ext):
        return False
    
    # 步骤4: 验证500米内有公交站
    print(f"\n【步骤4】验证{bus_stop_search_radius}米内有公交站")
    print("-" * 80)
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False
    
    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False
    
    print(f"✅ 找到公交站: {bus_stop_search_result.pois[0].name} (共{len(bus_stop_search_result.pois)}个)")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python id_525.py <poi_id> [user_location]")
        print("示例: python id_525.py B0GD0B6E49")
        print("示例: python id_525.py B0GD0B6E49 126.714045,45.753871")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0GD0B6E49"
        user_location = "126.714045,45.753871"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "126.714045,45.753871"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
