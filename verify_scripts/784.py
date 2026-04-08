
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近5公里酒店：调用 maps_around_search(location='118.626018,37.446143', radius='5000', keywords='酒店')，验证返回pois中包含目标poi_id=B0IAMAH094。
2) 酒店评分≥4.6：调用 maps_search_detail(id='B0IAMAH094')，读取biz_ext.rating，验证 rating >= 4.6。
3) 到出发地最大驾车距离≤2公里：调用 maps_driving_by_coordinates(origin='118.626018,37.446143', destination=酒店detail中的location='118.622969,37.442575')，验证 total_distance_meters <= 2000。
4) 途经点300米内有便利店（以“驾车路线steps的每个to_coordinates作为途经点集合”）：
- 取步骤坐标：从步骤列表提取每个 step.to_coordinates（以及终点坐标），对每个坐标调用 maps_around_search(location=该坐标, radius='300', keywords='便利店')；
- 验证每次返回pois数量 >= 1。
5) 酒店到周边1200米内公交站的最小步行距离≤1400米：
- 调用 maps_around_search(location=酒店坐标'118.622969,37.442575', radius='1200', keywords='公交站') 获取公交站集合S；
- 对S中每个站点si，调用 maps_walking_by_coordinates(origin=酒店坐标, destination=si.location)，取 total_distance_meters 的最小值d_min；验证 d_min <= 1400。
6) 酒店到周边1200米内公交站的最小步行时间≤25分钟：
- 复用步骤5中的集合S；
- 对S中每个站点si调用 maps_walking_by_coordinates(...)，取 total_duration_seconds 的最小值t_min；验证 t_min <= 1500秒。
7) 酒店到指定公交站“鲁班公寓(公交站)”直线距离≤250米：
- 调用 maps_text_search(keywords='鲁班公寓(公交站)', city='东营', citylimit='true') 获取该站点id与坐标（该站点为 BV10775930，坐标为 around_search结果中的 location='118.624280,37.441418'）；
- 调用 maps_distance(origins=酒店坐标'118.622969,37.442575', destination='118.624280,37.441418')，验证 distance_meters <= 250。
8) 酒店到东营胜利机场驾车时间≤30分钟：
- 调用 maps_text_search(keywords='东营胜利机场', city='东营') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取机场坐标；
- 调用 maps_driving_by_coordinates(origin=酒店坐标, destination=机场坐标)，验证 total_duration_seconds <= 1800秒。
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
    maps_text_search,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "118.626018,37.446143",
    target_poi_id: str = "B0IAMAH094",
    around_radius: int = 5000,
    hotel_keywords: str = "酒店",
    hotel_location: str = "118.622969,37.442575",
    min_rating: float = 4.6,
    max_driving_distance_to_origin: int = 2000,  # 米
    poi_around_radius_convenience: int = 300,
    convenience_keywords: str = "便利店",
    bus_search_radius: int = 1200,
    bus_keywords: str = "公交站",
    max_min_bus_walking_distance: int = 1400,  # 米
    max_min_bus_walking_duration: int = 1500,  # 秒，25分钟
    target_bus_name: str = "鲁班公寓(公交站)",
    target_bus_city: str = "东营",
    target_bus_citylimit: str = "true",
    target_bus_id: str = "BV10775930",
    max_target_bus_line_distance: int = 250,  # 米
    airport_address: str = "东营胜利机场",
    airport_city: str = "东营",
    max_airport_driving_duration: int = 1800,  # 秒，30分钟
) -> bool:
    """
    根据注释中的步骤验证酒店POI是否满足要求。
    """
    # 步骤1) 附近5公里酒店：周边搜索酒店，验证包含目标POI
    around_result = maps_around_search(
        location=user_location,
        radius=str(around_radius),
        keywords=hotel_keywords,
    )
    if around_result.error:
        print(f"❌ 周边酒店搜索失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print("❌ 在指定范围内未找到任何酒店")
        return False

    hotel_found = False
    for p in around_result.pois:
        if p.id == target_poi_id:
            hotel_found = True
            print(
                f"✅ 在{around_radius}米范围内找到目标酒店: {p.name} (ID: {p.id})，共返回 {len(around_result.pois)} 个POI"
            )
            break

    if not hotel_found:
        print(
            f"❌ 目标POI {target_poi_id} 未出现在 {around_radius} 米范围内的“{hotel_keywords}”搜索结果中"
        )
        return False

    # 使用给定酒店坐标
    hotel_coord = hotel_location
    print(f"✅ 使用酒店坐标: {hotel_coord}")

    # 步骤2) 酒店评分≥4.6
    detail = maps_search_detail(id=target_poi_id)
    if detail.error:
        print(f"❌ 获取酒店详情失败: {detail.error}")
        return False

    rating = None
    if detail.biz_ext and isinstance(detail.biz_ext, dict):
        rating_raw = detail.biz_ext.get("rating")
        try:
            rating = float(rating_raw) if rating_raw not in (None, "") else None
        except (TypeError, ValueError):
            rating = None

    if rating is None:
        print("❌ 无法获取酒店评分 biz_ext.rating")
        return False

    if rating < min_rating:
        print(f"❌ 酒店评分 {rating} < {min_rating}")
        return False

    print(f"✅ 酒店评分 {rating} ≥ {min_rating}")

    # 步骤3) 到出发地最大驾车距离≤2公里
    driving_to_origin = maps_driving_by_coordinates(
        origin=user_location,
        destination=hotel_coord,
    )
    if driving_to_origin.error:
        print(f"❌ 计算出发地到酒店的驾车路线失败: {driving_to_origin.error}")
        return False
    if driving_to_origin.total_distance_meters is None:
        print("❌ 驾车结果中无总距离信息")
        return False

    driving_distance = driving_to_origin.total_distance_meters
    if driving_distance > max_driving_distance_to_origin:
        print(
            f"❌ 出发地到酒店的驾车距离为 {driving_distance} 米，超过 {max_driving_distance_to_origin} 米"
        )
        return False
    print(
        f"✅ 出发地到酒店的驾车距离为 {driving_distance} 米，满足 ≤ {max_driving_distance_to_origin} 米"
    )

    # 步骤4) 途经点300米内有便利店：对每个step.to_coordinates和终点坐标搜索便利店
    if not driving_to_origin.steps or len(driving_to_origin.steps) == 0:
        print("❌ 驾车路线没有步骤信息，无法检查途经点便利店")
        return False

    all_points = [step.to_coordinates for step in driving_to_origin.steps if step.to_coordinates]
    # 终点坐标（已经包含在最后一个 step.to_coordinates 中，此处“以及终点坐标”注释不额外重复添加）

    for idx, coord in enumerate(all_points):
        around_conv = maps_around_search(
            location=coord,
            radius=str(poi_around_radius_convenience),
            keywords=convenience_keywords,
        )
        if around_conv.error:
            print(
                f"❌ 在途经点 {idx} ({coord}) 附近搜索便利店失败: {around_conv.error}"
            )
            return False
        if not around_conv.pois or len(around_conv.pois) == 0:
            print(
                f"❌ 途经点 {idx} ({coord}) {poi_around_radius_convenience} 米范围内未找到任何便利店"
            )
            return False
        print(
            f"✅ 途经点 {idx} ({coord}) 附近找到 {len(around_conv.pois)} 个便利店，例如 {around_conv.pois[0].name}"
        )

    # 步骤5) 酒店到周边1200米内公交站的最小步行距离≤1400米
    bus_around = maps_around_search(
        location=hotel_coord,
        radius=str(bus_search_radius),
        keywords=bus_keywords,
    )
    if bus_around.error:
        print(f"❌ 搜索酒店附近公交站失败: {bus_around.error}")
        return False
    if not bus_around.pois or len(bus_around.pois) == 0:
        print(
            f"❌ 在酒店 {bus_search_radius} 米范围内未找到任何公交站"
        )
        return False

    bus_pois = [p for p in bus_around.pois if p.location is not None]
    if len(bus_pois) == 0:
        print("❌ 公交站结果中均缺少坐标信息")
        return False
    print(f"✅ 在酒店附近找到 {len(bus_pois)} 个带坐标的公交站")

    d_min = None
    t_min = None

    for p in bus_pois:
        walk_res = maps_walking_by_coordinates(
            origin=hotel_coord,
            destination=p.location,
        )
        if walk_res.error:
            print(
                f"⚠️ 计算到公交站 {p.name} 的步行路线失败: {walk_res.error}"
            )
            continue
        if walk_res.total_distance_meters is None or walk_res.total_duration_seconds is None:
            print(
                f"⚠️ 到公交站 {p.name} 的步行结果缺少距离或时间信息"
            )
            continue

        dist = walk_res.total_distance_meters
        dur = walk_res.total_duration_seconds

        if d_min is None or dist < d_min:
            d_min = dist
        if t_min is None or dur < t_min:
            t_min = dur

    if d_min is None or t_min is None:
        print("❌ 无法获得到任何公交站的步行距离或时间")
        return False

    # 步骤5：检查 d_min
    if d_min > max_min_bus_walking_distance:
        print(
            f"❌ 酒店到周边公交站的最小步行距离为 {d_min} 米，超过 {max_min_bus_walking_distance} 米"
        )
        return False
    print(
        f"✅ 酒店到周边公交站的最小步行距离为 {d_min} 米，满足 ≤ {max_min_bus_walking_distance} 米"
    )

    # 步骤6) 酒店到周边1200米内公交站的最小步行时间≤25分钟（1500秒）
    if t_min > max_min_bus_walking_duration:
        print(
            f"❌ 酒店到周边公交站的最小步行时间为 {t_min} 秒，超过 {max_min_bus_walking_duration} 秒"
        )
        return False
    print(
        f"✅ 酒店到周边公交站的最小步行时间为 {t_min} 秒，满足 ≤ {max_min_bus_walking_duration} 秒"
    )

    # 步骤7) 酒店到指定公交站“鲁班公寓(公交站)”直线距离≤250米
    text_res = maps_text_search(
        keywords=target_bus_name,
        city=target_bus_city,
        citylimit=target_bus_citylimit,
    )
    if text_res.error:
        print(f"❌ 文本搜索目标公交站失败: {text_res.error}")
        return False
    if not text_res.pois or len(text_res.pois) == 0:
        print("❌ 文本搜索未找到目标公交站")
        return False

    # 这里描述中明确该站点为给定ID与坐标，直接使用给定坐标
    target_bus_coord = "118.624280,37.441418"
    print(
        f"✅ 使用目标公交站 {target_bus_name} (ID: {target_bus_id}) 坐标: {target_bus_coord}"
    )

    dist_bus = maps_distance(
        origins=hotel_coord,
        destination=target_bus_coord,
    )
    if dist_bus.error:
        print(f"❌ 计算酒店到目标公交站直线距离失败: {dist_bus.error}")
        return False
    if not dist_bus.results or len(dist_bus.results) == 0:
        print("❌ 未获得直线距离计算结果")
        return False

    line_distance = dist_bus.results[0].distance_meters
    if line_distance > max_target_bus_line_distance:
        print(
            f"❌ 酒店到 {target_bus_name} 的直线距离为 {line_distance} 米，超过 {max_target_bus_line_distance} 米"
        )
        return False
    print(
        f"✅ 酒店到 {target_bus_name} 的直线距离为 {line_distance} 米，满足 ≤ {max_target_bus_line_distance} 米"
    )

    # 步骤8) 用 maps_text_search + maps_search_detail 获取东营胜利机场坐标，酒店到东营胜利机场驾车时间≤30分钟
    text_search_result = maps_text_search(keywords=airport_address, city=airport_city)
    if text_search_result.error:
        print(f"❌ 获取东营胜利机场坐标失败: {text_search_result.error}")
        return False
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print("❌ 未找到东营胜利机场的POI结果")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取东营胜利机场坐标失败: {detail_result.error or '无location'}")
        return False

    airport_coord = detail_result.location
    print(f"✅ 使用机场坐标: {airport_coord}")

    driving_to_airport = maps_driving_by_coordinates(
        origin=hotel_coord,
        destination=airport_coord,
    )
    if driving_to_airport.error:
        print(f"❌ 计算酒店到机场的驾车路线失败: {driving_to_airport.error}")
        return False
    if driving_to_airport.total_duration_seconds is None:
        print("❌ 驾车结果中无总时间信息")
        return False

    airport_duration = driving_to_airport.total_duration_seconds
    if airport_duration > max_airport_driving_duration:
        print(
            f"❌ 酒店到东营胜利机场驾车时间为 {airport_duration} 秒，超过 {max_airport_driving_duration} 秒"
        )
        return False
    print(
        f"✅ 酒店到东营胜利机场驾车时间为 {airport_duration} 秒，满足 ≤ {max_airport_driving_duration} 秒"
    )

    print("✅ 所有验证步骤均通过！")
    return True


if __name__ == "__main__":
    print("开始验证 784.py 文件...\n")
    result = verify_poi(poi_id="B0IAMAH094")
    print(f"\n验证结果: {result}")