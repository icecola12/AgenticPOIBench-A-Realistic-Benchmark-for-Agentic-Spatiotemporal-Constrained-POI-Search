"""
修改任务指令：你要在附近2公里内找一家酒吧。你准备走路过去，所以步行时间要在10分钟以内。为了后面赶火车，这家酒吧开车到南昌站的时间不能超过8分钟。另外你不想离火车站太近，酒吧附近三公里内需要没有火车站。你对服务和解决方案持怀疑态度。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 核验POI基础信息（类型/评分/坐标）：调用 maps_search_detail(id="B0KDFX219D") 获取POI的 name 与 location。备注：本场景poi_type为"酒吧"，通过周边搜索关键词"酒吧"命中该POI来间接验证其类型。
2) 核验"附近2公里内"且候选数量充足：调用 maps_around_search(location="115.923627,28.695178", radius="2000", keywords="酒吧") 获取pois列表。验证：返回的pois中包含 id == "B0KDFX219D"，从而证明目标酒吧在用户2公里范围内。
3) 核验步行时间不超过10分钟：从步骤1得到目标POI坐标 destination=location。调用 maps_walking_by_coordinates(origin="115.923627,28.695178", destination=destination)。验证：total_duration_seconds <= 600。
4) 核验到南昌站驾车时间不超过8分钟，且酒吧不在任一"火车站"3公里内：
   a) 调用 maps_geo(address="南昌站", city="南昌") 获取南昌站坐标 rail_loc。
   b) 调用 maps_driving_by_coordinates(origin=destination, destination=rail_loc)。验证：total_duration_seconds <= 480。
   c) 调用 maps_around_search(location=destination, radius="3000", keywords="火车站")。验证：返回pois为空或pois数量为0（表示酒吧3公里范围内没有火车站POI）。
"""

import os
import sys

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
    maps_driving_by_coordinates,
    maps_geo
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.923627,28.695178",
    poi_location: str = None,
    station_address: str = "南昌站",
    station_city: str = "南昌",
    station_location: str = None,
    search_radius: int = 2000,
    keywords: str = "酒吧",
    max_walking_duration: int = 600,  # 10分钟 = 600秒
    max_driving_duration: int = 480,  # 8分钟 = 480秒
    station_search_radius: int = 3000,
    station_keywords: str = "火车站"
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 核验POI基础信息（类型/评分/坐标）：调用 maps_search_detail 获取POI的 name 与 location。
    2) 核验"附近2公里内"且候选数量充足：调用 maps_around_search，验证返回pois中包含目标poi_id。
    3) 核验步行时间不超过10分钟：调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 600。
    4) 核验到南昌站驾车时间不超过8分钟，且酒吧不在任一"火车站"3公里内：
       a) 调用 maps_geo 获取南昌站坐标。
       b) 调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 480。
       c) 调用 maps_around_search，验证返回pois为空或pois数量为0。
    
    Args:
        poi_id: POI ID，默认"B0KDFX219D"
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.923627,28.695178"
        poi_location: POI坐标，格式为"经度,纬度"，如果为None则从详情中获取
        station_address: 车站地址，默认"南昌站"
        station_city: 车站所在城市，默认"南昌"
        station_location: 车站坐标，格式为"经度,纬度"，如果为None则从地理编码中获取
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒吧"
        max_walking_duration: 最大步行时长（秒），默认600（10分钟）
        max_driving_duration: 最大驾车时长（秒），默认480（8分钟）
        station_search_radius: 火车站搜索半径（米），默认3000（3公里）
        station_keywords: 火车站搜索关键词，默认"火车站"
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 核验POI基础信息（类型/评分/坐标）
    print(f"【步骤1】核验POI基础信息（类型/评分/坐标）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.name:
        print(f"❌ POI没有name信息")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI信息: {poi_detail.name} (ID: {poi_id})")
    print(f"✅ 获取POI坐标: {poi_location}")
    print(f"📝 备注：本场景poi_type为\"{keywords}\"，通过周边搜索关键词\"{keywords}\"命中该POI来间接验证其类型。")
    
    # 步骤2: 核验"附近2公里内"且候选数量充足
    print(f"\n【步骤2】核验\"附近{search_radius // 1000}公里内\"且候选数量充足")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
        print(f"❌ 未找到符合条件的POI")
        return False
    
    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            print(f"✅ 返回POI总数: {len(around_search_result.pois)}")
            break
    
    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # 步骤3: 核验步行时间不超过10分钟
    print(f"\n【步骤3】核验步行时间不超过{max_walking_duration // 60}分钟")
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
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
    
    # 步骤4: 核验到南昌站驾车时间不超过8分钟，且酒吧不在任一"火车站"3公里内
    print(f"\n【步骤4】核验到{station_address}驾车时间不超过{max_driving_duration // 60}分钟，且酒吧不在任一\"{station_keywords}\"{station_search_radius // 1000}公里内")
    print("-" * 80)
    
    # 4a) 获取南昌站坐标
    print(f"【4a】获取{station_address}坐标")
    geo_result = maps_geo(address=station_address, city=station_city)
    if geo_result.error:
        print(f"❌ 获取车站坐标失败: {geo_result.error}")
        return False
    
    if not geo_result.results or len(geo_result.results) == 0:
        print(f"❌ 未找到车站地址")
        return False
    
    if geo_result.results[0].location:
        station_location = geo_result.results[0].location
        print(f"✅ 获取车站坐标: {station_location} ({station_address})")
    else:
        print(f"❌ 车站地理编码结果中没有location信息")
        return False
    
    # 4b) 验证驾车时间不超过8分钟
    print(f"\n【4b】验证驾车时间不超过{max_driving_duration // 60}分钟")
    driving_result = maps_driving_by_coordinates(
        origin=poi_location,
        destination=station_location
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 4c) 验证酒吧不在任一"火车站"3公里内
    print(f"\n【4c】验证酒吧不在任一\"{station_keywords}\"{station_search_radius // 1000}公里内")
    station_search_result = maps_around_search(
        location=poi_location,
        radius=str(station_search_radius),
        keywords=station_keywords
    )
    if station_search_result.error:
        print(f"❌ 搜索{station_keywords}失败: {station_search_result.error}")
        return False
    
    if station_search_result.pois and len(station_search_result.pois) > 0:
        print(f"❌ 酒吧{station_search_radius}米范围内找到{station_keywords}POI: {len(station_search_result.pois)}个")
        for poi in station_search_result.pois[:3]:  # 只显示前3个
            print(f"   - {poi.name} (ID: {poi.id})")
        return False
    
    print(f"✅ 酒吧{station_search_radius}米范围内没有{station_keywords}POI（返回pois为空或数量为0）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 591.py <poi_id> [user_location] [poi_location]")
        print("示例: python 591.py B0KDFX219D")
        print("示例: python 591.py B0KDFX219D 115.923627,28.695178")
        print("示例: python 591.py B0KDFX219D 115.923627,28.695178 115.923627,28.695178")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0KDFX219D"
        user_location = "115.923627,28.695178"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "115.923627,28.695178"
        poi_location = sys.argv[3] if len(sys.argv) > 3 else None
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    if poi_location:
        print(f"POI坐标: {poi_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, poi_location=poi_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
