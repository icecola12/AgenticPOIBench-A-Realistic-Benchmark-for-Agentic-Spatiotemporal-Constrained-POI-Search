"""
修改任务指令：你想找一个附近1.2公里的电影院。你准备骑车过去，所以骑行时间要在6分钟以内。而且你希望它在今天23:00之后还在营业。为了方便散场后赶去新乡东站坐车，要求从这家电影院开车到新乡东站的时间不超过20分钟。另外你不想去太偏远的店，所以这家电影院到新乡东站的直线距离也得在9公里以内，并且评分要不低于4.4。你害羞且缺乏安全感，说话犹豫，不自信。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边与类型验证：调用 maps_around_search(location="113.89986,35.296795", radius="1200", keywords="电影院")，验证返回pois中包含poi_id=B0FFHVEDIH。
2) 详情与评分/营业时间验证：调用 maps_search_detail(id="B0FFHVEDIH")，读取biz_ext.rating与biz_ext.open_time/opentime2，验证评分>=4.4，且营业时间覆盖到23:00之后（例如08:00-24:00）。
3) 骑行时间约束：用步骤2拿到POI的location="113.902223,35.296570"，调用 maps_bicycling_by_coordinates(origin="113.89986,35.296795", destination="113.902223,35.296570")，验证total_duration_seconds<=360。
4) 到新乡东站驾车时间约束：调用 maps_geo(address="新乡东站", city="新乡") 获取东站location="113.979042,35.314281"；再调用 maps_driving_by_coordinates(origin="113.902223,35.296570", destination="113.979042,35.314281")，验证total_duration_seconds<=1200。
5) 到新乡东站直线距离约束：调用 maps_distance(origins="113.902223,35.296570", destination="113.979042,35.314281")，验证distance<=9000(米)。
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
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates,
    maps_geo,
    maps_distance
)
from tools.amap_tools import maps_around_search


def parse_business_hours(opentime_str: str) -> tuple:
    """
    解析营业时间字符串，返回(开门时间, 关门时间)的元组
    
    支持格式：
    - "08:00-24:00" -> (8, 0, 24, 0)
    - "09:30-23:30" -> (9, 30, 23, 30)
    
    Args:
        opentime_str: 营业时间字符串，格式如"08:00-24:00"
    
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


