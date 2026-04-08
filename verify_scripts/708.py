
"""
修改任务指令：你要找一个附近2公里内的餐厅，走路过去用时不要超过8分钟。吃完饭你还得赶去"汕尾站"，所以从这家餐厅打车到汕尾站的时间不能超过20分钟。另外，这家餐厅得在晚上22:00之后还在营业，并且餐厅附近500米范围内必须能找到公交站。你说话简短急促，希望快速完成所有事。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search({location:"115.363803,22.777305", radius:"2000", keywords:"餐厅"})，确认返回pois中包含目标poi_id=B0K05ZV6GK。
2) 获取POI信息与营业时间：调用 maps_search_detail({id:"B0K05ZV6GK"})，读取biz_ext.open_time 或 biz_ext.opentime2，验证其营业结束时间晚于22:00（例如 open_time=10:00-22:00 视为22:00仍营业；若返回为分段/周几格式，以解析到当日闭店时间>=22:00为准）。同时获取其location=115.362471,22.773550。
3) 步行时间验证：调用 maps_walking_by_coordinates({origin:"115.363803,22.777305", destination:"115.362471,22.773550"})，取 total_duration_seconds/60 得到步行分钟数t_walk，验证 t_walk <= 8。
4) 到汕尾站打车（驾车）时间验证：先调用({address:"汕尾站", city:"汕尾"}) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 汕尾站坐标 destination_station=115.428313,22.809599；再调用 maps_driving_by_coordinates({origin:"115.362471,22.773550", destination:"115.428313,22.809599"})，取 total_duration_seconds/60 得到驾车分钟数t_drive，验证 t_drive <= 20。
5) 公交站邻近验证：调用 maps_around_search({location:"115.362471,22.773550", radius:"500", keywords:"公交站"})，验证返回pois数量>=1（即餐厅500米内存在公交站）。
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
    maps_text_search,
    maps_search_detail ,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.363803,22.777305",
    search_radius: int = 2000,  # 2km
    keywords: str = "餐厅",
    max_walking_minutes: int = 8,
    required_open_time: str = "22:00",
    station_address: str = "汕尾站",
    station_city: str = "汕尾",
    max_driving_minutes: int = 20,
    bus_stop_search_radius: int = 500,
    bus_stop_keywords: str = "公交站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：调用 maps_around_search，确认返回pois中包含目标poi_id。
    2) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 POI信息与营业时间：调用 maps_search_detail，读取biz_ext.open_time或biz_ext.opentime2，验证营业结束时间晚于22:00。同时获取location。
    3) 步行时间验证：调用 maps_walking_by_coordinates，验证步行时间 <= 8分钟。
    4) 到汕尾站打车时间验证：调用获取汕尾站坐标，再调用 maps_driving_by_coordinates，验证驾车时间 <= 20分钟。
    5) 公交站邻近验证：调用 maps_around_search，验证餐厅500米内存在公交站。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.363803,22.777305"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"餐厅"
        max_walking_minutes: 最大步行时长（分钟），默认8
        required_open_time: 要求的营业时间，默认"22:00"
        station_address: 车站地址，默认"汕尾站"
        station_city: 车站所在城市，默认"汕尾"
        max_driving_minutes: 最大驾车时长（分钟），默认20
        bus_stop_search_radius: 公交站搜索半径（米），默认500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（附近2公里）
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

    # 步骤2: 获取POI详情并验证营业时间
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证营业时间
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False

    open_time_str = poi_detail.biz_ext.get("open_time") or poi_detail.biz_ext.get("opentime2")
    if not open_time_str:
        print(f"❌ POI没有营业时间信息")
        return False

    # 解析营业时间，验证是否在22:00之后还营业
    # 简化处理：检查营业时间字符串中是否包含22:00或更晚的时间
    # 例如：10:00-22:00, 10:00-23:00, 周一至周日 10:00-22:00 等
    print(f"✅ 获取营业时间: {open_time_str}")

    # 提取结束时间（假设格式为 XX:XX-YY:YY 或包含此模式）
    import re
    # 匹配时间范围模式，如 10:00-22:00
    time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    matches = re.findall(time_pattern, open_time_str)

    if not matches:
        print(f"❌ 无法解析营业时间格式")
        return False

    # 取最后一个时间段的结束时间（通常是闭店时间）
    last_match = matches[-1]
    close_hour = int(last_match[2])
    close_minute = int(last_match[3])

    # 将required_open_time转换为小时和分钟
    required_parts = required_open_time.split(":")
    required_hour = int(required_parts[0])
    required_minute = int(required_parts[1]) if len(required_parts) > 1 else 0

    # 比较时间：闭店时间应该 >= 要求的时间
    close_time_minutes = close_hour * 60 + close_minute
    required_time_minutes = required_hour * 60 + required_minute

    if close_time_minutes < required_time_minutes:
        print(f"❌ 营业结束时间{close_hour:02d}:{close_minute:02d}早于要求的{required_open_time}")
        return False
    print(f"✅ 营业结束时间{close_hour:02d}:{close_minute:02d}，符合要求（>= {required_open_time}）")

    # 步骤3: 步行时间验证
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration_seconds = walking_result.total_duration_seconds
    walking_duration_minutes = walking_duration_seconds / 60
    if walking_duration_minutes > max_walking_minutes:
        print(f"❌ 步行时长{walking_duration_minutes:.1f}分钟，超过{max_walking_minutes}分钟")
        return False
    print(f"✅ 步行时长{walking_duration_minutes:.1f}分钟，符合要求（<= {max_walking_minutes}分钟）")

    # 步骤4: 到汕尾站打车时间验证（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取车站坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到车站坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    station_location = station_detail_result.location
    print(f"✅ 获取车站坐标: {station_location} ({station_address})")

    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration_seconds = driving_result.total_duration_seconds
    driving_duration_minutes = driving_duration_seconds / 60
    if driving_duration_minutes > max_driving_minutes:
        print(f"❌ 驾车时长{driving_duration_minutes:.1f}分钟，超过{max_driving_minutes}分钟")
        return False
    print(f"✅ 驾车时长{driving_duration_minutes:.1f}分钟，符合要求（<= {max_driving_minutes}分钟）")

    # 步骤5: 公交站邻近验证
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

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 708.py 文件...\n")
    result = verify_poi(poi_id="B0K05ZV6GK")
    print(f"\n验证结果: {result}")
