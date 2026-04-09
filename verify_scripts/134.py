
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边距离约束（附近3000米）：调用 maps_around_search(location='116.035001,43.944691', radius='3000', keywords='公共厕所')，验证返回pois中包含目标poi_id=B0FFIBFXMU。
2) 到出发地最大驾车距离（≤2公里）：调用 maps_search_detail('B0FFIBFXMU') 取目标坐标dest；调用 maps_driving_by_coordinates(origin='116.035001,43.944691', destination=dest)，验证 total_distance_meters ≤ 2000。
3) 目标场所到附近1500米内公交站的最小步行距离（≤22分钟）：以目标坐标为中心调用 maps_around_search(location=dest, radius='1500', keywords='公交站') 获取站点列表；对每个站点坐标si调用 maps_walking_by_coordinates(origin=dest, destination=si)，取 total_duration_seconds 的最小值min_t，验证 min_t ≤ 22*60。
4) 目标场所到附近1500米内公交站的最小直线距离（≤300米）：对步骤3同一批公交站坐标，调用 maps_distance(origins=站点坐标用'|'拼接, destination=dest)，取 distance_meters 的最小值min_d，验证 min_d ≤ 300。
5) 到指定公交站点的最大步行距离（≤1300米）：调用 maps_text_search(keywords='锡盟行政中心(公交站)', city='锡林浩特市', citylimit='true')，取返回中 id='BV10124066' 的坐标bs；调用 maps_walking_by_coordinates(origin=dest, destination=bs)，验证 total_distance_meters ≤ 1300。
6) 到特定交通枢纽（锡林浩特机场）最大驾车时间（≤16分钟）：调用 maps_text_search(keywords='锡林浩特机场', city='锡林浩特市') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取机场坐标ap；调用 maps_driving_by_coordinates(origin=dest, destination=ap)，验证 total_duration_seconds ≤ 16*60。
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
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance,
    maps_text_search
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.035001,43.944691",
    search_radius: int = 3000,  # 3km
    keywords: str = "公共厕所",
    max_driving_distance: int = 2000,  # 2km
    bus_stop_search_radius: int = 1500,  # 1.5km
    bus_stop_keywords: str = "公交站",
    max_walking_duration_to_bus: int = 22 * 60,  # 22 minutes = 1320 seconds
    max_straight_distance_to_bus: int = 300,  # 300 meters
    specific_bus_stop_keywords: str = "锡盟行政中心(公交站)",
    specific_bus_stop_city: str = "锡林浩特市",
    specific_bus_stop_id: str = "BV10124066",
    max_walking_distance_to_specific_bus: int = 1300,  # 1300 meters
    airport_address: str = "锡林浩特机场",
    airport_city: str = "锡林浩特市",
    max_driving_duration_to_airport: int = 16 * 60  # 16 minutes = 960 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边距离约束（附近3000米）：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 到出发地最大驾车距离（≤2公里）：调用 maps_search_detail 取目标坐标，再调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 2000。
    3) 目标场所到附近1500米内公交站的最小步行距离（≤22分钟）：以目标坐标为中心调用 maps_around_search 获取站点列表，对每个站点调用 maps_walking_by_coordinates，取最小值验证 ≤ 22*60。
    4) 目标场所到附近1500米内公交站的最小直线距离（≤300米）：对步骤3同一批公交站坐标，调用 maps_distance，取最小值验证 ≤ 300。
    5) 到指定公交站点的最大步行距离（≤1300米）：调用 maps_text_search 获取指定公交站坐标，调用 maps_walking_by_coordinates，验证 total_distance_meters ≤ 1300。
    6) 到特定交通枢纽（锡林浩特机场）最大驾车时间（≤16分钟）：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取机场坐标，调用 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 16*60。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.035001,43.944691"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"公共厕所"
        max_driving_distance: 最大驾车距离（米），默认2000（2公里）
        bus_stop_search_radius: 公交站搜索半径（米），默认1500（1.5公里）
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_walking_duration_to_bus: 到公交站最大步行时长（秒），默认1320（22分钟）
        max_straight_distance_to_bus: 到公交站最大直线距离（米），默认300
        specific_bus_stop_keywords: 指定公交站关键词，默认"锡盟行政中心(公交站)"
        specific_bus_stop_city: 指定公交站所在城市，默认"锡林浩特市"
        specific_bus_stop_id: 指定公交站ID，默认"BV10124066"
        max_walking_distance_to_specific_bus: 到指定公交站最大步行距离（米），默认1300
        airport_address: 机场地址，默认"锡林浩特机场"
        airport_city: 机场所在城市，默认"锡林浩特市"
        max_driving_duration_to_airport: 到机场最大驾车时长（秒），默认960（16分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边距离约束（附近3000米）
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

    # 步骤2: 到出发地最大驾车距离（≤2公里）
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 到出发地驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 到出发地驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")

    # 步骤3: 目标场所到附近1500米内公交站的最小步行距离（≤22分钟）
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

    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")

    # 计算到每个公交站的步行时间，找最小值
    min_walking_duration = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue
        walking_result = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop.location)
        if walking_result.error or walking_result.total_duration_seconds is None:
            continue
        if min_walking_duration is None or walking_result.total_duration_seconds < min_walking_duration:
            min_walking_duration = walking_result.total_duration_seconds

    if min_walking_duration is None:
        print(f"❌ 无法计算到公交站的步行时间")
        return False

    if min_walking_duration > max_walking_duration_to_bus:
        print(f"❌ 到最近公交站步行时间{min_walking_duration}秒，超过{max_walking_duration_to_bus}秒（{max_walking_duration_to_bus // 60}分钟）")
        return False
    print(f"✅ 到最近公交站步行时间{min_walking_duration}秒，符合要求（<= {max_walking_duration_to_bus}秒，即{max_walking_duration_to_bus // 60}分钟）")

    # 步骤4: 目标场所到附近1500米内公交站的最小直线距离（≤300米）
    # 构建所有公交站坐标字符串（用'|'拼接）
    bus_stop_locations = []
    for bus_stop in bus_stop_search_result.pois:
        if bus_stop.location:
            bus_stop_locations.append(bus_stop.location)

    if len(bus_stop_locations) == 0:
        print(f"❌ 没有有效的公交站坐标")
        return False

    origins_str = '|'.join(bus_stop_locations)
    distance_result = maps_distance(origins=origins_str, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到距离结果")
        return False

    # 找最小直线距离
    min_straight_distance = min(result.distance_meters for result in distance_result.results)
    if min_straight_distance > max_straight_distance_to_bus:
        print(f"❌ 到最近公交站直线距离{min_straight_distance}米，超过{max_straight_distance_to_bus}米")
        return False
    print(f"✅ 到最近公交站直线距离{min_straight_distance}米，符合要求（<= {max_straight_distance_to_bus}米）")

    # 步骤5: 到指定公交站点的最大步行距离（≤1300米）
    specific_bus_search_result = maps_text_search(
        keywords=specific_bus_stop_keywords,
        city=specific_bus_stop_city,
        citylimit="true"
    )
    if specific_bus_search_result.error:
        print(f"❌ 搜索指定公交站失败: {specific_bus_search_result.error}")
        return False

    if not specific_bus_search_result.pois or len(specific_bus_search_result.pois) == 0:
        print(f"❌ 未找到指定公交站")
        return False

    # 查找指定ID的公交站
    specific_bus_location = None
    for bus_stop in specific_bus_search_result.pois:
        if bus_stop.id == specific_bus_stop_id:
            # 需要获取该公交站的详细坐标
            bus_detail = maps_search_detail(id=specific_bus_stop_id)
            if bus_detail.error or not bus_detail.location:
                print(f"❌ 获取指定公交站坐标失败")
                return False
            specific_bus_location = bus_detail.location
            print(f"✅ 获取指定公交站坐标: {specific_bus_location} ({specific_bus_stop_keywords})")
            break

    if not specific_bus_location:
        print(f"❌ 未找到ID为{specific_bus_stop_id}的公交站")
        return False

    walking_to_specific_bus_result = maps_walking_by_coordinates(origin=poi_location, destination=specific_bus_location)
    if walking_to_specific_bus_result.error:
        print(f"❌ 计算到指定公交站步行路线失败: {walking_to_specific_bus_result.error}")
        return False

    if walking_to_specific_bus_result.total_distance_meters is None:
        print(f"❌ 无法获取到指定公交站步行距离")
        return False

    walking_distance_to_specific_bus = walking_to_specific_bus_result.total_distance_meters
    if walking_distance_to_specific_bus > max_walking_distance_to_specific_bus:
        print(f"❌ 到指定公交站步行距离{walking_distance_to_specific_bus}米，超过{max_walking_distance_to_specific_bus}米")
        return False
    print(f"✅ 到指定公交站步行距离{walking_distance_to_specific_bus}米，符合要求（<= {max_walking_distance_to_specific_bus}米）")

    # 步骤6: 到特定交通枢纽（锡林浩特机场）最大驾车时间（≤16分钟）
    text_search_result = maps_text_search(keywords=airport_address, city=airport_city)
    if text_search_result.error:
        print(f"❌ 获取机场坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到机场坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取机场坐标失败: {detail_result.error or '无location'}")
        return False

    airport_location = detail_result.location
    print(f"✅ 获取机场坐标: {airport_location} ({airport_address})")

    driving_to_airport_result = maps_driving_by_coordinates(origin=poi_location, destination=airport_location)
    if driving_to_airport_result.error:
        print(f"❌ 计算到机场驾车路线失败: {driving_to_airport_result.error}")
        return False

    if driving_to_airport_result.total_duration_seconds is None:
        print(f"❌ 无法获取到机场驾车时长")
        return False

    driving_duration_to_airport = driving_to_airport_result.total_duration_seconds
    if driving_duration_to_airport > max_driving_duration_to_airport:
        print(f"❌ 到机场驾车时长{driving_duration_to_airport}秒，超过{max_driving_duration_to_airport}秒（{max_driving_duration_to_airport // 60}分钟）")
        return False
    print(f"✅ 到机场驾车时长{driving_duration_to_airport}秒，符合要求（<= {max_driving_duration_to_airport}秒，即{max_driving_duration_to_airport // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    print("开始验证 775.py 文件...\\n")
    result = verify_poi(poi_id="B0FFIBFXMU")
    print(f"\n验证结果: {result}")
