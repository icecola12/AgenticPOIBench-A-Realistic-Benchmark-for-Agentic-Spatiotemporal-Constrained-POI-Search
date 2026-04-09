"""
修改任务指令：你想在附近2500米以内找一家电影院。你打算骑车过去，所以骑行距离也得在2500米以内。因为你等会儿要去玉林客运中心坐车，电影院到"玉林客运中心(公交站)"步行过去不能超过40分钟。另外为了下车后方便换乘，电影院附近1200米范围里要能找到公交站，并且从电影院走到这些公交站里最近的那个，步行距离不能超过1000米，同时电影院到附近这些公交站的最近直线距离也不能超过60米。你还需要开车去接朋友，所以从你这里开车到电影院的距离不能超过2公里。你情绪化，时而冷静时而愤怒，态度变化快。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2500米以内：调用 maps_around_search(location='110.152134,22.616571', radius='2500', keywords='电影院')，验证返回pois中包含目标POI id='B0FFHO4GJZ'。  
2) 最大骑行距离2500米：先调用 maps_search_detail('B0FFHO4GJZ') 取目标坐标destination；再调用 maps_bicycling_by_coordinates(origin='110.152134,22.616571', destination=destination)，验证 total_distance_meters ≤ 2500。  
3) 最大驾车距离2公里：调用 maps_driving_by_coordinates(origin='110.152134,22.616571', destination=destination)，验证 total_distance_meters ≤ 2000。  
4) 到指定公交站(玉林客运中心公交站)步行时间≤40分钟：result = maps_geo(address="玉林客运中心(公交站)", city="玉林") 获取坐标；调用 maps_walking_by_coordinates(origin=destination, destination=公交站坐标)，验证 total_duration_seconds ≤ 2400。  
5) 目标附近1200米内要有公交站：调用 maps_around_search(location=destination, radius='1200', keywords='公交站')，验证 pois 数量 ≥ 1。  
6) 到附近1200米内公交站的最小步行距离≤1000米：对第5步返回的所有公交站POI，逐个调用 maps_walking_by_coordinates(origin=destination, destination=bus_stop_location)，取 total_distance_meters 的最小值 min_walk_dist，验证 min_walk_dist ≤ 1000。  
7) 到附近1200米内公交站的最小直线距离≤60米：对第5步返回的所有公交站POI，调用 maps_distance(origins=所有bus_stop_location用'|'拼接, destination=destination)，取 distance_meters 的最小值 min_line_dist，验证 min_line_dist ≤ 60。
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
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates,
    maps_geo,
    maps_walking_by_coordinates,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.152134,22.616571",
    search_radius: int = 2500,
    keywords: str = "电影院",
    max_bicycling_distance: int = 2500,  # 2500米
    max_driving_distance: int = 2000,  # 2公里 = 2000米
    bus_center_address: str = "玉林客运中心(公交站)",
    bus_center_city: str = "玉林",
    max_walking_duration_to_bus_center: int = 2400,  # 40分钟 = 2400秒
    bus_stop_search_radius: int = 1200,
    bus_stop_keywords: str = "公交站",
    max_walk_dist_to_bus_stop: int = 1000,  # 1000米
    max_line_dist_to_bus_stop: int = 60,  # 60米
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近2500米以内：maps_around_search，验证返回pois中包含目标poi_id。
    2) 最大骑行距离2500米：maps_search_detail 取目标坐标，maps_bicycling_by_coordinates 验证 total_distance_meters ≤ 2500。
    3) 最大驾车距离2公里：maps_driving_by_coordinates 验证 total_distance_meters ≤ 2000。
    4) 到玉林客运中心(公交站)步行时间≤40分钟：maps_geo 获取公交站坐标，maps_walking_by_coordinates 验证 total_duration_seconds ≤ 2400。
    5) 目标附近1200米内要有公交站：maps_around_search 验证 pois 数量 ≥ 1。
    6) 到附近1200米内公交站的最小步行距离≤1000米：对每个公交站算步行距离，取最小值，验证 ≤ 1000。
    7) 到附近1200米内公交站的最小直线距离≤60米：maps_distance(origins=公交站坐标用'|'拼接, destination=电影院)，取最小值，验证 ≤ 60。

    Args:
        poi_id: POI ID，默认"B0FFHO4GJZ"
        user_location: 用户坐标，默认"110.152134,22.616571"
        search_radius: 搜索半径（米），默认2500
        keywords: 搜索关键词，默认"电影院"
        max_bicycling_distance: 最大骑行距离（米），默认2500
        max_driving_distance: 最大驾车距离（米），默认2000（2公里）
        bus_center_address: 指定公交站地址，默认"玉林客运中心(公交站)"
        bus_center_city: 指定公交站城市，默认"玉林"
        max_walking_duration_to_bus_center: 到指定公交站最大步行时间（秒），默认2400（40分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认1200
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_walk_dist_to_bus_stop: 到最近公交站最大步行距离（米），默认1000
        max_line_dist_to_bus_stop: 到最近公交站最大直线距离（米），默认60

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2500米范围验证
    # 注意：首个约束应该为"你想找一个附近指定距离的poi点"，而非"你想找一个离你不超过指定距离的poi点"
    print(f"【步骤1】验证附近范围（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索附近POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois:
        print(f"❌ 未找到符合条件的POI")
        return False

    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 获取电影院坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI详情中没有location信息")
        return False

    destination = poi_detail.location
    print(f"✅ 获取电影院坐标: {destination} ({poi_detail.name})")

    # 步骤2: 最大骑行距离2500米
    print(f"\n【步骤2】验证骑行距离（≤{max_bicycling_distance}米）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=destination
    )
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（≤{max_bicycling_distance}米）")

    # 步骤3: 最大驾车距离2公里
    print(f"\n【步骤3】验证驾车距离（≤{max_driving_distance}米，即{max_driving_distance // 1000}公里）")
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=destination
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米（{max_driving_distance // 1000}公里）")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（≤{max_driving_distance}米）")

    # 步骤4: 到玉林客运中心(公交站)步行时间≤40分钟
    print(f"\n【步骤4】验证到指定公交站步行时间（≤{max_walking_duration_to_bus_center}秒，即{max_walking_duration_to_bus_center // 60}分钟）")
    print("-" * 80)
    bus_center_geo = maps_geo(address=bus_center_address, city=bus_center_city)
    if bus_center_geo.error:
        print(f"❌ 获取公交站坐标失败: {bus_center_geo.error}")
        return False

    if not bus_center_geo.results or len(bus_center_geo.results) == 0:
        print(f"❌ 未找到指定公交站地址")
        return False

    bus_center_location = bus_center_geo.results[0].location
    print(f"✅ 指定公交站坐标: {bus_center_location} ({bus_center_geo.results[0].formatted_address})")

    walk_to_bus_center_result = maps_walking_by_coordinates(
        origin=destination,
        destination=bus_center_location
    )
    if walk_to_bus_center_result.error:
        print(f"❌ 计算到指定公交站步行路线失败: {walk_to_bus_center_result.error}")
        return False

    if walk_to_bus_center_result.total_duration_seconds is None:
        print(f"❌ 无法获取到指定公交站的步行时长")
        return False

    walk_duration = walk_to_bus_center_result.total_duration_seconds
    if walk_duration > max_walking_duration_to_bus_center:
        print(f"❌ 到指定公交站步行时长{walk_duration}秒，超过{max_walking_duration_to_bus_center}秒（40分钟）")
        return False
    print(f"✅ 到指定公交站步行时长{walk_duration}秒，符合要求（≤{max_walking_duration_to_bus_center}秒）")

    # 步骤5: 目标附近1200米内要有公交站
    print(f"\n【步骤5】验证电影院{bus_stop_search_radius}米内有公交站")
    print("-" * 80)
    bus_stop_search_result = maps_around_search(
        location=destination,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) < 1:
        print(f"❌ 电影院{bus_stop_search_radius}米范围内未找到公交站")
        return False

    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")

    # 步骤6: 到附近1200米内公交站的最小步行距离≤1000米
    print(f"\n【步骤6】验证到最近公交站步行距离（≤{max_walk_dist_to_bus_stop}米）")
    print("-" * 80)
    min_walk_dist = None
    for bus_stop in bus_stop_search_result.pois:
        walk_result = maps_walking_by_coordinates(
            origin=destination,
            destination=bus_stop.location
        )
        if walk_result.error:
            print(f"⚠️  计算到公交站{bus_stop.name}的步行路线失败: {walk_result.error}")
            continue

        if walk_result.total_distance_meters is None:
            print(f"⚠️  无法获取到公交站{bus_stop.name}的步行距离")
            continue

        dist = walk_result.total_distance_meters
        if min_walk_dist is None or dist < min_walk_dist:
            min_walk_dist = dist
            print(f"  到公交站{bus_stop.name}的步行距离: {dist}米")

    if min_walk_dist is None:
        print(f"❌ 无法计算到任何公交站的步行距离")
        return False

    if min_walk_dist > max_walk_dist_to_bus_stop:
        print(f"❌ 到最近公交站步行距离{min_walk_dist}米，超过{max_walk_dist_to_bus_stop}米")
        return False
    print(f"✅ 到最近公交站步行距离{min_walk_dist}米，符合要求（≤{max_walk_dist_to_bus_stop}米）")

    # 步骤7: 到附近1200米内公交站的最小直线距离≤60米
    # maps_distance(origins=公交站坐标用'|'拼接, destination=电影院)：从各公交站到电影院的直线距离，取最小值
    print(f"\n【步骤7】验证到最近公交站直线距离（≤{max_line_dist_to_bus_stop}米）")
    print("-" * 80)
    origins_str = "|".join(bs.location for bs in bus_stop_search_result.pois)
    distance_result = maps_distance(
        origins=origins_str,
        destination=destination
    )
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离测量结果")
        return False

    min_line_dist = min(r.distance_meters for r in distance_result.results)
    if min_line_dist > max_line_dist_to_bus_stop:
        print(f"❌ 到最近公交站直线距离{min_line_dist}米，超过{max_line_dist_to_bus_stop}米")
        return False
    print(f"✅ 到最近公交站直线距离{min_line_dist}米，符合要求（≤{max_line_dist_to_bus_stop}米）")

    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 757.py <poi_id> [user_location]")
        print("示例: python 757.py B0FFHO4GJZ")
        print("示例: python 757.py B0FFHO4GJZ 110.152134,22.616571")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0FFHO4GJZ"
        user_location = "110.152134,22.616571"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "110.152134,22.616571"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)

    result = verify_poi(poi_id, user_location=user_location)

    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
