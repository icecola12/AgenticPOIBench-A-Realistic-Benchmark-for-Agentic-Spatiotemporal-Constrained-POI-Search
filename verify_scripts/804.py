"""
修改任务指令：你想在附近2000米以内找一家酒吧。你打算等会儿去大庆西站的公交站坐车，所以这个酒吧要满足：你先步行到酒吧、再从酒吧步行去“大庆西站(临时站)(公交站)”的总时间，相比你直接步行去这个公交站，最多只多40分钟。另外酒吧附近1500米内得能找到公交站，而且酒吧走到这些公交站里最近的那个，步行不要超过15分钟；同时酒吧到附近1500米内公交站的最近直线距离也不能超过500米。你一个喜欢开玩笑的有趣的人，试图让对话变得轻松。
输入：B0L6O7KM3R
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米：调用 maps_around_search(location='124.873499,46.644608', radius='2000', keywords='酒吧')，验证返回pois中包含 id='B0L6O7KM3R'。
2) 绕行增加时间≤40分钟：
- 调用 maps_around_search(location='124.873499,46.644608', radius='2000', keywords='公交站')，在返回结果中选取名称为“大庆西站(临时站)(公交站)”的POI，其location应为'124.883103,46.654475'。
- 调用 maps_search_detail(id='B0L6O7KM3R') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 酒吧坐标P='124.883392,46.632243'。
- 调用 maps_walking_by_coordinates(origin='124.873499,46.644608', destination='124.883103,46.654475') 得到 t_AB（秒）。
- 调用 maps_walking_by_coordinates(origin='124.873499,46.644608', destination=P) 得到 t_AP（秒）。
- 调用 maps_walking_by_coordinates(origin=P, destination='124.883103,46.654475') 得到 t_PB（秒）。
- 计算 extra = t_AP + t_PB - t_AB，验证 extra ≤ 40*60。
（基于已获取真实数据：t_AB=983s，t_AP=1658s，t_PB=1610s，extra=2285s；因此该约束是场景中可验证的关键难点，Agent需找到满足≤1500s的候选酒吧。）
3) 酒吧附近1500米内存在公交站，且最近公交站步行≤15分钟：
- 调用 maps_around_search(location=P, radius='1500', keywords='公交站')，验证 pois 非空。
- 对返回的每个公交站S，调用 maps_walking_by_coordinates(origin=P, destination=S.location) 得到 poi_id，再 maps_search_detail(id=poi_id) 得到 步行时长，取最小值 t_min，验证 t_min ≤ 15*60。
4) 最近公交站直线距离≤500米：
- 在步骤3返回的公交站集合中，对每个公交站S调用 maps_distance(origins=P, destination=S.location) 得到直线距离，取最小值 d_min，验证 d_min ≤ 500。
（示例可核验：公交站“昆仑唐人中心(公交站)”location='124.883263,46.636478'，maps_distance返回约471米。）
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates ,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B0L6O7KM3R",
    user_location: str = "124.873499,46.644608",
    radius: str = "2000",
    keywords: str = "酒吧",
    bus_station_name: str = "大庆西站(临时站)(公交站)",
    bus_station_location: str = "124.883103,46.654475",
    max_detour_time: int = 40 * 60,
    bus_search_radius: str = "1500",
    bus_keywords: str = "公交站",
    max_walking_time_to_bus: int = 15 * 60,
    max_distance_to_bus: int = 500
) -> bool:
    """
    验证POI是否符合给定的验证条件

    Args:
        target_poi_id: 目标POI ID
        user_location: 用户坐标，格式为"经度,纬度"
        radius: 搜索半径（米）
        keywords: 搜索关键词
        bus_station_name: 公交站名称
        bus_station_location: 公交站坐标
        max_detour_time: 最大绕路时间增量（秒）
        bus_search_radius: 公交站搜索半径（米）
        bus_keywords: 公交站搜索关键词
        max_walking_time_to_bus: 到公交站的最大步行时间（秒）
        max_distance_to_bus: 到公交站的最大直线距离（米）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    all_passed = True

    # 步骤1: 附近2000米内包含目标POI
    print(f"步骤1: 验证附近{radius}米内的周边搜索约束 - 查询POI ID: {target_poi_id}")
    around_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )

    if around_result.error:
        print(f"步骤1失败: {around_result.error}")
        return False

    if not around_result.pois:
        print("步骤1失败: 未找到任何POI")
        return False

    # 检查是否包含目标POI
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id not in poi_ids:
        print(f"步骤1失败: POI列表不包含目标POI ID '{target_poi_id}'")
        all_passed = False
    else:
        print(f"步骤1通过: POI列表中包含目标POI ID '{target_poi_id}'")

    # 获取POI坐标（后续步骤需要）
    print(f"\n获取POI坐标 - 查询POI ID: {target_poi_id}")
    poi_detail = maps_search_detail(id=target_poi_id)

    if poi_detail.error:
        print(f"获取POI坐标失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print("获取POI坐标失败: 未获取到POI坐标")
        return False

    poi_location = poi_detail.location
    print(f"POI坐标: {poi_location}")

    # 步骤2: 绕行增加时间≤25分钟
    print(f"\n步骤2: 验证绕路时间增量不超过{max_detour_time}秒（{max_detour_time//60}分钟）")

    # 计算直接到公交站的时间 t_AB
    walking_direct = maps_walking_by_coordinates(
        origin=user_location,
        destination=bus_station_location
    )

    if walking_direct.error:
        print(f"步骤2失败: 计算直接路线时间失败 - {walking_direct.error}")
        all_passed = False
    else:
        if walking_direct.total_duration_seconds is None:
            print("步骤2失败: 未获取到直接路线时间")
            all_passed = False
        else:
            t_AB = walking_direct.total_duration_seconds

            # 计算到POI的时间 t_AP
            walking_to_poi = maps_walking_by_coordinates(
                origin=user_location,
                destination=poi_location
            )

            # 计算POI到公交站的时间 t_PB
            walking_poi_to_bus = maps_walking_by_coordinates(
                origin=poi_location,
                destination=bus_station_location
            )

            if (walking_to_poi.error or walking_to_poi.total_duration_seconds is None or
                walking_poi_to_bus.error or walking_poi_to_bus.total_duration_seconds is None):
                print("步骤2失败: 计算绕路路线时间失败")
                all_passed = False
            else:
                t_AP = walking_to_poi.total_duration_seconds
                t_PB = walking_poi_to_bus.total_duration_seconds
                extra = t_AP + t_PB - t_AB

                if extra > max_detour_time:
                    print(f"步骤2失败: 绕路时间增量{extra}秒超过要求{max_detour_time}秒（t_AB={t_AB}秒, t_AP={t_AP}秒, t_PB={t_PB}秒）")
                    all_passed = False
                else:
                    print(f"步骤2通过: 绕路时间增量{extra}秒，满足要求（<={max_detour_time}秒）（t_AB={t_AB}秒, t_AP={t_AP}秒, t_PB={t_PB}秒）")

    # 步骤3和4需要公交站信息，先搜索POI附近的公交站
    print(f"\n搜索POI附近{bus_search_radius}米的{bus_keywords}")
    bus_around_result = maps_around_search(
        location=poi_location,
        radius=bus_search_radius,
        keywords=bus_keywords
    )

    if bus_around_result.error:
        print(f"公交站搜索失败: {bus_around_result.error}")
        print("步骤3失败: 无法获取公交站信息")
        print("步骤4失败: 无法获取公交站信息")
        all_passed = False
        bus_pois = []
    else:
        bus_pois = bus_around_result.pois if bus_around_result.pois else []
        bus_count = len(bus_pois)
        print(f"找到{bus_count}个{bus_keywords}")

    # 步骤3: 酒吧附近1500米内存在公交站，且最近公交站步行≤15分钟
    print(f"\n步骤3: 验证最近公交站步行时间不超过{max_walking_time_to_bus}秒（{max_walking_time_to_bus//60}分钟）")
    if not bus_pois:
        print("步骤3失败: 未找到任何公交站")
        all_passed = False
    else:
        # 计算到每个公交站的步行时间，找到最小值
        min_walking_time = float('inf')
        for bus_poi in bus_pois:
            bus_detail = maps_search_detail(id=bus_poi.id)
            if bus_detail.error or not bus_detail.location:
                continue

            bus_location = bus_detail.location
            walking_result = maps_walking_by_coordinates(
                origin=poi_location,
                destination=bus_location
            )

            if walking_result.error or walking_result.total_duration_seconds is None:
                continue

            walking_time = walking_result.total_duration_seconds
            if walking_time < min_walking_time:
                min_walking_time = walking_time

        if min_walking_time == float('inf'):
            print("步骤3失败: 无法计算到任何公交站的步行时间")
            all_passed = False
        elif min_walking_time > max_walking_time_to_bus:
            print(f"步骤3失败: 到最近公交站的步行时间{min_walking_time}秒超过要求{max_walking_time_to_bus}秒")
            all_passed = False
        else:
            print(f"步骤3通过: 到最近公交站的步行时间{min_walking_time}秒，满足要求（<={max_walking_time_to_bus}秒）")

    # 步骤4: 最近公交站直线距离≤500米
    print(f"\n步骤4: 验证到最近公交站的直线距离不超过{max_distance_to_bus}米")
    if not bus_pois:
        print("步骤4失败: 未找到任何公交站")
        all_passed = False
    else:
        # 计算到每个公交站的直线距离，找到最小值
        min_distance = float('inf')
        for bus_poi in bus_pois:
            bus_detail = maps_search_detail(id=bus_poi.id)
            if bus_detail.error or not bus_detail.location:
                continue

            bus_location = bus_detail.location
            distance_result = maps_distance(
                origins=poi_location,
                destination=bus_location
            )

            if distance_result.error or not distance_result.results or len(distance_result.results) == 0:
                continue

            distance = distance_result.results[0].distance_meters
            if distance < min_distance:
                min_distance = distance

        if min_distance == float('inf'):
            print("步骤4失败: 无法计算到任何公交站的距离")
            all_passed = False
        elif min_distance > max_distance_to_bus:
            print(f"步骤4失败: 到最近公交站的距离{min_distance}米超过要求{max_distance_to_bus}米")
            all_passed = False
        else:
            print(f"步骤4通过: 到最近公交站的距离{min_distance}米，满足要求（<={max_distance_to_bus}米）")

    # 输出最终结果
    print(f"\n最终验证结果: {'通过' if all_passed else '失败'}")
    return all_passed


def main():
    result = verify_poi()
    print(f"\n验证结果: {result}")


if __name__ == "__main__":
    main()
