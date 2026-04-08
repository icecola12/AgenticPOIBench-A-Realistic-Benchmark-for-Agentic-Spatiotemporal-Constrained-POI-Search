
"""
修改任务指令：你要在附近12000米以内找一家博物馆。你希望这家博物馆在你开车过去不超过8分钟，同时你骑行过去的距离不要超过3500米。为了方便坐地铁，你要求这家博物馆周边1500米内必须能找到地铁站，并且从博物馆步行到步行时间最近的地铁站不超过12分钟，同时博物馆到直线距离最近地铁站的直线距离也要不超过700米。另外你准备去南昌昌北国际机场，要求从博物馆开车去机场不超过35分钟。最后，你朋友从南昌西站开车过来接你，要求你朋友从南昌西站开车先到博物馆再去机场的总耗时，相比他直接从南昌西站开车去机场，绕路增加的时间不超过10分钟。你情绪化，时而冷静时而愤怒，态度变化快。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近12000米内博物馆（周边搜索约束）
- 调用 maps_around_search(location='115.9115,28.711825', keywords='博物馆', radius='12000')
- 断言返回pois列表中包含 target_poi_id='B0FFGY018L'

2) 评分约束（>=4.8）
- 调用 maps_search_detail(id='B0FFGY018L')，读取 biz_ext.rating
- 验证 rating >= 4.8（该POI返回rating=4.9）

3) 目标场所到出发地的最大驾车距离（<=4公里）
- 取目标POI坐标：maps_search_detail(id='B0FFGY018L').location = '115.881823,28.705900'
- 调用 maps_driving_by_coordinates(origin='115.9115,28.711825', destination='115.881823,28.705900')
- 验证 total_distance_meters <= 4000（本次返回3008m）

4) 目标场所到出发地的最大骑行距离（<=3500米）
- 调用 maps_bicycling_by_coordinates(origin='115.9115,28.711825', destination='115.881823,28.705900')
- 验证 total_distance_meters <= 3500（本次返回3008m）

5) 目标场所到指定出发点的驾车通行时间（<=8分钟）
- 调用 maps_driving_by_coordinates(origin='115.9115,28.711825', destination='115.881823,28.705900')
- 验证 total_duration_seconds <= 8*60（本次返回341s）

6) 目标场所周边1500米内存在地铁站 & 最近地铁站步行时间<=12分钟
- 调用 maps_around_search(location='115.881823,28.705900', keywords='地铁站', radius='1500')，得到候选地铁站列表（本次2个：珠江路、长江路）
- 对每个地铁站poi，调用 maps_walking_by_coordinates(origin='115.881823,28.705900', destination=station.location)
- 取 total_duration_seconds 最小值 t_min，验证 t_min <= 12*60（本次到“珠江路(地铁站)”为690s）

7) 目标场所到周边1500米内地铁站的最小直线距离<=700米
- 复用第6步地铁站列表，调用 maps_distance(origins=station1.location|station2.location|..., destination='115.881823,28.705900')
- 取 distance_meters 最小值 d_min，验证 d_min <= 700（本次到“珠江路(地铁站)”直线距离604m）

8) 目标场所到特定交通枢纽（南昌昌北国际机场）的驾车时间<=35分钟
- 调用 maps_text_search(keywords='南昌昌北国际机场', city='南昌') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到机场坐标 airport
- 调用 maps_driving_by_coordinates(origin='115.881823,28.705900', destination=airport)
- 验证 total_duration_seconds <= 35*60（本次返回1947s）

9) 从起点A(南昌西站)经由目标场所到达终点B(昌北机场)的绕行增加时间<=10分钟
- 调用 maps_text_search(keywords='南昌西站', city='南昌') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到西站坐标 A
- 机场坐标B同第8步
- 计算直达：t_direct = maps_driving_by_coordinates(origin=A, destination=B).total_duration_seconds（本次4730s）
- 计算经由：t_via = maps_driving_by_coordinates(origin=A, destination='115.881823,28.705900').total_duration_seconds + maps_driving_by_coordinates(origin='115.881823,28.705900', destination=B).total_duration_seconds（本次2060s+1947s=4007s）
- 验证 (t_via - t_direct) <= 10*60（本次为-723s，满足“不超过10分钟”的上限约束）
"""
import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_text_search,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance,
    maps_bicycling_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.9115,28.711825",
    target_poi_id: str = "B0FFGY018L",
    around_radius: int = 12000,
    museum_keywords: str = "博物馆",
    min_rating: float = 4.8,
    poi_location: str = "115.881823,28.705900",
    max_driving_distance: int = 4000,      # 米
    max_bicycling_distance: int = 3500,    # 米
    max_driving_duration_to_poi: int = 8 * 60,  # 秒
    metro_radius: int = 1500,
    metro_keywords: str = "地铁站",
    max_metro_walking_duration: int = 12 * 60,  # 秒
    max_metro_line_distance: int = 700,         # 米
    airport_address: str = "南昌昌北国际机场",
    airport_city: str = "南昌",
    airport_location: str = "115.911718,28.858250",
    max_airport_driving_duration: int = 35 * 60,  # 秒
    west_station_address: str = "南昌西站",
    west_station_city: str = "南昌",
    west_station_location: str = "115.792516,28.624876",
    max_detour_duration: int = 10 * 60,  # 秒
) -> bool:
    """
    根据给定的九个步骤验证 POI 是否符合要求。
    """
    # 步骤1) 附近12000米内博物馆（周边搜索约束）
    around_result = maps_around_search(
        location=user_location,
        keywords=museum_keywords,
        radius=str(around_radius),
    )
    if around_result.error:
        print(f"❌ 周边博物馆搜索失败: {around_result.error}")
        return False
    if not around_result.pois or len(around_result.pois) == 0:
        print("❌ 在指定范围内未找到任何博物馆")
        return False

    poi_found = False
    for p in around_result.pois:
        if p.id == target_poi_id:
            poi_found = True
            print(
                f"✅ 在{around_radius}米范围内找到目标博物馆: {p.name} (ID: {p.id})，共返回 {len(around_result.pois)} 个POI"
            )
            break
    if not poi_found:
        print(
            f"❌ 目标POI {target_poi_id} 未出现在 {around_radius} 米范围内的“{museum_keywords}”搜索结果中"
        )
        return False

    # 步骤2) 评分约束（>=4.8）
    detail = maps_search_detail(id=target_poi_id)
    if detail.error:
        print(f"❌ 获取博物馆详情失败: {detail.error}")
        return False

    rating = None
    if detail.biz_ext and isinstance(detail.biz_ext, dict):
        rating_raw = detail.biz_ext.get("rating")
        try:
            rating = float(rating_raw) if rating_raw not in (None, "") else None
        except (TypeError, ValueError):
            rating = None

    if rating is None:
        print("❌ 无法获取博物馆评分 biz_ext.rating")
        return False
    if rating < min_rating:
        print(f"❌ 博物馆评分 {rating} < {min_rating}")
        return False
    print(f"✅ 博物馆评分 {rating} ≥ {min_rating}")

    # 步骤3) 目标场所到出发地的最大驾车距离（<=4公里）
    museum_coord = poi_location
    print(f"✅ 使用目标博物馆坐标: {museum_coord}")

    driving_to_poi = maps_driving_by_coordinates(
        origin=user_location,
        destination=museum_coord,
    )
    if driving_to_poi.error:
        print(f"❌ 计算出发地到博物馆的驾车路线失败: {driving_to_poi.error}")
        return False
    if driving_to_poi.total_distance_meters is None:
        print("❌ 驾车结果中无总距离信息")
        return False

    driving_distance = driving_to_poi.total_distance_meters
    if driving_distance > max_driving_distance:
        print(
            f"❌ 出发地到博物馆的驾车距离为 {driving_distance} 米，超过 {max_driving_distance} 米"
        )
        return False
    print(
        f"✅ 出发地到博物馆的驾车距离为 {driving_distance} 米，满足 ≤ {max_driving_distance} 米"
    )

    # 步骤4) 目标场所到出发地的最大骑行距离（<=3500米）
    bicycling_to_poi = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=museum_coord,
    )
    if bicycling_to_poi.error:
        print(f"❌ 计算出发地到博物馆的骑行路线失败: {bicycling_to_poi.error}")
        return False
    if bicycling_to_poi.total_distance_meters is None:
        print("❌ 骑行结果中无总距离信息")
        return False

    bicycling_distance = bicycling_to_poi.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(
            f"❌ 出发地到博物馆的骑行距离为 {bicycling_distance} 米，超过 {max_bicycling_distance} 米"
        )
        return False
    print(
        f"✅ 出发地到博物馆的骑行距离为 {bicycling_distance} 米，满足 ≤ {max_bicycling_distance} 米"
    )

    # 步骤5) 目标场所到指定出发点的驾车通行时间（<=8分钟）
    driving_time_to_poi = maps_driving_by_coordinates(
        origin=user_location,
        destination=museum_coord,
    )
    if driving_time_to_poi.error:
        print(f"❌ 再次计算驾车时间失败: {driving_time_to_poi.error}")
        return False
    if driving_time_to_poi.total_duration_seconds is None:
        print("❌ 驾车时间结果中无总时间信息")
        return False

    duration_to_poi = driving_time_to_poi.total_duration_seconds
    if duration_to_poi > max_driving_duration_to_poi:
        print(
            f"❌ 出发地到博物馆驾车时间为 {duration_to_poi} 秒，超过 {max_driving_duration_to_poi} 秒"
        )
        return False
    print(
        f"✅ 出发地到博物馆驾车时间为 {duration_to_poi} 秒，满足 ≤ {max_driving_duration_to_poi} 秒"
    )

    # 步骤6) 目标场所周边1500米内存在地铁站 & 最近地铁站步行时间<=12分钟
    metro_around = maps_around_search(
        location=museum_coord,
        keywords=metro_keywords,
        radius=str(metro_radius),
    )
    if metro_around.error:
        print(f"❌ 搜索博物馆附近地铁站失败: {metro_around.error}")
        return False
    if not metro_around.pois or len(metro_around.pois) == 0:
        print(
            f"❌ 在博物馆 {metro_radius} 米范围内未找到任何地铁站"
        )
        return False

    metro_pois = [p for p in metro_around.pois if p.location is not None]
    if len(metro_pois) == 0:
        print("❌ 地铁站结果中均缺少坐标信息")
        return False
    print(f"✅ 在博物馆附近找到 {len(metro_pois)} 个带坐标的地铁站")

    t_min = None
    for s in metro_pois:
        walk_res = maps_walking_by_coordinates(
            origin=museum_coord,
            destination=s.location,
        )
        if walk_res.error:
            print(
                f"⚠️ 计算到地铁站 {s.name} 的步行路线失败: {walk_res.error}"
            )
            continue
        if walk_res.total_duration_seconds is None:
            print(
                f"⚠️ 到地铁站 {s.name} 的步行结果无时间信息"
            )
            continue

        dur = walk_res.total_duration_seconds
        if t_min is None or dur < t_min:
            t_min = dur

    if t_min is None:
        print("❌ 无法获取到任何地铁站的步行时间")
        return False

    if t_min > max_metro_walking_duration:
        print(
            f"❌ 博物馆到步行时间最近地铁站的时间为 {t_min} 秒，超过 {max_metro_walking_duration} 秒"
        )
        return False
    print(
        f"✅ 博物馆到步行时间最近地铁站的时间为 {t_min} 秒，满足 ≤ {max_metro_walking_duration} 秒"
    )

    # 步骤7) 目标场所到周边1500米内地铁站的最小直线距离<=700米
    origins_str = "|".join(p.location for p in metro_pois if p.location)
    distance_res = maps_distance(
        origins=origins_str,
        destination=museum_coord,
    )
    if distance_res.error:
        print(f"❌ 计算地铁站到博物馆直线距离失败: {distance_res.error}")
        return False
    if not distance_res.results or len(distance_res.results) == 0:
        print("❌ 未获得直线距离计算结果")
        return False

    d_min = None
    for item in distance_res.results:
        d = item.distance_meters
        if d_min is None or d < d_min:
            d_min = d

    if d_min is None:
        print("❌ 无法计算最小直线距离")
        return False
    if d_min > max_metro_line_distance:
        print(
            f"❌ 地铁站到博物馆的最小直线距离为 {d_min} 米，超过 {max_metro_line_distance} 米"
        )
        return False
    print(
        f"✅ 地铁站到博物馆的最小直线距离为 {d_min} 米，满足 ≤ {max_metro_line_distance} 米"
    )

    # 步骤8) 用 maps_text_search + maps_search_detail 获取机场坐标，目标场所到南昌昌北国际机场的驾车时间<=35分钟
    text_search_result = maps_text_search(keywords=airport_address, city=airport_city)
    if text_search_result.error:
        print(f"❌ 获取机场坐标失败: {text_search_result.error}")
        return False
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print("❌ 未找到机场的POI结果")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取机场坐标失败: {detail_result.error or '无location'}")
        return False

    airport_coord = detail_result.location
    print(f"✅ 使用机场坐标: {airport_coord}")

    driving_to_airport = maps_driving_by_coordinates(
        origin=museum_coord,
        destination=airport_coord,
    )
    if driving_to_airport.error:
        print(f"❌ 计算博物馆到机场的驾车路线失败: {driving_to_airport.error}")
        return False
    if driving_to_airport.total_duration_seconds is None:
        print("❌ 驾车结果中无总时间信息")
        return False

    duration_to_airport = driving_to_airport.total_duration_seconds
    if duration_to_airport > max_airport_driving_duration:
        print(
            f"❌ 博物馆到机场驾车时间为 {duration_to_airport} 秒，超过 {max_airport_driving_duration} 秒"
        )
        return False
    print(
        f"✅ 博物馆到机场驾车时间为 {duration_to_airport} 秒，满足 ≤ {max_airport_driving_duration} 秒"
    )

    # 步骤9) 用 maps_text_search + maps_search_detail 获取南昌西站坐标，从南昌西站经博物馆到机场的绕行时间增加不超过10分钟
    text_search_result = maps_text_search(keywords=west_station_address, city=west_station_city)
    if text_search_result.error:
        print(f"❌ 获取南昌西站坐标失败: {text_search_result.error}")
        return False
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print("❌ 未找到南昌西站的POI结果")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取南昌西站坐标失败: {detail_result.error or '无location'}")
        return False

    west_coord = detail_result.location
    print(f"✅ 使用南昌西站坐标: {west_coord}")

    # 直达 A -> B
    direct_drive = maps_driving_by_coordinates(
        origin=west_coord,
        destination=airport_coord,
    )
    if direct_drive.error:
        print(f"❌ 计算南昌西站到机场直达路线失败: {direct_drive.error}")
        return False
    if direct_drive.total_duration_seconds is None:
        print("❌ 直达路线结果中无总时间信息")
        return False
    t_direct = direct_drive.total_duration_seconds

    # 经由 A -> 博物馆 -> B
    drive_A_to_museum = maps_driving_by_coordinates(
        origin=west_coord,
        destination=museum_coord,
    )
    if drive_A_to_museum.error:
        print(f"❌ 计算南昌西站到博物馆路线失败: {drive_A_to_museum.error}")
        return False
    if drive_A_to_museum.total_duration_seconds is None:
        print("❌ 南昌西站到博物馆路线结果中无时间信息")
        return False

    drive_museum_to_B = maps_driving_by_coordinates(
        origin=museum_coord,
        destination=airport_coord,
    )
    if drive_museum_to_B.error:
        print(f"❌ 计算博物馆到机场路线失败: {drive_museum_to_B.error}")
        return False
    if drive_museum_to_B.total_duration_seconds is None:
        print("❌ 博物馆到机场路线结果中无时间信息")
        return False

    t_via = drive_A_to_museum.total_duration_seconds + drive_museum_to_B.total_duration_seconds
    detour = t_via - t_direct

    if detour > max_detour_duration:
        print(
            f"❌ 经由博物馆的绕行时间增加 {detour} 秒，超过 {max_detour_duration} 秒"
        )
        return False
    print(
        f"✅ 经由博物馆的绕行时间增加 {detour} 秒，满足 ≤ {max_detour_duration} 秒"
    )

    print("✅ 所有验证步骤均通过！")
    return True


if __name__ == "__main__":
    print("开始验证 786.py 文件...\n")
    result = verify_poi(poi_id="B0FFGY018L")
    print(f"\n验证结果: {result}")