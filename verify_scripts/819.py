
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近范围：调用 maps_around_search(location='115.929528,28.70008', radius='5000', keywords='网吧')，验证返回pois中包含目标POI id='B0FFI7VYGO'。
2) 指定地铁站直线距离：调用 maps_text_search(keywords='国威路(地铁站)', city='南昌', citylimit='true') 获取该站坐标；再调用 maps_search_detail('B0FFI7VYGO') 获取网吧坐标；调用 maps_distance(origins=网吧坐标, destination=地铁站坐标) 验证直线距离≤900米。
3) 800米内地铁站最短步行时间：调用 maps_around_search(location=网吧坐标, radius='800', keywords='地铁站') 获取候选地铁站列表；对每个地铁站调用 maps_walking_by_coordinates(origin=网吧坐标, destination=地铁站坐标) 取最小total_duration_seconds，验证≤480秒(8分钟)。
4) 用户到网吧最大驾车距离：调用 maps_search_detail('B0FFI7VYGO') 获取网吧坐标；调用 maps_driving_by_coordinates(origin='115.929528,28.70008', destination=网吧坐标) 验证 total_distance_meters≤3000米。
5) 朋友(起凤路地铁站)到网吧骑行距离：调用 maps_text_search(keywords='起凤路(地铁站)', city='南昌', citylimit='true') 获取起凤路站坐标；调用 maps_bicycling_by_coordinates(origin=起凤路站坐标, destination=网吧坐标) 验证 total_distance_meters≤3000米。
6) 网吧到指定POI"鸿瑞网咖"驾车时间：调用 maps_text_search(keywords='鸿瑞网咖', city='南昌', citylimit='true') 获取"鸿瑞网咖"坐标（或在周边搜索结果中取其POI）；调用 maps_driving_by_coordinates(origin=网吧坐标, destination=鸿瑞网咖坐标) 验证 total_duration_seconds≤420秒(7分钟)。
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
    maps_text_search,
    maps_distance,
    maps_driving_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.929528,28.70008",
    search_radius: int = 5000,
    keywords: str = "网吧",
    specific_subway_name: str = "国威路(地铁站)",
    city: str = "南昌",
    max_specific_subway_distance: int = 900,  # 900 meters
    subway_search_radius: int = 800,
    subway_keywords: str = "地铁站",
    max_subway_walking_duration: int = 480,  # 8 minutes = 480 seconds
    max_driving_distance: int = 3000,  # 3000 meters
    friend_subway_name: str = "起凤路(地铁站)",
    max_friend_bicycling_distance: int = 3000,  # 3000 meters
    target_poi_name: str = "鸿瑞网咖",
    max_target_driving_duration: int = 420  # 7 minutes = 420 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近范围：调用 maps_around_search，验证返回pois中包含目标POI。
    2) 指定地铁站直线距离：调用 maps_text_search 获取地铁站坐标，调用 maps_search_detail 获取网吧坐标，调用 maps_distance 验证直线距离≤900米。
    3) 800米内地铁站最短步行时间：调用 maps_around_search 获取候选地铁站列表，对每个地铁站调用 maps_walking_by_coordinates，取最小值，验证≤480秒。
    4) 用户到网吧最大驾车距离：调用 maps_search_detail 获取网吧坐标，调用 maps_driving_by_coordinates 验证≤3000米。
    5) 朋友(起凤路地铁站)到网吧骑行距离：调用 maps_text_search 获取起凤路站坐标，调用 maps_bicycling_by_coordinates 验证≤3000米。
    6) 网吧到指定POI"鸿瑞网咖"驾车时间：调用 maps_text_search 获取"鸿瑞网咖"坐标，调用 maps_driving_by_coordinates 验证≤420秒。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.929528,28.70008"
        search_radius: 搜索半径（米），默认5000
        keywords: 搜索关键词，默认"网吧"
        specific_subway_name: 指定地铁站名称，默认"国威路(地铁站)"
        city: 城市名称，默认"南昌"
        max_specific_subway_distance: 到指定地铁站最大直线距离（米），默认900
        subway_search_radius: 地铁站搜索半径（米），默认800
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_subway_walking_duration: 到地铁站最大步行时长（秒），默认480（8分钟）
        max_driving_distance: 最大驾车距离（米），默认3000
        friend_subway_name: 朋友所在地铁站名称，默认"起凤路(地铁站)"
        max_friend_bicycling_distance: 朋友最大骑行距离（米），默认3000
        target_poi_name: 目标POI名称，默认"鸿瑞网咖"
        max_target_driving_duration: 到目标POI最大驾车时长（秒），默认420（7分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近范围
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

    # 步骤3: 指定地铁站直线距离≤900米
    specific_subway_search_result = maps_text_search(
        keywords=specific_subway_name,
        city=city,
        citylimit="true"
    )
    if specific_subway_search_result.error:
        print(f"❌ 搜索{specific_subway_name}失败: {specific_subway_search_result.error}")
        return False

    if not specific_subway_search_result.pois or len(specific_subway_search_result.pois) == 0:
        print(f"❌ 未找到{specific_subway_name}")
        return False

    # 获取地铁站详情以获取坐标
    specific_subway_id = specific_subway_search_result.pois[0].id
    specific_subway_detail = maps_search_detail(id=specific_subway_id)
    if specific_subway_detail.error:
        print(f"❌ 获取{specific_subway_name}详情失败: {specific_subway_detail.error}")
        return False

    if not specific_subway_detail.location:
        print(f"❌ {specific_subway_name}没有location信息")
        return False

    specific_subway_location = specific_subway_detail.location
    print(f"✅ 获取{specific_subway_name}坐标: {specific_subway_location}")

    specific_distance_result = maps_distance(origins=poi_location, destination=specific_subway_location)
    if specific_distance_result.error:
        print(f"❌ 计算到{specific_subway_name}距离失败: {specific_distance_result.error}")
        return False

    if not specific_distance_result.results or len(specific_distance_result.results) == 0:
        print(f"❌ 未获取到到{specific_subway_name}的距离信息")
        return False

    specific_distance = specific_distance_result.results[0].distance_meters
    if specific_distance > max_specific_subway_distance:
        print(f"❌ 到{specific_subway_name}直线距离{specific_distance}米，超过{max_specific_subway_distance}米")
        return False
    print(f"✅ 到{specific_subway_name}直线距离{specific_distance}米，符合要求（<= {max_specific_subway_distance}米）")

    # 步骤4: 800米内地铁站最短步行时间≤480秒
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False

    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")

    # 计算到每个地铁站的步行时间，找到最小值
    min_subway_walking_duration = None
    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        subway_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=subway.location
        )
        if subway_walking_result.error or subway_walking_result.total_duration_seconds is None:
            continue

        duration = subway_walking_result.total_duration_seconds
        if min_subway_walking_duration is None or duration < min_subway_walking_duration:
            min_subway_walking_duration = duration

    if min_subway_walking_duration is None:
        print(f"❌ 无法计算到地铁站的步行时间")
        return False

    if min_subway_walking_duration > max_subway_walking_duration:
        print(f"❌ 到最近地铁站步行时长{min_subway_walking_duration}秒，超过{max_subway_walking_duration}秒（{max_subway_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到最近地铁站步行时长{min_subway_walking_duration}秒，符合要求（<= {max_subway_walking_duration}秒，即{max_subway_walking_duration // 60}分钟）")

    # 步骤5: 用户到网吧最大驾车距离≤3000米
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")

    # 步骤6: 朋友(起凤路地铁站)到网吧骑行距离≤3000米
    friend_subway_search_result = maps_text_search(
        keywords=friend_subway_name,
        city=city,
        citylimit="true"
    )
    if friend_subway_search_result.error:
        print(f"❌ 搜索{friend_subway_name}失败: {friend_subway_search_result.error}")
        return False

    if not friend_subway_search_result.pois or len(friend_subway_search_result.pois) == 0:
        print(f"❌ 未找到{friend_subway_name}")
        return False

    # 获取地铁站详情以获取坐标
    friend_subway_id = friend_subway_search_result.pois[0].id
    friend_subway_detail = maps_search_detail(id=friend_subway_id)
    if friend_subway_detail.error:
        print(f"❌ 获取{friend_subway_name}详情失败: {friend_subway_detail.error}")
        return False

    if not friend_subway_detail.location:
        print(f"❌ {friend_subway_name}没有location信息")
        return False

    friend_subway_location = friend_subway_detail.location
    print(f"✅ 获取{friend_subway_name}坐标: {friend_subway_location}")

    friend_bicycling_result = maps_bicycling_by_coordinates(origin=friend_subway_location, destination=poi_location)
    if friend_bicycling_result.error:
        print(f"❌ 计算从{friend_subway_name}骑行路线失败: {friend_bicycling_result.error}")
        return False

    if friend_bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取从{friend_subway_name}骑行距离")
        return False

    friend_bicycling_distance = friend_bicycling_result.total_distance_meters
    if friend_bicycling_distance > max_friend_bicycling_distance:
        print(f"❌ 从{friend_subway_name}骑行距离{friend_bicycling_distance}米，超过{max_friend_bicycling_distance}米")
        return False
    print(f"✅ 从{friend_subway_name}骑行距离{friend_bicycling_distance}米，符合要求（<= {max_friend_bicycling_distance}米）")

    # 步骤7: 网吧到指定POI"鸿瑞网咖"驾车时间≤420秒
    target_poi_search_result = maps_text_search(
        keywords=target_poi_name,
        city=city,
        citylimit="true"
    )
    if target_poi_search_result.error:
        print(f"❌ 搜索{target_poi_name}失败: {target_poi_search_result.error}")
        return False

    if not target_poi_search_result.pois or len(target_poi_search_result.pois) == 0:
        print(f"❌ 未找到{target_poi_name}")
        return False

    # 获取目标POI详情以获取坐标
    target_poi_id = target_poi_search_result.pois[0].id
    target_poi_detail = maps_search_detail(id=target_poi_id)
    if target_poi_detail.error:
        print(f"❌ 获取{target_poi_name}详情失败: {target_poi_detail.error}")
        return False

    if not target_poi_detail.location:
        print(f"❌ {target_poi_name}没有location信息")
        return False

    target_poi_location = target_poi_detail.location
    print(f"✅ 获取{target_poi_name}坐标: {target_poi_location}")

    target_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=target_poi_location)
    if target_driving_result.error:
        print(f"❌ 计算到{target_poi_name}驾车路线失败: {target_driving_result.error}")
        return False

    if target_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{target_poi_name}驾车时长")
        return False

    target_driving_duration = target_driving_result.total_duration_seconds
    if target_driving_duration > max_target_driving_duration:
        print(f"❌ 到{target_poi_name}驾车时长{target_driving_duration}秒，超过{max_target_driving_duration}秒（{max_target_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{target_poi_name}驾车时长{target_driving_duration}秒，符合要求（<= {max_target_driving_duration}秒，即{max_target_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 819.py 文件...\n")
    result = verify_poi(poi_id="B0FFI7VYGO")
    print(f"\n验证结果: {result}")

