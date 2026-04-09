"""
修改任务指令：你想在附近5000米以内找一家网吧。你打算步行过去，所以步行距离不能超过2000米。你还要赶去广州塔，从你这里出发，经由这家网吧再到广州塔的总步行时间不能超过130分钟，并且相比你直接步行去广州塔，总耗时增加不能超过20分钟。另外，这家网吧到"车陂南(地铁站)"的步行时间要在30分钟内；同时网吧周边3000米范围内的地铁站里，离网吧最近的那个站，直线距离不能超过1600米、步行距离不能超过1300米。最后，你从你这里走到网吧的路上，找一个中途经过的点，在这个途径点200米内必须能找到便利店。你善于使用强制和协商的策略来达到目的。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近5000米内网吧：调用 maps_around_search(location='113.419815,23.116299', radius='5000', keywords='网吧')，验证返回pois里包含 id='B0LR0SMK8N'。
2) 从出发点步行到网吧距离≤2000米：先调用 maps_search_detail(id='B0LR0SMK8N') 获取网吧坐标 destination；调用 maps_walking_by_coordinates(origin='113.419815,23.116299', destination=destination)，验证 total_distance_meters ≤ 2000。
3) 经由网吧到广州塔总步行时间≤130分钟：调用 maps_geo(address='广州塔', city='广州') 获取广州塔坐标 B；调用 maps_walking_by_coordinates(origin='113.419815,23.116299', destination=destination) 得到 t_A_to_P；调用 maps_walking_by_coordinates(origin=destination, destination=B) 得到 t_P_to_B；验证 (t_A_to_P + t_P_to_B) / 60 ≤ 130。
4) 经由网吧到广州塔相对直达广州塔，增加耗时≤20分钟：调用 maps_walking_by_coordinates(origin='113.419815,23.116299', destination=B) 得到 t_A_to_B；验证 ((t_A_to_P + t_P_to_B) - t_A_to_B) / 60 ≤ 20。
5) 网吧到"车陂南(地铁站)"步行时间≤30分钟：调用 maps_text_search(keywords='车陂南地铁站', city='广州', citylimit='true')，选取POI '车陂南(地铁站)'（id='BV10014566'）；调用 maps_search_detail(id='BV10014566') 获取其坐标 S；调用 maps_walking_by_coordinates(origin=destination, destination=S)；验证 total_duration_seconds / 60 ≤ 30。
6) 网吧周边3000米内地铁站集合：最近站直线距离≤1600米：调用 maps_around_search(location=destination, radius='3000', keywords='地铁站') 获取地铁站列表 stations；对每个station调用 maps_distance(origins=station.location, destination=destination)，取最小直线距离 d_min；验证 d_min ≤ 1600。
7) 网吧周边3000米内地铁站集合：最近站步行距离≤1300米：对第6步中取得d_min对应的最近站 station_nearest；调用 maps_walking_by_coordinates(origin=destination, destination=station_nearest.location)；验证 total_distance_meters ≤ 1300。
8) 途径点附近200米内有便利店（途径点取A->P步行路线第1个step的to_coordinates）：调用 maps_walking_by_coordinates(origin='113.419815,23.116299', destination=destination) 获取 steps；取 waypoint = steps[0].to_coordinates；调用 maps_around_search(location=waypoint, radius='200', keywords='便利店')；验证返回pois数量 > 0。
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
    maps_geo,
    maps_text_search,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "113.419815,23.116299",
    netbar_location: str = "",
    search_radius: int = 5000,
    keywords: str = "网吧",
    max_walking_distance: int = 2000,
    guangzhou_tower_address: str = "广州塔",
    city: str = "广州",
    max_total_via_duration_seconds: int = 7800,  # 130分钟 = 7800秒
    max_extra_duration_seconds: int = 1200,  # 20分钟 = 1200秒
    chebei_subway_keywords: str = "车陂南地铁站",
    max_walking_duration_to_chebei: int = 1800,  # 30分钟 = 1800秒
    subway_search_radius: int = 3000,
    subway_keywords: str = "地铁站",
    max_line_dist_to_subway: int = 1600,
    max_walking_distance_to_subway: int = 1300,
    waypoint_convenience_radius: int = 200,
    convenience_keywords: str = "便利店",
) -> bool:
    """
    验证POI（网吧）是否符合要求。

    验证步骤：
    1) 附近5000米内网吧：maps_around_search，验证返回pois里包含目标poi_id。
    2) 从出发点步行到网吧距离≤2000米：maps_search_detail 取网吧坐标，maps_walking_by_coordinates 验证 total_distance_meters ≤ 2000。
    3) 经由网吧到广州塔总步行时间≤130分钟：maps_geo 得广州塔坐标，算 t_A_to_P + t_P_to_B ≤ 7800秒。
    4) 经由网吧相对直达增加耗时≤20分钟：算 (t_A_to_P + t_P_to_B) - t_A_to_B ≤ 1200秒。
    5) 网吧到车陂南(地铁站)步行时间≤30分钟：maps_text_search + maps_search_detail 得坐标，maps_walking_by_coordinates ≤ 1800秒。
    6) 网吧周边3000米内地铁站：最近站直线距离≤1600米。
    7) 最近站步行距离≤1300米。
    8) 途径点（A->P 第1个 step 的 to_coordinates）附近200米内有便利店。

    Args:
        poi_id: POI ID，默认"B0LR0SMK8N"
        user_location: 用户坐标，默认"113.419815,23.116299"
        netbar_location: 网吧坐标（从 detail 获取后可覆盖），默认空
        search_radius: 搜索半径（米），默认5000
        keywords: 搜索关键词，默认"网吧"
        max_walking_distance: 用户到网吧最大步行距离（米），默认2000
        guangzhou_tower_address: 广州塔地址，默认"广州塔"
        city: 城市，默认"广州"
        max_total_via_duration_seconds: 经由网吧到广州塔最大总时长（秒），默认7800（130分钟）
        max_extra_duration_seconds: 经由相对直达最大增加时长（秒），默认1200（20分钟）
        chebei_subway_keywords: 车陂南地铁站搜索关键词，默认"车陂南地铁站"
        max_walking_duration_to_chebei: 网吧到车陂南地铁站最大步行时间（秒），默认1800（30分钟）
        subway_search_radius: 地铁站搜索半径（米），默认3000
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_line_dist_to_subway: 到最近地铁站最大直线距离（米），默认1600
        max_walking_distance_to_subway: 到最近地铁站最大步行距离（米），默认1300
        waypoint_convenience_radius: 途径点便利店搜索半径（米），默认200
        convenience_keywords: 便利店搜索关键词，默认"便利店"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近5000米内网吧
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

    # 步骤2: 获取网吧坐标并验证用户到网吧步行距离≤2000米
    print(f"\n【步骤2】验证从出发点步行到网吧距离（≤{max_walking_distance}米）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI详情中没有location信息")
        return False

    netbar_location = poi_detail.location
    print(f"✅ 网吧坐标: {netbar_location} ({poi_detail.name})")

    walk_to_netbar = maps_walking_by_coordinates(
        origin=user_location,
        destination=netbar_location
    )
    if walk_to_netbar.error:
        print(f"❌ 计算到网吧步行路线失败: {walk_to_netbar.error}")
        return False

    if walk_to_netbar.total_distance_meters is None:
        print(f"❌ 无法获取到网吧步行距离")
        return False

    if walk_to_netbar.total_distance_meters > max_walking_distance:
        print(f"❌ 到网吧步行距离{walk_to_netbar.total_distance_meters}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 到网吧步行距离{walk_to_netbar.total_distance_meters}米，符合要求（≤{max_walking_distance}米）")

    t_a_to_p = walk_to_netbar.total_duration_seconds  # 用于步骤3、4

    # 步骤3: 经由网吧到广州塔总步行时间≤130分钟
    print(f"\n【步骤3】验证经由网吧到广州塔总步行时间（≤{max_total_via_duration_seconds // 60}分钟）")
    print("-" * 80)
    geo_tower = maps_geo(address=guangzhou_tower_address, city=city)
    if geo_tower.error or not geo_tower.results:
        print(f"❌ 地理编码广州塔失败: {geo_tower.error or '无结果'}")
        return False

    tower_location = geo_tower.results[0].location
    print(f"✅ 广州塔坐标: {tower_location}")

    walk_netbar_to_tower = maps_walking_by_coordinates(
        origin=netbar_location,
        destination=tower_location
    )
    if walk_netbar_to_tower.error or walk_netbar_to_tower.total_duration_seconds is None:
        print(f"❌ 计算网吧到广州塔步行时间失败")
        return False

    t_p_to_b = walk_netbar_to_tower.total_duration_seconds
    total_via = t_a_to_p + t_p_to_b
    if total_via > max_total_via_duration_seconds:
        print(f"❌ 经由网吧到广州塔总步行时间{total_via}秒（{total_via // 60}分钟），超过{max_total_via_duration_seconds}秒（130分钟）")
        return False
    print(f"✅ 经由网吧到广州塔总步行时间{total_via}秒（{total_via // 60}分钟），符合要求")

    # 步骤4: 经由网吧相对直达增加耗时≤20分钟
    print(f"\n【步骤4】验证经由网吧相对直达增加耗时（≤{max_extra_duration_seconds // 60}分钟）")
    print("-" * 80)
    walk_direct = maps_walking_by_coordinates(
        origin=user_location,
        destination=tower_location
    )
    if walk_direct.error or walk_direct.total_duration_seconds is None:
        print(f"❌ 计算直达广州塔步行时间失败")
        return False

    t_a_to_b = walk_direct.total_duration_seconds
    extra = total_via - t_a_to_b
    if extra > max_extra_duration_seconds:
        print(f"❌ 经由网吧相对直达增加耗时{extra}秒（{extra // 60}分钟），超过{max_extra_duration_seconds}秒（20分钟）")
        return False
    print(f"✅ 经由网吧相对直达增加耗时{extra}秒（{extra // 60}分钟），符合要求")

    # 步骤5: 网吧到车陂南(地铁站)步行时间≤30分钟
    print(f"\n【步骤5】验证网吧到车陂南(地铁站)步行时间（≤{max_walking_duration_to_chebei // 60}分钟）")
    print("-" * 80)
    chebei_search = maps_text_search(
        keywords=chebei_subway_keywords,
        city=city,
        citylimit="true"
    )
    if chebei_search.error or not chebei_search.pois:
        print(f"❌ 文本搜索车陂南地铁站失败或无结果")
        return False

    chebei_poi_id = chebei_search.pois[0].id
    print(f"✅ 车陂南(地铁站) POI id: {chebei_poi_id} ({chebei_search.pois[0].name})")

    chebei_detail = maps_search_detail(id=chebei_poi_id)
    if chebei_detail.error or not chebei_detail.location:
        print(f"❌ 获取车陂南地铁站坐标失败")
        return False

    chebei_location = chebei_detail.location
    walk_to_chebei = maps_walking_by_coordinates(
        origin=netbar_location,
        destination=chebei_location
    )
    if walk_to_chebei.error or walk_to_chebei.total_duration_seconds is None:
        print(f"❌ 计算到车陂南地铁站步行时间失败")
        return False

    if walk_to_chebei.total_duration_seconds > max_walking_duration_to_chebei:
        print(f"❌ 到车陂南地铁站步行时间{walk_to_chebei.total_duration_seconds}秒，超过{max_walking_duration_to_chebei}秒（30分钟）")
        return False
    print(f"✅ 到车陂南地铁站步行时间{walk_to_chebei.total_duration_seconds}秒，符合要求（≤30分钟）")

    # 步骤6: 网吧周边3000米内地铁站，最近站直线距离≤1600米
    print(f"\n【步骤6】验证网吧周边{subway_search_radius}米内地铁站最近站直线距离（≤{max_line_dist_to_subway}米）")
    print("-" * 80)
    subway_search_result = maps_around_search(
        location=netbar_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 网吧{subway_search_radius}米范围内未找到地铁站")
        return False

    d_min = None
    station_nearest = None
    for station in subway_search_result.pois:
        if not station.location:
            continue
        dist_result = maps_distance(
            origins=station.location,
            destination=netbar_location
        )
        if dist_result.error or not dist_result.results:
            continue
        d = dist_result.results[0].distance_meters
        if d_min is None or d < d_min:
            d_min = d
            station_nearest = station

    if d_min is None or station_nearest is None:
        print(f"❌ 无法计算到任一地铁站的直线距离")
        return False

    if d_min > max_line_dist_to_subway:
        print(f"❌ 到最近地铁站直线距离{d_min}米，超过{max_line_dist_to_subway}米")
        return False
    print(f"✅ 到最近地铁站直线距离{d_min}米，符合要求（≤{max_line_dist_to_subway}米）")

    # 步骤7: 最近站步行距离≤1300米
    print(f"\n【步骤7】验证到最近地铁站步行距离（≤{max_walking_distance_to_subway}米）")
    print("-" * 80)
    walk_to_nearest_subway = maps_walking_by_coordinates(
        origin=netbar_location,
        destination=station_nearest.location
    )
    if walk_to_nearest_subway.error or walk_to_nearest_subway.total_distance_meters is None:
        print(f"❌ 计算到最近地铁站步行距离失败")
        return False

    if walk_to_nearest_subway.total_distance_meters > max_walking_distance_to_subway:
        print(f"❌ 到最近地铁站步行距离{walk_to_nearest_subway.total_distance_meters}米，超过{max_walking_distance_to_subway}米")
        return False
    print(f"✅ 到最近地铁站步行距离{walk_to_nearest_subway.total_distance_meters}米，符合要求（≤{max_walking_distance_to_subway}米）")

    # 步骤8: 途径点附近200米内有便利店
    print(f"\n【步骤8】验证途径点附近{waypoint_convenience_radius}米内有便利店")
    print("-" * 80)
    if not walk_to_netbar.steps or len(walk_to_netbar.steps) == 0:
        print(f"❌ 到网吧步行路线无 steps 信息")
        return False

    waypoint = walk_to_netbar.steps[0].to_coordinates
    print(f"✅ 途径点坐标（第1个 step 的 to_coordinates）: {waypoint}")

    convenience_search = maps_around_search(
        location=waypoint,
        radius=str(waypoint_convenience_radius),
        keywords=convenience_keywords
    )
    if convenience_search.error:
        print(f"❌ 搜索便利店失败: {convenience_search.error}")
        return False

    if not convenience_search.pois or len(convenience_search.pois) == 0:
        print(f"❌ 途径点{waypoint_convenience_radius}米范围内未找到便利店")
        return False

    print(f"✅ 途径点{waypoint_convenience_radius}米范围内找到便利店（共{len(convenience_search.pois)}个）")

    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 761.py <poi_id> [user_location]")
        print("示例: python 761.py B0LR0SMK8N")
        print("示例: python 761.py B0LR0SMK8N 113.419815,23.116299")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0LR0SMK8N"
        user_location = "113.419815,23.116299"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "113.419815,23.116299"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)

    result = verify_poi(poi_id, user_location=user_location)

    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
