"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
🔍 验证方法 (verification_method):

我将按照四个步骤进行验证。  
  
步骤1：验证POI在用户周边2km内  
- 调用 maps_around_search，参数：location=114.443824,23.115187，radius=2000，keywords=便利店  
- 断言返回结果pois中包含 target_poi_id=B0JB1MC8QY  
  
步骤2：验证步行时长不超过25分钟  
- 调用 maps_search_detail(B0JB1MC8QY) 获取POI坐标destination  
- 调用 maps_walking_by_coordinates，参数：origin=114.443824,23.115187，destination=POI坐标  
- 断言 total_duration_seconds <= 25*60  
  
步骤3：验证从该店骑行到惠州火车站不超过20分钟  
- 调用 maps_geo，参数：address=惠州火车站，city=惠州，取返回的location作为station_location（使用 formatted_address 对应"惠州火车站(公交站)"那条记录的location=114.417042,23.152309）  
- 调用 maps_bicycling_by_coordinates，参数：origin=POI坐标，destination=station_location  
- 断言 total_duration_seconds <= 20*60  
  
步骤4：验证营业时间满足"至少到23:00还在营业"  
- 调用 maps_search_detail(B0JB1MC8QY)，读取 biz_ext.open_time 或 biz_ext.opentime2  
- 断言其营业时间覆盖到 23:00（例如 07:00-24:00 满足；若为分段营业则需包含23:00所在时段）
"""

import os
import sys
import re

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
    maps_geo,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search


def parse_business_hours(open_time_str: str) -> bool:
    """
    解析营业时间字符串，判断是否覆盖到23:00
    
    Args:
        open_time_str: 营业时间字符串，例如 "07:00-24:00" 或 "08:00-22:00;23:00-01:00"
    
    Returns:
        bool: 如果营业时间覆盖到23:00，返回True；否则返回False
    """
    if not open_time_str:
        return False
    
    # 移除空格
    open_time_str = open_time_str.strip()
    
    # 处理分段营业时间（用分号分隔）
    time_segments = open_time_str.split(';')
    
    for segment in time_segments:
        segment = segment.strip()
        if not segment:
            continue
        
        # 匹配时间范围，例如 "07:00-24:00" 或 "23:00-01:00"
        match = re.match(r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', segment)
        if match:
            start_hour = int(match.group(1))
            start_minute = int(match.group(2))
            end_hour = int(match.group(3))
            end_minute = int(match.group(4))
            
            # 转换为分钟数（从00:00开始）
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            # 处理跨天情况（例如 23:00-01:00）
            if end_minutes < start_minutes:
                # 跨天：23:00-01:00 意味着 23:00-24:00 和 00:00-01:00
                # 23:00在23:00-24:00这个范围内
                if start_minutes <= 23 * 60:
                    return True
            else:
                # 不跨天：检查23:00是否在范围内
                target_minutes = 23 * 60  # 23:00 = 1380分钟
                if start_minutes <= target_minutes < end_minutes:
                    return True
                # 如果结束时间是24:00，也满足
                if end_hour == 24:
                    return True
    
    return False


def verify_poi(
    poi_id: str,
    user_location: str = "114.443824,23.115187",
    max_walking_duration: int = 25 * 60,  # 25分钟 = 1500秒
    search_radius: int = 2000,  # 2km
    keywords: str = "便利店",
    station_address: str = "惠州火车站",
    station_city: str = "惠州",
    station_formatted_address: str = "惠州火车站(公交站)",
    max_bicycling_duration: int = 20 * 60,  # 20分钟 = 1200秒
    required_closing_time: str = "23:00"  # 至少营业到23:00
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 验证POI在用户周边2km内：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 验证步行时长不超过25分钟：调用 maps_search_detail 获取POI坐标，再调用 maps_walking_by_coordinates，验证 total_duration_seconds<=1500。
    3) 验证从该店骑行到惠州火车站不超过20分钟：调用 maps_geo 获取火车站坐标，再调用 maps_bicycling_by_coordinates，验证 total_duration_seconds<=1200。
    4) 验证营业时间满足"至少到23:00还在营业"：调用 maps_search_detail，读取 biz_ext.open_time 或 biz_ext.opentime2，验证营业时间覆盖到23:00。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"114.443824,23.115187"
        max_walking_duration: 最大步行时长（秒），默认1500（25分钟）
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"便利店"
        station_address: 火车站地址，默认"惠州火车站"
        station_city: 火车站所在城市，默认"惠州"
        station_formatted_address: 火车站格式化地址（用于匹配），默认"惠州火车站(公交站)"
        max_bicycling_duration: 最大骑行时长（秒），默认1200（20分钟）
        required_closing_time: 要求的最晚营业时间，默认"23:00"
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 验证POI在用户周边2km内
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
    
    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")
    
    # 步骤2: 验证步行时长不超过25分钟
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
    
    # 步骤3: 验证从该店骑行到惠州火车站不超过20分钟
    geo_result = maps_geo(address=station_address, city=station_city)
    if geo_result.error:
        print(f"❌ 获取火车站坐标失败: {geo_result.error}")
        return False
    
    if not geo_result.results or len(geo_result.results) == 0:
        print(f"❌ 未找到火车站坐标")
        return False
    
    # 查找匹配的formatted_address
    station_location = None
    for result in geo_result.results:
        if station_formatted_address in result.formatted_address:
            station_location = result.location
            print(f"✅ 获取火车站坐标: {station_location} ({result.formatted_address})")
            break
    
    if not station_location:
        # 如果没有找到完全匹配的，使用第一条记录（根据验证方法，应该使用"惠州火车站(公交站)"那条）
        # 但为了更准确，我们尝试查找包含"公交站"的记录
        for result in geo_result.results:
            if "公交站" in result.formatted_address:
                station_location = result.location
                print(f"✅ 获取火车站坐标（使用公交站记录）: {station_location} ({result.formatted_address})")
                break
        
        # 如果还是没找到，使用第一条记录
        if not station_location:
            station_location = geo_result.results[0].location
            print(f"✅ 获取火车站坐标（使用第一条记录）: {station_location} ({geo_result.results[0].formatted_address})")
    
    bicycling_result = maps_bicycling_by_coordinates(origin=poi_location, destination=station_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    
    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False
    
    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 到火车站骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 到火车站骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    
    # 步骤4: 验证营业时间满足"至少到23:00还在营业"
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息，无法验证营业时间")
        return False
    
    # 尝试获取open_time或opentime2
    open_time = None
    if isinstance(poi_detail.biz_ext, dict):
        open_time = poi_detail.biz_ext.get("open_time") or poi_detail.biz_ext.get("opentime2")
    
    if not open_time:
        print(f"❌ POI没有营业时间信息（open_time或opentime2）")
        return False
    
    print(f"📅 POI营业时间: {open_time}")
    
    if not parse_business_hours(open_time):
        print(f"❌ 营业时间{open_time}不满足至少到{required_closing_time}还在营业的要求")
        return False
    
    print(f"✅ 营业时间{open_time}满足至少到{required_closing_time}还在营业的要求")
    
    print(f"✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python id_539.py <poi_id> [user_location]")
        print("示例: python id_539.py B0JB1MC8QY")
        print("示例: python id_539.py B0JB1MC8QY 114.443824,23.115187")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0JB1MC8QY"
        user_location = "114.443824,23.115187"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "114.443824,23.115187"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("-" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("-" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