def check_business_hours_after_23(biz_ext: dict) -> bool:
    """
    检查营业时间是否覆盖到23:00之后
    
    Args:
        biz_ext: POI的biz_ext字典
    
    Returns:
        bool: True表示营业时间覆盖到23:00之后，False表示不符合要求或无法确定
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

    # 跨天：关门时间在次日凌晨（如 10:00-2:00），有效关门晚于当日任意时刻，满足“晚于23:00”
    if close_minutes <= open_minutes:
        print(f"✅ 营业时间跨天（{open_hour:02d}:{open_minute:02d}-{close_hour:02d}:{close_minute:02d}），关门在次日，晚于23:00")
        return True

    # 检查关门时间是否晚于23:00
    # 23:00 = 23小时0分钟
    if close_hour > 23:
        print(f"✅ 关门时间{close_hour:02d}:{close_minute:02d}晚于23:00")
        return True
    elif close_hour == 23 and close_minute > 0:
        print(f"✅ 关门时间{close_hour:02d}:{close_minute:02d}晚于23:00")
        return True
    elif close_hour == 23 and close_minute == 0:
        print(f"⚠️  关门时间正好23:00，需要确认是否包含23:00")
        # 根据需求，如果正好23:00，可能不满足"23:00之后"的要求
        # 但通常"营业到23:00"可能意味着23:00关门，这里严格判断为不满足
        print(f"❌ 关门时间{close_hour:02d}:{close_minute:02d}不晚于23:00")
        return False
    else:
        print(f"❌ 关门时间{close_hour:02d}:{close_minute:02d}早于23:00")
        return False


def verify_poi(
    poi_id: str,
    user_location: str = "113.89986,35.296795",
    cinema_location: str = "113.902223,35.296570",
    station_address: str = "新乡东站",
    station_city: str = "新乡",
    station_location: str = "113.979042,35.314281",
    search_radius: int = 1200,
    keywords: str = "电影院",
    min_rating: float = 4.4,
    max_bicycling_duration: int = 360,  # 6分钟 = 360秒
    max_driving_duration: int = 1200,  # 20分钟 = 1200秒
    max_distance: int = 9000  # 9公里 = 9000米
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 周边与类型验证：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 详情与评分/营业时间验证：调用 maps_search_detail，读取biz_ext.rating与biz_ext.open_time/opentime2，验证评分>=4.4，且营业时间覆盖到23:00之后。
    3) 骑行时间约束：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds<=360（6分钟）。
    4) 到新乡东站驾车时间约束：调用 maps_geo 获取东站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds<=1200（20分钟）。
    5) 到新乡东站直线距离约束：调用 maps_distance，验证 distance<=9000（9公里）。
    
    Args:
        poi_id: POI ID，默认"B0FFHVEDIH"
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.89986,35.296795"
        cinema_location: 电影院坐标，格式为"经度,纬度"，默认"113.902223,35.296570"
        station_address: 车站地址，默认"新乡东站"
        station_city: 车站所在城市，默认"新乡"
        station_location: 车站坐标，格式为"经度,纬度"，默认"113.979042,35.314281"
        search_radius: 搜索半径（米），默认1200（1.2公里）
        keywords: 搜索关键词，默认"电影院"
        min_rating: 最小评分，默认4.4
        max_bicycling_duration: 最大骑行时长（秒），默认360（6分钟）
        max_driving_duration: 最大驾车时长（秒），默认1200（20分钟）
        max_distance: 最大直线距离（米），默认9000（9公里）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边与类型验证
    print(f"【步骤1】验证周边与类型（{search_radius}米范围内，关键词：{keywords}）")
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
            break
    
    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # 步骤2: 详情与评分/营业时间验证
    print(f"\n【步骤2】验证详情与评分/营业时间（评分>={min_rating}，营业时间覆盖到23:00之后）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    # 验证评分
    rating = poi_detail.biz_ext.get("rating")
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False
    
    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析rating值: {rating}")
        return False
    
    if rating_value < min_rating:
        print(f"❌ POI评分{rating_value}，低于要求的最小评分{min_rating}")
        return False
    print(f"✅ POI评分{rating_value}，满足要求（>={min_rating}）")
    
    # 验证营业时间
    if not check_business_hours_after_23(poi_detail.biz_ext):
        return False
    
    # 获取电影院坐标（如果详情中有location，使用详情中的；否则使用传入的默认值）
    if poi_detail.location:
        cinema_location = poi_detail.location
        print(f"✅ 获取电影院坐标: {cinema_location} ({poi_detail.name})")
    else:
        print(f"⚠️  POI详情中没有location信息，使用默认坐标: {cinema_location}")
    
    # 步骤3: 骑行时间约束
    print(f"\n【步骤3】验证骑行时间（<={max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=cinema_location
    )
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    
    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False
    
    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    
    # 步骤4: 到新乡东站驾车时间约束
    print(f"\n【步骤4】验证到新乡东站驾车时间（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    # 获取车站坐标
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
        print(f"⚠️  车站地理编码结果中没有location信息，使用默认坐标: {station_location}")
    
    # 计算驾车时间
    driving_result = maps_driving_by_coordinates(
        origin=cinema_location,
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
    
    # 步骤5: 到新乡东站直线距离约束
    print(f"\n【步骤5】验证到新乡东站直线距离（<={max_distance}米，即{max_distance // 1000}公里）")
    print("-" * 80)
    distance_result = maps_distance(
        origins=cinema_location,
        destination=station_location
    )
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离测量结果")
        return False
    
    distance_value = distance_result.results[0].distance_meters
    if distance_value > max_distance:
        print(f"❌ 直线距离{distance_value}米，超过{max_distance}米（{max_distance // 1000}公里）")
        return False
    print(f"✅ 直线距离{distance_value}米，符合要求（<= {max_distance}米，即{max_distance // 1000}公里）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 585.py <poi_id> [user_location] [cinema_location]")
        print("示例: python 585.py B0FFHVEDIH")
        print("示例: python 585.py B0FFHVEDIH 113.89986,35.296795")
        print("示例: python 585.py B0FFHVEDIH 113.89986,35.296795 113.902223,35.296570")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0FFHVEDIH"
        user_location = "113.89986,35.296795"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "113.89986,35.296795"
        cinema_location = sys.argv[3] if len(sys.argv) > 3 else "113.902223,35.296570"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print(f"电影院坐标: {cinema_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, cinema_location=cinema_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
