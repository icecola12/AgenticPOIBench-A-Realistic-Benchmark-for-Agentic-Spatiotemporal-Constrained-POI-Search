"""
修改任务指令：你想在附近3000米以内找一个加油站。你打算骑车过去，所以从你到加油站的骑行距离不能超过2000米。加油站附近1500米范围内要能找到地铁站，并且加油站到这些地铁站里直线距离最近的一个不能超过800米，同时步行到最近地铁站的步行距离也不能超过1100米。你还希望从加油站走到最近的地铁站不超过18分钟。另外你要去赶飞机，从这个加油站开车到北京首都国际机场的用时不能超过45分钟。你没有耐心，说话直接
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近3000米：调用 maps_around_search(location='116.364697,39.931225', keywords='加油站', radius='3000')，验证返回pois中包含 target_poi_id='B000A81JYJ'。
2) 加油站类型+评分：调用 maps_search_detail(id='B000A81JYJ')，验证 name/类型为加油站；并验证 biz_ext.rating >= 4.6。
3) 你到加油站骑行距离≤2000米：调用 maps_bicycling_by_coordinates(origin='116.364697,39.931225', destination=POI.location)，验证 total_distance_meters <= 2000。
4) 加油站附近1500米内存在地铁站：调用 maps_around_search(location=POI.location, keywords='地铁站', radius='1500')，取返回的所有地铁站poi列表S，验证 |S|>=1。
5) 地铁站直线距离约束≤800米：对S中每个地铁站，调用 maps_distance(origins=所有地铁站location用'|'拼接, destination=POI.location)，取最小 distance_meters，验证 <= 800。
6) 地铁站步行距离约束≤1100米：对S中每个地铁站，分别调用 maps_walking_by_coordinates(origin=POI.location, destination=station.location)，取最小 total_distance_meters，验证 <= 1100。
7) 地铁站步行时间≤18分钟：沿用第6步的步行结果，取最小 total_duration_seconds，验证 <= 1080。
8) 到北京首都国际机场驾车时间≤45分钟：调用 maps_text_search(keywords='北京首都国际机场', city='北京') 取 poi_id，再 maps_search_detail(id=poi_id) 得到 机场坐标 A；再调用 maps_driving_by_coordinates(origin=POI.location, destination=A.location)，验证 total_duration_seconds <= 2700。
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
    maps_walking_by_coordinates,
    maps_distance,
    maps_bicycling_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.364697,39.931225",
    target_poi_id: str = "B000A81JYJ",
    around_radius: int = 3000,
    around_keywords: str = "加油站",
    max_bicycling_distance: int = 2000,  # 米
    subway_keywords: str = "地铁站",
    subway_search_radius: int = 1500,  # 米
    max_subway_straight_distance: int = 800,  # 米
    max_subway_walking_distance: int = 1100,  # 米
    max_subway_walking_duration: int = 1080,  # 秒，18分钟
    airport_address: str = "北京首都国际机场",
    airport_city: str = "北京",
    max_airport_driving_duration: int = 2700,  # 秒，45分钟
    min_rating: float = 4.6,
) -> bool:
    """
    验证POI是否符合要求。

    按注释中的步骤依次验证：
    1) 周边3000米内加油站包含目标POI；
    2) 目标POI为加油站且评分>=4.6；
    3) 用户到加油站骑行距离<=2000米；
    4) 加油站附近1500米内存在至少一个地铁站；
    5) 这些地铁站到加油站的最小直线距离<=800米；
    6) 加油站到这些地铁站中步行距离最小的<=1100米；
    7) 加油站到这些地铁站中步行时间最小的<=1080秒（18分钟）；
    8) 加油站到北京首都国际机场驾车时间<=2700秒（45分钟）。

    Args:
        poi_id: 待验证的POI ID（应与 target_poi_id 一致）
        其余参数对应各项约束的可配置阈值。

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1：附近3000米内的加油站包含目标POI
    around_result = maps_around_search(
        location=user_location,
        keywords=around_keywords,
        radius=str(around_radius),
    )
    if around_result.error:
        print(f"❌ 周边搜索失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print("❌ 周边未找到任何加油站")
        return False

    found = False
    for p in around_result.pois:
        if p.id == target_poi_id:
            found = True
            print(
                f"✅ 在{around_radius}米范围内找到目标加油站: {p.name} (ID: {p.id})，共返回 {len(around_result.pois)} 个POI"
            )
            break
    if not found:
        print(
            f"❌ 目标POI {target_poi_id} 不在 {around_radius} 米范围内的“{around_keywords}”搜索结果中"
        )
        return False

    # 步骤2：加油站类型 + 评分
    detail = maps_search_detail(id=target_poi_id)
    if detail.error:
        print(f"❌ 获取POI详情失败: {detail.error}")
        return False

    if not detail.name:
        print("❌ POI详情中没有名称信息")
        return False

    if "加油" not in detail.name and "加油站" not in detail.name:
        print(f"❌ POI名称不符合加油站预期: {detail.name}")
        return False
    print(f"✅ POI名称看起来是加油站: {detail.name}")

    rating = None
    if detail.biz_ext and isinstance(detail.biz_ext, dict):
        rating_raw = detail.biz_ext.get("rating")
        try:
            rating = float(rating_raw) if rating_raw not in (None, "") else None
        except (TypeError, ValueError):
            rating = None

    if rating is None:
        print("❌ 无法获取评分信息 biz_ext.rating")
        return False
    if rating < min_rating:
        print(f"❌ 加油站评分 {rating} < {min_rating}")
        return False
    print(f"✅ 加油站评分 {rating} ≥ {min_rating}")

    if not detail.location:
        print("❌ POI详情中无坐标信息")
        return False
    poi_location = detail.location
    print(f"✅ 获取加油站坐标: {poi_location}")

    # 步骤3：你到加油站骑行距离≤2000米
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location, destination=poi_location
    )
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    if bicycling_result.total_distance_meters is None:
        print("❌ 骑行结果中无总距离信息")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(
            f"❌ 骑行距离 {bicycling_distance} 米，超过 {max_bicycling_distance} 米"
        )
        return False
    print(
        f"✅ 骑行距离 {bicycling_distance} 米，满足 ≤ {max_bicycling_distance} 米"
    )

    # 步骤4：加油站附近1500米内存在地铁站
    subway_around_result = maps_around_search(
        location=poi_location,
        keywords=subway_keywords,
        radius=str(subway_search_radius),
    )
    if subway_around_result.error:
        print(f"❌ 搜索地铁站失败: {subway_around_result.error}")
        return False
    if not subway_around_result.pois or len(subway_around_result.pois) == 0:
        print(
            f"❌ 在加油站 {subway_search_radius} 米范围内未找到任何地铁站"
        )
        return False

    subway_pois = [
        s for s in subway_around_result.pois if s.location is not None
    ]
    if len(subway_pois) == 0:
        print("❌ 地铁站结果中均无坐标，无法继续验证")
        return False
    print(
        f"✅ 在加油站 {subway_search_radius} 米范围内找到 {len(subway_pois)} 个地铁站"
    )

    # 步骤5：地铁站直线距离约束≤800米（批量调用 maps_distance）
    origins_str = "|".join(s.location for s in subway_pois if s.location)
    distance_result = maps_distance(origins=origins_str, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算地铁站到加油站直线距离失败: {distance_result.error}")
        return False
    if not distance_result.results or len(distance_result.results) == 0:
        print("❌ 未获得地铁站直线距离结果")
        return False

    min_straight_distance = None
    for item in distance_result.results:
        d = item.distance_meters
        if min_straight_distance is None or d < min_straight_distance:
            min_straight_distance = d

    if min_straight_distance is None:
        print("❌ 无法计算最小直线距离")
        return False
    if min_straight_distance > max_subway_straight_distance:
        print(
            f"❌ 地铁站到加油站的最小直线距离为 {min_straight_distance} 米，超过 {max_subway_straight_distance} 米"
        )
        return False
    print(
        f"✅ 地铁站到加油站的最小直线距离为 {min_straight_distance} 米，满足 ≤ {max_subway_straight_distance} 米"
    )

    # 步骤6&7：地铁站步行距离和时间约束
    min_walking_distance = None
    min_walking_duration = None

    for s in subway_pois:
        walk_res = maps_walking_by_coordinates(
            origin=poi_location, destination=s.location
        )
        if walk_res.error:
            print(
                f"⚠️ 计算到地铁站 {s.name} 的步行路线失败: {walk_res.error}"
            )
            continue
        if walk_res.total_distance_meters is None or walk_res.total_duration_seconds is None:
            print(
                f"⚠️ 到地铁站 {s.name} 的步行结果缺少距离或时间信息"
            )
            continue

        dist = walk_res.total_distance_meters
        dur = walk_res.total_duration_seconds

        if min_walking_distance is None or dist < min_walking_distance:
            min_walking_distance = dist
        if min_walking_duration is None or dur < min_walking_duration:
            min_walking_duration = dur

    if min_walking_distance is None or min_walking_duration is None:
        print("❌ 无法获取任何地铁站的步行距离或时间")
        return False

    # 步骤6：步行距离≤1100米
    if min_walking_distance > max_subway_walking_distance:
        print(
            f"❌ 到最近地铁站的最小步行距离为 {min_walking_distance} 米，超过 {max_subway_walking_distance} 米"
        )
        return False
    print(
        f"✅ 到最近地铁站的最小步行距离为 {min_walking_distance} 米，满足 ≤ {max_subway_walking_distance} 米"
    )

    # 步骤7：步行时间≤18分钟（1080秒）
    if min_walking_duration > max_subway_walking_duration:
        print(
            f"❌ 到最近地铁站的最小步行时间为 {min_walking_duration} 秒，超过 {max_subway_walking_duration} 秒"
        )
        return False
    print(
        f"✅ 到最近地铁站的最小步行时间为 {min_walking_duration} 秒，满足 ≤ {max_subway_walking_duration} 秒"
    )

    # 步骤8：到北京首都国际机场驾车时间≤45分钟（用 maps_text_search + maps_search_detail 替代 maps_geo）
    airport_text_result = maps_text_search(keywords=airport_address, city=airport_city)
    if airport_text_result.error:
        print(f"❌ 获取机场坐标失败: {airport_text_result.error}")
        return False
    if not airport_text_result.pois or len(airport_text_result.pois) == 0:
        print("❌ 未找到机场地理编码结果")
        return False

    first_poi_id = airport_text_result.pois[0].id
    airport_detail_result = maps_search_detail(id=first_poi_id)
    if airport_detail_result.error:
        print(f"❌ 获取坐标失败: {airport_detail_result.error}")
        return False
    if not airport_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    airport_location = airport_detail_result.location
    print(f"✅ 获取机场坐标: {airport_location} ({airport_address})")

    driving_res = maps_driving_by_coordinates(
        origin=poi_location, destination=airport_location
    )
    if driving_res.error:
        print(f"❌ 计算到机场的驾车路线失败: {driving_res.error}")
        return False
    if driving_res.total_duration_seconds is None:
        print("❌ 驾车结果中无总时间信息")
        return False

    driving_duration = driving_res.total_duration_seconds
    if driving_duration > max_airport_driving_duration:
        print(
            f"❌ 从加油站到机场驾车时间为 {driving_duration} 秒，超过 {max_airport_driving_duration} 秒"
        )
        return False
    print(
        f"✅ 从加油站到机场驾车时间为 {driving_duration} 秒，满足 ≤ {max_airport_driving_duration} 秒"
    )

    print("✅ 所有验证步骤均通过！")
    return True


if __name__ == "__main__":
    print("开始验证 780.py 文件...\n")
    result = verify_poi(poi_id="B000A81JYJ")
    print(f"\n验证结果: {result}")