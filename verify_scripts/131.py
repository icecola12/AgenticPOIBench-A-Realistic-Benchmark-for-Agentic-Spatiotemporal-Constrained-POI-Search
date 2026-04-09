"""
修改任务指令：你想在附近2000米以内找一家酒吧。你希望这家酒吧到你骑行过去的距离不超过1500米。另外你想把集合点定在地铁站附近：酒吧到附近800米范围内任意一个地铁站的最近直线距离不超过250米，而且从酒吧步行到"友谊南路(地铁站)"不超过12分钟。为了让外地来的朋友好打车，你还要求从"天津站"和"天津西站"出发步行到酒吧的时间差不超过20分钟。你说话简短急促，希望快速完成所有事。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米：调用 maps_around_search(location='117.216809,39.064497', radius='2000', keywords='酒吧')，验证返回pois中包含 target_poi_id='B0J2FR5W41'。  
2) 用户到酒吧骑行距离≤1500米：调用 maps_bicycling_by_coordinates(origin='117.216809,39.064497', destination=目标POI坐标)，验证 total_distance_meters ≤ 1500。  
3) 酒吧到附近800米内地铁站的最近直线距离≤250米：  
   a. 调用 maps_around_search(location=目标POI坐标, radius='800', keywords='地铁站') 获取候选地铁站列表。  
   b. 对所有候选地铁站，调用 maps_distance(origins=地铁站坐标串'lon,lat|...', destination=目标POI坐标)，取最小 distance_meters，验证 min_distance_meters ≤ 250。  
4) 酒吧到"友谊南路(地铁站)"步行时间≤12分钟：  
   a. 调用 maps_text_search(keywords='友谊南路地铁站', city='天津', citylimit='true') 得到其POI id。  
   b. 调用 maps_search_detail(id=该地铁站id) 获取地铁站坐标。  
   c. 调用 maps_walking_by_coordinates(origin=目标POI坐标, destination=地铁站坐标)，验证 total_duration_seconds ≤ 720。  
5) 从"天津站"和"天津西站"步行到酒吧的时间差≤20分钟：  
   a. 调用 maps_text_search(keywords='天津站', city='天津', citylimit='true')，再 maps_search_detail 获取天津站坐标。  
   b. 调用 maps_text_search(keywords='天津西站', city='天津', citylimit='true')，再 maps_search_detail 获取天津西站坐标。  
   c. 分别调用 maps_walking_by_coordinates(origin=天津站坐标, destination=目标POI坐标) 得到tA；调用 maps_walking_by_coordinates(origin=天津西站坐标, destination=目标POI坐标) 得到tB。  
   d. 验证 |tA - tB| ≤ 1200秒。
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
    maps_text_search,
    maps_walking_by_coordinates,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.216809,39.064497",
    search_radius: int = 2000,
    keywords: str = "酒吧",
    max_bicycling_distance: int = 1500,  # 1500米
    subway_search_radius: int = 800,
    subway_keywords: str = "地铁站",
    max_line_dist_to_subway: int = 250,  # 250米
    friendship_subway_keywords: str = "友谊南路地铁站",
    city: str = "天津",
    max_walking_duration_to_subway: int = 720,  # 12分钟 = 720秒
    station_a_keywords: str = "天津站",
    station_b_keywords: str = "天津西站",
    max_walking_time_diff_seconds: int = 1200,  # 20分钟 = 1200秒
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近2000米：maps_around_search，验证返回pois中包含目标poi_id。
    2) 用户到酒吧骑行距离≤1500米：maps_bicycling_by_coordinates 验证 total_distance_meters ≤ 1500。
    3) 酒吧到附近800米内地铁站的最近直线距离≤250米：maps_around_search 获取地铁站列表，maps_distance 取最小 distance_meters ≤ 250。
    4) 酒吧到"友谊南路(地铁站)"步行时间≤12分钟：maps_text_search 得POI id，maps_search_detail 得坐标，maps_walking_by_coordinates 验证 ≤ 720秒。
    5) 天津站与天津西站步行到酒吧的时间差≤20分钟：分别取两站坐标，算步行时间 tA、tB，验证 |tA - tB| ≤ 1200秒。

    Args:
        poi_id: POI ID，默认"B0J2FR5W41"
        user_location: 用户坐标，默认"117.216809,39.064497"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"酒吧"
        max_bicycling_distance: 最大骑行距离（米），默认1500
        subway_search_radius: 地铁站搜索半径（米），默认800
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_line_dist_to_subway: 到最近地铁站最大直线距离（米），默认250
        friendship_subway_keywords: 友谊南路地铁站搜索关键词，默认"友谊南路地铁站"
        city: 城市，默认"天津"
        max_walking_duration_to_subway: 到友谊南路地铁站最大步行时间（秒），默认720（12分钟）
        station_a_keywords: 天津站搜索关键词，默认"天津站"
        station_b_keywords: 天津西站搜索关键词，默认"天津西站"
        max_walking_time_diff_seconds: 两站到酒吧步行时间差上限（秒），默认1200（20分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2000米范围验证
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

    # 获取酒吧坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI详情中没有location信息")
        return False

    bar_location = poi_detail.location
    print(f"✅ 获取酒吧坐标: {bar_location} ({poi_detail.name})")

    # 步骤2: 用户到酒吧骑行距离≤1500米
    print(f"\n【步骤2】验证骑行距离（≤{max_bicycling_distance}米）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=bar_location
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

    # 步骤3: 酒吧到附近800米内地铁站的最近直线距离≤250米
    print(f"\n【步骤3】验证酒吧到附近{subway_search_radius}米内地铁站的最近直线距离（≤{max_line_dist_to_subway}米）")
    print("-" * 80)
    subway_search_result = maps_around_search(
        location=bar_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 酒吧{subway_search_radius}米范围内未找到地铁站")
        return False

    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")

    origins_str = "|".join(s.location for s in subway_search_result.pois if s.location)
    if not origins_str:
        print(f"❌ 地铁站无有效坐标")
        return False

    distance_result = maps_distance(
        origins=origins_str,
        destination=bar_location
    )
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离测量结果")
        return False

    min_distance_meters = min(r.distance_meters for r in distance_result.results)
    if min_distance_meters > max_line_dist_to_subway:
        print(f"❌ 到最近地铁站直线距离{min_distance_meters}米，超过{max_line_dist_to_subway}米")
        return False
    print(f"✅ 到最近地铁站直线距离{min_distance_meters}米，符合要求（≤{max_line_dist_to_subway}米）")

    # 步骤4: 酒吧到"友谊南路(地铁站)"步行时间≤12分钟
    print(f"\n【步骤4】验证酒吧到友谊南路(地铁站)步行时间（≤{max_walking_duration_to_subway}秒，即12分钟）")
    print("-" * 80)
    text_search_result = maps_text_search(
        keywords=friendship_subway_keywords,
        city=city,
        citylimit="true"
    )
    if text_search_result.error:
        print(f"❌ 文本搜索地铁站失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到友谊南路地铁站")
        return False

    friendship_subway_id = text_search_result.pois[0].id
    print(f"✅ 友谊南路地铁站 POI id: {friendship_subway_id} ({text_search_result.pois[0].name})")

    friendship_subway_detail = maps_search_detail(id=friendship_subway_id)
    if friendship_subway_detail.error:
        print(f"❌ 获取友谊南路地铁站详情失败: {friendship_subway_detail.error}")
        return False

    if not friendship_subway_detail.location:
        print(f"❌ 友谊南路地铁站无坐标")
        return False

    friendship_subway_location = friendship_subway_detail.location
    print(f"✅ 友谊南路地铁站坐标: {friendship_subway_location}")

    walk_to_subway_result = maps_walking_by_coordinates(
        origin=bar_location,
        destination=friendship_subway_location
    )
    if walk_to_subway_result.error:
        print(f"❌ 计算到友谊南路地铁站步行路线失败: {walk_to_subway_result.error}")
        return False

    if walk_to_subway_result.total_duration_seconds is None:
        print(f"❌ 无法获取到友谊南路地铁站的步行时长")
        return False

    walk_duration = walk_to_subway_result.total_duration_seconds
    if walk_duration > max_walking_duration_to_subway:
        print(f"❌ 到友谊南路地铁站步行时长{walk_duration}秒，超过{max_walking_duration_to_subway}秒（12分钟）")
        return False
    print(f"✅ 到友谊南路地铁站步行时长{walk_duration}秒，符合要求（≤{max_walking_duration_to_subway}秒）")

    # 步骤5: 从"天津站"和"天津西站"步行到酒吧的时间差≤20分钟
    print(f"\n【步骤5】验证天津站与天津西站步行到酒吧的时间差（≤{max_walking_time_diff_seconds}秒，即20分钟）")
    print("-" * 80)

    # 天津站坐标
    station_a_search = maps_text_search(keywords=station_a_keywords, city=city, citylimit="true")
    if station_a_search.error or not station_a_search.pois:
        print(f"❌ 未找到天津站")
        return False
    station_a_id = station_a_search.pois[0].id
    station_a_detail = maps_search_detail(id=station_a_id)
    if station_a_detail.error or not station_a_detail.location:
        print(f"❌ 获取天津站坐标失败")
        return False
    station_a_location = station_a_detail.location
    print(f"✅ 天津站坐标: {station_a_location}")

    # 天津西站坐标
    station_b_search = maps_text_search(keywords=station_b_keywords, city=city, citylimit="true")
    if station_b_search.error or not station_b_search.pois:
        print(f"❌ 未找到天津西站")
        return False
    station_b_id = station_b_search.pois[0].id
    station_b_detail = maps_search_detail(id=station_b_id)
    if station_b_detail.error or not station_b_detail.location:
        print(f"❌ 获取天津西站坐标失败")
        return False
    station_b_location = station_b_detail.location
    print(f"✅ 天津西站坐标: {station_b_location}")

    # tA: 天津站步行到酒吧
    walk_a_result = maps_walking_by_coordinates(
        origin=station_a_location,
        destination=bar_location
    )
    if walk_a_result.error or walk_a_result.total_duration_seconds is None:
        print(f"❌ 计算天津站到酒吧步行时间失败")
        return False
    t_a = walk_a_result.total_duration_seconds
    print(f"✅ 天津站到酒吧步行时长: {t_a}秒")

    # tB: 天津西站步行到酒吧
    walk_b_result = maps_walking_by_coordinates(
        origin=station_b_location,
        destination=bar_location
    )
    if walk_b_result.error or walk_b_result.total_duration_seconds is None:
        print(f"❌ 计算天津西站到酒吧步行时间失败")
        return False
    t_b = walk_b_result.total_duration_seconds
    print(f"✅ 天津西站到酒吧步行时长: {t_b}秒")

    time_diff = abs(t_a - t_b)
    if time_diff > max_walking_time_diff_seconds:
        print(f"❌ 两站到酒吧步行时间差{time_diff}秒，超过{max_walking_time_diff_seconds}秒（20分钟）")
        return False
    print(f"✅ 两站到酒吧步行时间差{time_diff}秒，符合要求（≤{max_walking_time_diff_seconds}秒）")

    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 759.py <poi_id> [user_location]")
        print("示例: python 759.py B0J2FR5W41")
        print("示例: python 759.py B0J2FR5W41 117.216809,39.064497")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0J2FR5W41"
        user_location = "117.216809,39.064497"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "117.216809,39.064497"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)

    result = verify_poi(poi_id, user_location=user_location)

    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
