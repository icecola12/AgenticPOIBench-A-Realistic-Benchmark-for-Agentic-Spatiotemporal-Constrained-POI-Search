
"""
修改任务指令：你要在附近3000米以内找一家民宿。你打算先去民宿放行李再出门，所以从你当前位置开车到民宿的路程不要超过3公里。你还要去乐山万达广场见朋友，要求"从你当前位置出发→先到这家民宿→再到乐山万达广场"的总驾车时间不超过20分钟，而且相比你直接从当前位置开车去乐山万达广场，绕到民宿后增加的时间不要超过6分钟。民宿周边400米内必须能找到ATM。最后，这家民宿不能在"觉也·青年旅舍(乐山高铁站店)"直线距离500米范围内。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束（首要约束）：调用 maps_around_search(location=U, radius=3000, keywords='民宿')，验证返回pois中包含目标poi_id=B0L6GCTJFC。
2) 目标POI评分：调用 maps_search_detail(id='B0L6GCTJFC')，验证biz_ext.rating=4.9 ≥ 4.8。
3) 最大驾车距离（U→民宿）：调用 maps_driving_by_coordinates(origin=U, destination=目标POI坐标103.740889,29.613173)，验证 total_distance_meters ≤ 3000（实测1517m）。
4) 途径点附近有POI类型A（民宿附近有ATM）：调用 maps_around_search(location=目标POI坐标, radius=400, keywords='ATM')，验证pois数量≥1（实测2个）。
5) 总行程时间限制（U→民宿→万达广场）：
- 调用 maps_text_search(keywords='乐山万达广场', city='乐山') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取B坐标=103.737663,29.620517。
- 调用 maps_driving_by_coordinates(U→目标POI) 得到t1=181秒；调用 maps_driving_by_coordinates(目标POI→B) 得到t2（按实际调用结果计）。验证 (t1+t2) ≤ 1200秒（20分钟）。
6) 绕行增量时间限制（相比U→万达广场直达）：调用 maps_driving_by_coordinates(U→B) 得到t_direct；验证 (t1+t2) - t_direct ≤ 360秒（6分钟）。
7) 不在其他地点附近：
- 调用 maps_text_search(keywords='觉也·青年旅舍(乐山高铁站店)', city='乐山', citylimit='true') 得到其poi_id='B0J2TH451G'，再调用 maps_search_detail(id='B0J2TH451G') 得到其坐标H=103.727007,29.601438。
- 调用 maps_distance(origins=H, destination=目标POI坐标) 验证直线距离 > 500米（实测1873m）。
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
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "103.74745,29.612762",  # 默认使用万达广场坐标作为起点
    search_radius: int = 3000,
    keywords: str = "民宿",
    min_rating: float = 4.8,
    max_driving_distance: int = 3000,  # 3 km = 3000 meters
    atm_search_radius: int = 400,
    atm_keywords: str = "ATM",
    min_atm_count: int = 1,
    destination_name: str = "乐山万达广场",
    city: str = "乐山",
    max_total_duration: int = 1200,  # 20 minutes = 1200 seconds
    max_detour_increment: int = 360,  # 6 minutes = 360 seconds
    exclusion_place_name: str = "觉也·青年旅舍(乐山高铁站店)",
    min_exclusion_distance: int = 500  # 500 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边约束（首要约束）：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 目标POI评分：调用 maps_search_detail，验证biz_ext.rating ≥ 4.8。
    3) 最大驾车距离（U→民宿）：调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 3000。
    4) 途径点附近有POI类型A（民宿附近有ATM）：调用 maps_around_search，验证pois数量≥1。
    5) 总行程时间限制（U→民宿→万达广场）：调用 maps_text_search + maps_search_detail 和 maps_driving_by_coordinates，验证 (t1+t2) ≤ 1200秒。
    6) 绕行增量时间限制（相比U→万达广场直达）：调用 maps_driving_by_coordinates，验证 (t1+t2) - t_direct ≤ 360秒。
    7) 不在其他地点附近：调用 maps_text_search 和 maps_distance，验证直线距离 > 500米。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"103.737663,29.620517"
        search_radius: 搜索半径（米），默认3000
        keywords: 搜索关键词，默认"民宿"
        min_rating: 最低评分，默认4.8
        max_driving_distance: 最大驾车距离（米），默认3000
        atm_search_radius: ATM搜索半径（米），默认400
        atm_keywords: ATM搜索关键词，默认"ATM"
        min_atm_count: 最小ATM数量，默认1
        destination_name: 目的地名称，默认"乐山万达广场"
        city: 城市名称，默认"乐山"
        max_total_duration: 最大总行程时间（秒），默认1200（20分钟）
        max_detour_increment: 最大绕行增加时间（秒），默认360（6分钟）
        exclusion_place_name: 排除地点名称，默认"觉也·青年旅舍(乐山高铁站店)"
        min_exclusion_distance: 最小排除距离（米），默认500

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边约束（首要约束）
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

    # 步骤2: 目标POI评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分
    if poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = float(poi_detail.biz_ext['rating'])
        if rating < min_rating:
            print(f"❌ POI评分{rating}分，低于{min_rating}分")
            return False
        print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")
    else:
        print(f"❌ POI没有评分信息")
        return False

    # 步骤3: 最大驾车距离（U→民宿）≤3000米
    driving_to_poi_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_to_poi_result.error:
        print(f"❌ 计算到民宿驾车路线失败: {driving_to_poi_result.error}")
        return False

    if driving_to_poi_result.total_distance_meters is None:
        print(f"❌ 无法获取到民宿驾车距离")
        return False

    if driving_to_poi_result.total_duration_seconds is None:
        print(f"❌ 无法获取到民宿驾车时长")
        return False

    driving_to_poi_distance = driving_to_poi_result.total_distance_meters
    driving_to_poi_duration = driving_to_poi_result.total_duration_seconds
    if driving_to_poi_distance > max_driving_distance:
        print(f"❌ 到民宿驾车距离{driving_to_poi_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 到民宿驾车距离{driving_to_poi_distance}米，符合要求（<= {max_driving_distance}米）")
    print(f"✅ 到民宿驾车时长{driving_to_poi_duration}秒")

    # 步骤4: 途径点附近有POI类型A（民宿附近有ATM）
    atm_search_result = maps_around_search(
        location=poi_location,
        radius=str(atm_search_radius),
        keywords=atm_keywords
    )
    if atm_search_result.error:
        print(f"❌ 搜索ATM失败: {atm_search_result.error}")
        return False

    atm_count = len(atm_search_result.pois) if atm_search_result.pois else 0
    if atm_count < min_atm_count:
        print(f"❌ 民宿周边{atm_search_radius}米内找到{atm_count}个ATM，少于{min_atm_count}个")
        return False
    print(f"✅ 民宿周边{atm_search_radius}米内找到{atm_count}个ATM，符合要求（>= {min_atm_count}个）")

    # 步骤5: 总行程时间限制（U→民宿→万达广场）≤20分钟
    destination_text_search_result = maps_text_search(keywords=destination_name, city=city)
    if destination_text_search_result.error:
        print(f"❌ 获取{destination_name}坐标失败: {destination_text_search_result.error}")
        return False

    if not destination_text_search_result.pois or len(destination_text_search_result.pois) == 0:
        print(f"❌ 未找到{destination_name}坐标")
        return False

    destination_poi_id = destination_text_search_result.pois[0].id
    destination_detail_result = maps_search_detail(id=destination_poi_id)
    if destination_detail_result.error:
        print(f"❌ 获取{destination_name}详情失败: {destination_detail_result.error}")
        return False
    if not destination_detail_result.location:
        print(f"❌ {destination_name}没有location信息")
        return False
    destination_location = destination_detail_result.location
    print(f"✅ 获取{destination_name}坐标: {destination_location}")

    # 计算民宿→万达广场的驾车时间
    driving_poi_to_dest_result = maps_driving_by_coordinates(origin=poi_location, destination=destination_location)
    if driving_poi_to_dest_result.error:
        print(f"❌ 计算民宿到{destination_name}驾车路线失败: {driving_poi_to_dest_result.error}")
        return False

    if driving_poi_to_dest_result.total_duration_seconds is None:
        print(f"❌ 无法获取民宿到{destination_name}驾车时长")
        return False

    driving_poi_to_dest_duration = driving_poi_to_dest_result.total_duration_seconds
    total_duration = driving_to_poi_duration + driving_poi_to_dest_duration
    if total_duration > max_total_duration:
        print(f"❌ 总行程时间{total_duration}秒（{total_duration / 60:.2f}分钟），超过{max_total_duration}秒（{max_total_duration // 60}分钟）")
        return False
    print(f"✅ 总行程时间{total_duration}秒（{total_duration / 60:.2f}分钟），符合要求（<= {max_total_duration}秒，即{max_total_duration // 60}分钟）")

    # 步骤6: 绕行增量时间限制（相比U→万达广场直达）≤6分钟
    direct_driving_result = maps_driving_by_coordinates(origin=user_location, destination=destination_location)
    if direct_driving_result.error:
        print(f"❌ 计算直接到{destination_name}驾车路线失败: {direct_driving_result.error}")
        return False

    if direct_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取直接到{destination_name}驾车时长")
        return False

    direct_duration = direct_driving_result.total_duration_seconds
    detour_increment = total_duration - direct_duration
    if detour_increment > max_detour_increment:
        print(f"❌ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），超过{max_detour_increment}秒（{max_detour_increment // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），符合要求（<= {max_detour_increment}秒，即{max_detour_increment // 60}分钟）")

    # 步骤7: 不在其他地点附近（>500米）
    exclusion_search_result = maps_text_search(
        keywords=exclusion_place_name,
        city=city,
        citylimit="true"
    )
    if exclusion_search_result.error:
        print(f"❌ 搜索{exclusion_place_name}失败: {exclusion_search_result.error}")
        return False

    if not exclusion_search_result.pois or len(exclusion_search_result.pois) == 0:
        print(f"❌ 未找到{exclusion_place_name}")
        return False

    # 获取排除地点详情以获取坐标
    exclusion_poi_id = exclusion_search_result.pois[0].id
    exclusion_detail = maps_search_detail(id=exclusion_poi_id)
    if exclusion_detail.error:
        print(f"❌ 获取{exclusion_place_name}详情失败: {exclusion_detail.error}")
        return False

    if not exclusion_detail.location:
        print(f"❌ {exclusion_place_name}没有location信息")
        return False

    exclusion_location = exclusion_detail.location
    print(f"✅ 获取{exclusion_place_name}坐标: {exclusion_location}")

    # 计算直线距离
    distance_result = maps_distance(origins=exclusion_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算到{exclusion_place_name}距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到到{exclusion_place_name}的距离信息")
        return False

    exclusion_distance = distance_result.results[0].distance_meters
    if exclusion_distance <= min_exclusion_distance:
        print(f"❌ 到{exclusion_place_name}直线距离{exclusion_distance}米，不大于{min_exclusion_distance}米")
        return False
    print(f"✅ 到{exclusion_place_name}直线距离{exclusion_distance}米，符合要求（> {min_exclusion_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 844.py 文件...\n")
    result = verify_poi(poi_id="B0L6GCTJFC")
    print(f"\n验证结果: {result}")

